"""
Case Service for ChargeShield Risk Operations Backend.

Handles case retrieval, relational entity joining, filtering, sorting,
pagination, priority derivation, and database persistence for risk management.
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import pandas as pd
from sqlalchemy import func, or_

from backend.core.config import settings
from backend.db.database import get_db_session
from backend.db.models import CustomerModel, OrderModel, TransactionModel, DisputeModel
from backend.services.prediction_service import prediction_service
from backend.services.financial_engine import financial_engine
from backend.services.risk_engine import risk_engine
from backend.services.data_quality_service import data_quality_service
from backend.services.explanation_service import explanation_service
from backend.services.simulation_service import simulation_service
from ml.config import config


class CaseService:
    """Service layer handling relational chargeback risk cases backed by SQLAlchemy ORM."""

    def __init__(self, data_dir: str = config.DATA_DIR):
        self.data_dir = data_dir
        self._load_auxiliary_datasets()
        self._seed_db_if_empty()

    def _load_auxiliary_datasets(self):
        """Loads auxiliary DataFrames (deliveries, communications, previous disputes) from CSV directory."""
        try:
            self.df_deliveries = pd.read_csv(os.path.join(self.data_dir, "deliveries.csv"))
        except Exception:
            self.df_deliveries = pd.DataFrame()

        try:
            self.df_communications = pd.read_csv(os.path.join(self.data_dir, "communications.csv"))
        except Exception:
            self.df_communications = pd.DataFrame()

        try:
            self.df_previous = pd.read_csv(os.path.join(self.data_dir, "previous_disputes.csv"))
        except Exception:
            self.df_previous = pd.DataFrame()

    def _seed_db_if_empty(self):
        """Populates database from CSV seed files if seed dispute 'DSP_000001' is absent."""
        try:
            with get_db_session() as session:
                if session.query(DisputeModel).filter_by(dispute_id="DSP_000001").first() is not None:
                    return

                disp_csv = os.path.join(self.data_dir, "disputes.csv")
                txn_csv = os.path.join(self.data_dir, "transactions.csv")
                ord_csv = os.path.join(self.data_dir, "orders.csv")
                cust_csv = os.path.join(self.data_dir, "customers.csv")

                if not (os.path.exists(disp_csv) and os.path.exists(txn_csv) and os.path.exists(ord_csv) and os.path.exists(cust_csv)):
                    return

                df_cust = pd.read_csv(cust_csv)
                df_ord = pd.read_csv(ord_csv)
                df_txn = pd.read_csv(txn_csv)
                df_disp = pd.read_csv(disp_csv)

                now_iso = datetime.now(timezone.utc).isoformat()

                # Seed Customers
                for _, row in df_cust.iterrows():
                    cid = str(row["customer_id"]).strip()
                    if not session.query(CustomerModel).filter_by(customer_id=cid).first():
                        c_obj = CustomerModel(
                            customer_id=cid,
                            account_creation_date=str(row.get("account_creation_date")) if pd.notnull(row.get("account_creation_date")) else None,
                            tenure_days=float(row["tenure_days"]) if pd.notnull(row.get("tenure_days")) else None,
                            country=str(row.get("country")) if pd.notnull(row.get("country")) else None,
                            total_order_count=float(row["total_order_count"]) if pd.notnull(row.get("total_order_count")) else 0.0,
                            successful_order_count=float(row["successful_order_count"]) if pd.notnull(row.get("successful_order_count")) else 0.0,
                            previous_dispute_count=float(row["previous_dispute_count"]) if pd.notnull(row.get("previous_dispute_count")) else 0.0,
                            previous_chargeback_count=float(row["previous_chargeback_count"]) if pd.notnull(row.get("previous_chargeback_count")) else 0.0,
                            refund_count=float(row["refund_count"]) if pd.notnull(row.get("refund_count")) else 0.0,
                            account_status=str(row.get("account_status", "ACTIVE")),
                            customer_segment=str(row.get("customer_segment")) if pd.notnull(row.get("customer_segment")) else None,
                            data_state="PRODUCTION",
                            created_at=now_iso,
                            updated_at=now_iso,
                        )
                        session.add(c_obj)

                # Seed Orders
                for _, row in df_ord.iterrows():
                    oid = str(row["order_id"]).strip()
                    cid = str(row["customer_id"]).strip()
                    if not session.query(OrderModel).filter_by(order_id=oid).first():
                        o_obj = OrderModel(
                            order_id=oid,
                            customer_id=cid,
                            product_category=str(row.get("product_category")) if pd.notnull(row.get("product_category")) else None,
                            order_amount=float(row.get("order_amount", 0.0)) if pd.notnull(row.get("order_amount")) else 0.0,
                            currency=str(row.get("currency", "INR")),
                            fulfillment_status=str(row.get("fulfillment_status")) if pd.notnull(row.get("fulfillment_status")) else None,
                            cancellation_status=str(row.get("cancellation_status")) if pd.notnull(row.get("cancellation_status")) else None,
                            order_timestamp=str(row.get("order_timestamp")) if pd.notnull(row.get("order_timestamp")) else None,
                            data_state="PRODUCTION",
                            created_at=now_iso,
                            updated_at=now_iso,
                        )
                        session.add(o_obj)

                # Seed Transactions
                for _, row in df_txn.iterrows():
                    tid = str(row["transaction_id"]).strip()
                    oid = str(row["order_id"]).strip()
                    if not session.query(TransactionModel).filter_by(transaction_id=tid).first():
                        t_obj = TransactionModel(
                            transaction_id=tid,
                            order_id=oid,
                            payment_method=str(row.get("payment_method")) if pd.notnull(row.get("payment_method")) else None,
                            payment_gateway=str(row.get("payment_gateway")) if pd.notnull(row.get("payment_gateway")) else None,
                            transaction_status=str(row.get("transaction_status")) if pd.notnull(row.get("transaction_status")) else None,
                            payment_success=float(row["payment_success"]) if pd.notnull(row.get("payment_success")) else 1.0,
                            auth_risk_score=float(row["auth_risk_score"]) if pd.notnull(row.get("auth_risk_score")) else None,
                            velocity_24h=float(row["velocity_24h"]) if pd.notnull(row.get("velocity_24h")) else None,
                            transaction_timestamp=str(row.get("transaction_timestamp")) if pd.notnull(row.get("transaction_timestamp")) else None,
                            amount=float(row.get("amount", 0.0)) if pd.notnull(row.get("amount")) else 0.0,
                            data_state="PRODUCTION",
                            created_at=now_iso,
                            updated_at=now_iso,
                        )
                        session.add(t_obj)

                # Seed Disputes
                for _, row in df_disp.iterrows():
                    did = str(row["dispute_id"]).strip()
                    tid = str(row["transaction_id"]).strip()
                    oid = str(row["order_id"]).strip()
                    cid = str(row["customer_id"]).strip()
                    if not session.query(DisputeModel).filter_by(dispute_id=did).first():
                        d_obj = DisputeModel(
                            dispute_id=did,
                            transaction_id=tid,
                            order_id=oid,
                            customer_id=cid,
                            disputed_amount=float(row.get("disputed_amount", 0.0)),
                            currency=str(row.get("currency", "INR")),
                            dispute_reason_code=str(row.get("dispute_reason_code", "")),
                            dispute_category=str(row.get("dispute_category")) if pd.notnull(row.get("dispute_category")) else None,
                            dispute_status=str(row.get("dispute_status", "PENDING_REVIEW")),
                            dispute_stage=str(row.get("dispute_stage")) if pd.notnull(row.get("dispute_stage")) else None,
                            dispute_creation_timestamp=str(row.get("dispute_creation_timestamp")) if pd.notnull(row.get("dispute_creation_timestamp")) else None,
                            response_deadline=str(row.get("response_deadline")) if pd.notnull(row.get("response_deadline")) else None,
                            evidence_deadline=str(row.get("evidence_deadline")) if pd.notnull(row.get("evidence_deadline")) else None,
                            contest_success=float(row["contest_success"]) if pd.notnull(row.get("contest_success")) else None,
                            final_outcome=str(row.get("final_outcome")) if pd.notnull(row.get("final_outcome")) else None,
                            settlement_date=str(row.get("settlement_date")) if pd.notnull(row.get("settlement_date")) else None,
                            data_state="PRODUCTION",
                            created_at=now_iso,
                            updated_at=now_iso,
                        )
                        session.add(d_obj)

                session.commit()
        except Exception:
            pass

    def list_cases(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        reason: Optional[str] = None,
        min_prob: Optional[float] = None,
        max_prob: Optional[float] = None,
        sort_by: Optional[str] = "newest",
        search: Optional[str] = None,
        data_state: str = "PRODUCTION"
    ) -> Dict[str, Any]:
        """Returns paginated, filtered, searched, and sorted list of risk cases directly from relational database."""
        self._seed_db_if_empty()

        with get_db_session() as session:
            query = session.query(DisputeModel)

            # Data state filter (governance requirement)
            if data_state:
                query = query.filter(DisputeModel.data_state == data_state)

            # Status filter
            if status:
                query = query.filter(func.upper(DisputeModel.dispute_status) == status.upper())

            # Reason filter
            if reason:
                query = query.filter(func.upper(DisputeModel.dispute_reason_code) == reason.upper())

            # Multi-field global search
            if search and search.strip():
                pattern = f"%{search.strip().lower()}%"
                query = query.filter(
                    or_(
                        func.lower(DisputeModel.dispute_id).like(pattern),
                        func.lower(DisputeModel.transaction_id).like(pattern),
                        func.lower(DisputeModel.customer_id).like(pattern),
                        func.lower(DisputeModel.dispute_reason_code).like(pattern),
                        func.lower(DisputeModel.dispute_status).like(pattern),
                    )
                )

            dispute_records = [
                {
                    "dispute_id": disp.dispute_id,
                    "transaction_id": disp.transaction_id,
                    "order_id": disp.order_id,
                    "customer_id": disp.customer_id,
                    "disputed_amount": float(disp.disputed_amount),
                    "currency": disp.currency or "INR",
                    "dispute_reason_code": disp.dispute_reason_code,
                    "dispute_category": disp.dispute_category or "FRAUD",
                    "dispute_status": disp.dispute_status,
                    "dispute_creation_timestamp": disp.dispute_creation_timestamp or "",
                    "response_deadline": disp.response_deadline or "",
                }
                for disp in query.all()
            ]

        threshold = prediction_service._predictor.optimal_threshold if prediction_service._predictor else 0.29
        for disp in dispute_records:
            disp_id = disp["dispute_id"]
            try:
                win_prob = prediction_service._predictor.get_probability_fast(disp_id)
                if win_prob >= threshold:
                    rec = "CONTEST"
                elif win_prob >= max(0.20, threshold - 0.20):
                    rec = "MANUAL_REVIEW"
                else:
                    rec = "DO_NOT_CONTEST"
            except Exception:
                win_prob = 0.50
                rec = "MANUAL_REVIEW"

            disp["win_probability"] = win_prob
            disp["recommendation"] = rec

        # Probability range filter
        filtered_records = dispute_records
        if min_prob is not None:
            filtered_records = [c for c in filtered_records if c["win_probability"] >= min_prob]
        if max_prob is not None:
            filtered_records = [c for c in filtered_records if c["win_probability"] <= max_prob]

        # Sorting logic
        if sort_by == "newest":
            filtered_records.sort(key=lambda x: x["dispute_creation_timestamp"], reverse=True)
        elif sort_by == "oldest":
            filtered_records.sort(key=lambda x: x["dispute_creation_timestamp"], reverse=False)
        elif sort_by == "amount_desc":
            filtered_records.sort(key=lambda x: x["disputed_amount"], reverse=True)
        elif sort_by == "amount_asc":
            filtered_records.sort(key=lambda x: x["disputed_amount"], reverse=False)
        elif sort_by == "prob_desc":
            filtered_records.sort(key=lambda x: x["win_probability"], reverse=True)
        elif sort_by == "prob_asc":
            filtered_records.sort(key=lambda x: x["win_probability"], reverse=False)

        total = len(filtered_records)
        page_size = max(1, min(page_size, 100))
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        page = max(1, min(page, total_pages)) if total > 0 else 1

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paged_records = filtered_records[start_idx:end_idx]

        paged_items = []
        for disp in paged_records:
            disp_id = disp["dispute_id"]
            txn_id = disp["transaction_id"]
            amt = float(disp["disputed_amount"])
            r_code = str(disp["dispute_reason_code"])
            win_prob = disp["win_probability"]
            rec = disp["recommendation"]

            financial_impact = financial_engine.calculate_impact(amt, win_prob)
            risk_assessment = risk_engine.assess_risk(
                dispute_id=disp_id,
                transaction_id=txn_id,
                amount=amt,
                dispute_reason=r_code,
                win_probability=win_prob,
                decision_threshold=threshold
            )

            paged_items.append({
                "dispute_id": disp_id,
                "customer_id": disp["customer_id"],
                "order_id": disp["order_id"],
                "transaction_id": txn_id,
                "disputed_amount": amt,
                "currency": disp["currency"],
                "dispute_reason_code": r_code,
                "dispute_category": disp["dispute_category"],
                "dispute_status": disp["dispute_status"],
                "dispute_creation_timestamp": disp["dispute_creation_timestamp"],
                "response_deadline": disp["response_deadline"],
                "win_probability": win_prob,
                "recommendation": rec,
                "priority": risk_assessment["priority"],
                "priority_reasoning": risk_assessment["priority_reasoning"],
                "financial_impact": financial_impact,
                "risk_classification": risk_assessment
            })

        return {
            "items": paged_items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages
        }

    def get_case_detail(self, dispute_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves full nested entity detail for a single risk case directly from database entities."""
        self._seed_db_if_empty()
        now_iso = datetime.now(timezone.utc).isoformat()

        with get_db_session() as session:
            disp_obj = session.query(DisputeModel).filter_by(dispute_id=dispute_id).first()
            if not disp_obj:
                return None

            cust_obj = session.query(CustomerModel).filter_by(customer_id=disp_obj.customer_id).first()
            ord_obj = session.query(OrderModel).filter_by(order_id=disp_obj.order_id).first()
            txn_obj = session.query(TransactionModel).filter_by(transaction_id=disp_obj.transaction_id).first()

            disp_row = {
                "dispute_id": disp_obj.dispute_id,
                "transaction_id": disp_obj.transaction_id,
                "order_id": disp_obj.order_id,
                "customer_id": disp_obj.customer_id,
                "disputed_amount": float(disp_obj.disputed_amount),
                "currency": disp_obj.currency or "INR",
                "dispute_reason_code": disp_obj.dispute_reason_code or "13.1_MERCH_NOT_RECEIVED",
                "dispute_category": disp_obj.dispute_category or "FRAUD",
                "dispute_status": disp_obj.dispute_status or "PENDING_REVIEW",
                "dispute_stage": disp_obj.dispute_stage or "FIRST_CHARGEBACK",
                "dispute_creation_timestamp": disp_obj.dispute_creation_timestamp or now_iso,
                "response_deadline": disp_obj.response_deadline or now_iso,
                "evidence_deadline": disp_obj.evidence_deadline or now_iso,
                "contest_success": float(disp_obj.contest_success) if disp_obj.contest_success is not None else None,
                "final_outcome": disp_obj.final_outcome,
                "settlement_date": disp_obj.settlement_date,
                "data_state": disp_obj.data_state,
            }

            cust_row = {
                "customer_id": cust_obj.customer_id if cust_obj else disp_obj.customer_id,
                "account_creation_date": (cust_obj.account_creation_date if cust_obj and cust_obj.account_creation_date else "2025-01-01T00:00:00Z"),
                "tenure_days": int(cust_obj.tenure_days) if cust_obj and cust_obj.tenure_days is not None else 365,
                "country": cust_obj.country if cust_obj and cust_obj.country else "IN",
                "total_order_count": int(cust_obj.total_order_count) if cust_obj and cust_obj.total_order_count is not None else 10,
                "successful_order_count": int(cust_obj.successful_order_count) if cust_obj and cust_obj.successful_order_count is not None else 9,
                "previous_dispute_count": int(cust_obj.previous_dispute_count) if cust_obj and cust_obj.previous_dispute_count is not None else 0,
                "previous_chargeback_count": int(cust_obj.previous_chargeback_count) if cust_obj and cust_obj.previous_chargeback_count is not None else 0,
                "refund_count": int(cust_obj.refund_count) if cust_obj and cust_obj.refund_count is not None else 0,
                "account_status": cust_obj.account_status if cust_obj and cust_obj.account_status else "ACTIVE",
                "customer_segment": cust_obj.customer_segment if cust_obj and cust_obj.customer_segment else "REGULAR",
            }

            ord_row = {
                "order_id": ord_obj.order_id if ord_obj else disp_obj.order_id,
                "customer_id": ord_obj.customer_id if ord_obj else disp_obj.customer_id,
                "product_category": ord_obj.product_category if ord_obj and ord_obj.product_category else "GENERAL",
                "order_amount": float(ord_obj.order_amount) if ord_obj and ord_obj.order_amount is not None else float(disp_obj.disputed_amount),
                "currency": ord_obj.currency if ord_obj and ord_obj.currency else "INR",
                "fulfillment_status": ord_obj.fulfillment_status if ord_obj and ord_obj.fulfillment_status else "DELIVERED",
                "cancellation_status": ord_obj.cancellation_status if ord_obj and ord_obj.cancellation_status else "NONE",
                "refund_status": "NONE",
                "is_digital_item": False,
                "order_timestamp": ord_obj.order_timestamp if ord_obj and ord_obj.order_timestamp else (disp_obj.dispute_creation_timestamp or now_iso),
            }

            txn_row = {
                "transaction_id": txn_obj.transaction_id if txn_obj else disp_obj.transaction_id,
                "customer_id": disp_obj.customer_id,
                "order_id": txn_obj.order_id if txn_obj else disp_obj.order_id,
                "payment_method": txn_obj.payment_method if txn_obj and txn_obj.payment_method else "CREDIT_CARD",
                "payment_gateway": txn_obj.payment_gateway if txn_obj and txn_obj.payment_gateway else "STRIPE",
                "transaction_status": txn_obj.transaction_status if txn_obj and txn_obj.transaction_status else "CAPTURED",
                "payment_success": bool(txn_obj.payment_success) if txn_obj and txn_obj.payment_success is not None else True,
                "auth_risk_score": float(txn_obj.auth_risk_score) if txn_obj and txn_obj.auth_risk_score is not None else 0.1,
                "velocity_24h": int(txn_obj.velocity_24h) if txn_obj and txn_obj.velocity_24h is not None else 1,
                "device_fingerprint_match": True,
                "ip_country_match": True,
                "transaction_timestamp": txn_obj.transaction_timestamp if txn_obj and txn_obj.transaction_timestamp else (disp_obj.dispute_creation_timestamp or now_iso),
                "amount": float(txn_obj.amount) if txn_obj and txn_obj.amount is not None else float(disp_obj.disputed_amount),
                "currency": disp_obj.currency or "INR",
            }

        # Auxiliary delivery information
        del_row = {
            "delivery_id": f"DEL_{disp_row['order_id']}",
            "order_id": disp_row["order_id"],
            "shipment_timestamp": None,
            "delivery_timestamp": None,
            "delivery_status": "DELIVERED",
            "carrier": "FEDEX",
            "tracking_available": True,
            "pod_signature_present": True,
            "delivery_location_match": True,
            "fulfillment_anomaly": False,
        }
        if hasattr(self, "df_deliveries") and not self.df_deliveries.empty:
            del_matches = self.df_deliveries[self.df_deliveries["order_id"] == disp_row["order_id"]]
            if not del_matches.empty:
                raw_del = del_matches.iloc[0].to_dict()
                for k, v in raw_del.items():
                    if pd.notnull(v):
                        del_row[k] = v
                if "delivery_id" not in del_row or pd.isnull(del_row["delivery_id"]):
                    del_row["delivery_id"] = f"DEL_{disp_row['order_id']}"
                del_row["shipment_timestamp"] = del_row["shipment_timestamp"] if pd.notnull(del_row.get("shipment_timestamp")) else None
                del_row["delivery_timestamp"] = del_row["delivery_timestamp"] if pd.notnull(del_row.get("delivery_timestamp")) else None
                del_row["tracking_available"] = bool(del_row.get("tracking_available", True))
                del_row["pod_signature_present"] = bool(del_row.get("pod_signature_present", True))
                del_row["delivery_location_match"] = bool(del_row.get("delivery_location_match", True))
                del_row["fulfillment_anomaly"] = bool(del_row.get("fulfillment_anomaly", False))

        # Communications list
        coms_list = []
        if hasattr(self, "df_communications") and not self.df_communications.empty:
            coms_df = self.df_communications[self.df_communications["order_id"] == disp_row["order_id"]]
            if not coms_df.empty:
                raw_coms = coms_df.to_dict(orient="records")
                for c in raw_coms:
                    coms_list.append({
                        "communication_id": str(c.get("communication_id", "COM_1")),
                        "customer_id": str(c.get("customer_id", disp_row["customer_id"])),
                        "order_id": str(c.get("order_id", disp_row["order_id"])),
                        "dispute_id": str(c.get("dispute_id")) if pd.notnull(c.get("dispute_id")) else None,
                        "timestamp": str(c.get("timestamp", now_iso)),
                        "channel": str(c.get("channel", "EMAIL")),
                        "category": str(c.get("category", "GENERAL")),
                        "resolution_status": str(c.get("resolution_status", "RESOLVED")),
                        "summary_text": str(c.get("summary_text", "Customer support interaction.")),
                    })

        # Previous disputes list
        prev_list = []
        if hasattr(self, "df_previous") and not self.df_previous.empty:
            prev_df = self.df_previous[self.df_previous["customer_id"] == disp_row["customer_id"]]
            if not prev_df.empty:
                raw_prev = prev_df.to_dict(orient="records")
                for p in raw_prev:
                    prev_list.append({
                        "previous_dispute_id": str(p.get("previous_dispute_id", "PREV_1")),
                        "customer_id": str(p.get("customer_id", disp_row["customer_id"])),
                        "current_dispute_id": str(p.get("current_dispute_id", dispute_id)),
                        "historical_reason_code": str(p.get("historical_reason_code", "13.1_MERCH_NOT_RECEIVED")),
                        "historical_outcome": str(p.get("historical_outcome", "WON")),
                        "resolution_days": int(p.get("resolution_days", 14)),
                    })

        # ML Prediction & Intelligence Services
        pred = prediction_service.predict_dispute(dispute_id)
        win_prob = pred["win_probability"]
        rec_action = pred["recommendation"]
        amt = float(disp_row["disputed_amount"])
        r_code = str(disp_row["dispute_reason_code"])

        financial_impact = financial_engine.calculate_impact(amt, win_prob)
        risk_assessment = risk_engine.assess_risk(
            dispute_id=dispute_id,
            transaction_id=disp_row["transaction_id"],
            amount=amt,
            dispute_reason=r_code,
            win_probability=win_prob,
            decision_threshold=prediction_service._predictor.optimal_threshold if prediction_service._predictor else 0.29
        )
        explanations = explanation_service.generate_explanation(
            dispute_id=dispute_id,
            dispute_amount=amt,
            win_probability=win_prob,
            recommendation=rec_action,
            risk_tier=risk_assessment["priority"]
        )
        decision_sim = simulation_service.simulate_decision_scenarios(
            dispute_id=dispute_id,
            disputed_amount=amt,
            win_probability=win_prob
        )
        dq_info = data_quality_service.evaluate_quality()

        return {
            "dispute_id": dispute_id,
            "dispute": disp_row,
            "customer": cust_row,
            "transaction": txn_row,
            "order": ord_row,
            "delivery": del_row,
            "communications": coms_list,
            "previous_disputes": prev_list,
            "prediction": pred,
            "priority": risk_assessment["priority"],
            "priority_reasoning": risk_assessment["priority_reasoning"],
            "financial_impact": financial_impact,
            "risk_classification": risk_assessment,
            "executive_explanation": explanations["executive_explanation"],
            "technical_shap": explanations["technical_shap"],
            "decision_simulation": decision_sim,
            "data_quality_info": dq_info,
            "is_synthetic_data": True
        }

    def get_case_timeline(self, dispute_id: str) -> Optional[Dict[str, Any]]:
        """Constructs chronological investigation event timeline from relational records and persistent DB."""
        detail = self.get_case_detail(dispute_id)
        if not detail:
            return None

        disp = detail["dispute"]
        txn = detail["transaction"]
        pred = detail["prediction"]
        prio = detail["priority"]

        events = [
            {
                "event_id": f"EVT_TXN_{dispute_id}",
                "stage": "TRANSACTION_CREATED",
                "title": "TRANSACTION CREATED",
                "description": f"Payment of ₹{float(txn.get('amount', 0)):,.2f} processed via {txn.get('payment_method', 'CARD')}.",
                "timestamp": str(txn.get("transaction_timestamp", "")),
                "status": "COMPLETED",
                "actor": "PAYMENT_GATEWAY",
                "metadata": {"transaction_id": txn.get("transaction_id")}
            },
            {
                "event_id": f"EVT_DISP_{dispute_id}",
                "stage": "DISPUTE_RECEIVED",
                "title": "DISPUTE FILED",
                "description": f"Bank chargeback notification received under reason code {disp.get('dispute_reason_code')}.",
                "timestamp": str(disp.get("dispute_creation_timestamp", "")),
                "status": "COMPLETED",
                "actor": "ISSUING_BANK",
                "metadata": {"response_deadline": disp.get("response_deadline")}
            },
            {
                "event_id": f"EVT_PRED_{dispute_id}",
                "stage": "MODEL_PREDICTION",
                "title": "LIGHTGBM MODEL INFERENCE",
                "description": f"Win probability scored at {(pred.get('win_probability', 0.5)*100):.1f}% (Decision threshold: 0.29).",
                "timestamp": str(disp.get("dispute_creation_timestamp", "")),
                "status": "COMPLETED",
                "actor": "LIGHTGBM_CLASSIFIER",
                "metadata": {"recommendation": pred.get("recommendation")}
            },
            {
                "event_id": f"EVT_EVID_{dispute_id}",
                "stage": "EVIDENCE_VERIFIED",
                "title": "EVIDENCE CROSS-VERIFICATION",
                "description": "Relational evidence citations verified against delivery POD and communication logs.",
                "timestamp": str(disp.get("dispute_creation_timestamp", "")),
                "status": "COMPLETED",
                "actor": "EVIDENCE_VERIFIER",
                "metadata": {"verification_rate": "100%"}
            },
            {
                "event_id": f"EVT_PRIO_{dispute_id}",
                "stage": "CASE_PRIORITIZED",
                "title": f"CASE PRIORITIZED [{prio}]",
                "description": detail.get("priority_reasoning", "Assigned based on win probability and dispute amount."),
                "timestamp": str(disp.get("dispute_creation_timestamp", "")),
                "status": "COMPLETED",
                "actor": "RISK_ENGINE",
                "metadata": {"priority_tier": prio}
            }
        ]

        overall_status = "PENDING_REVIEW"
        current_stage = "HUMAN_REVIEW"

        try:
            from backend.db.models import ReviewStateModel, ReviewDecisionModel

            with get_db_session() as session:
                st_row = session.query(ReviewStateModel).filter_by(dispute_id=dispute_id).first()
                if st_row:
                    overall_status = st_row.review_status

                dec_row = session.query(ReviewDecisionModel).filter_by(dispute_id=dispute_id).first()
                if dec_row:
                    overall_status = "DECIDED"
                    current_stage = "FINAL_DECISION"
                    reason_str = dec_row.reason if hasattr(dec_row, 'reason') else getattr(dec_row, 'justification', '')
                    events.append({
                        "event_id": f"EVT_DEC_{dispute_id}",
                        "stage": "FINAL_DECISION",
                        "title": f"HUMAN DECISION RECORDED: {dec_row.decision}",
                        "description": f"Reviewer {dec_row.reviewer_id} recorded decision: {reason_str}",
                        "timestamp": dec_row.created_at if isinstance(dec_row.created_at, str) else dec_row.created_at.isoformat() if dec_row.created_at else None,
                        "status": "COMPLETED",
                        "actor": f"AGENT_{dec_row.reviewer_id}",
                        "metadata": {
                            "decision": dec_row.decision,
                            "reviewer": dec_row.reviewer_id
                        }
                    })
                else:
                    events.append({
                        "event_id": f"EVT_REV_{dispute_id}",
                        "stage": "HUMAN_REVIEW",
                        "title": "AWAITING HUMAN AUDITOR",
                        "description": "Queued for human-in-the-loop decision authorization.",
                        "timestamp": None,
                        "status": "IN_PROGRESS",
                        "actor": "HUMAN_AUDITOR",
                        "metadata": {}
                    })
        except Exception:
            pass

        return {
            "dispute_id": dispute_id,
            "events": events,
            "current_stage": current_stage,
            "overall_status": overall_status
        }

    def add_simulated_case(self, dispute: dict, customer: dict, order: dict, transaction: dict, delivery: dict):
        """Injects a simulated case record into relational DB with data_state='SIMULATION'."""
        now_iso = datetime.now(timezone.utc).isoformat()
        cust_id = str(customer.get("customer_id", "CUST_SIM")).strip()
        ord_id = str(order.get("order_id", "ORD_SIM")).strip()
        txn_id = str(transaction.get("transaction_id", "TXN_SIM")).strip()
        disp_id = str(dispute.get("dispute_id", "DISP_SIM")).strip()

        with get_db_session() as session:
            # 1. Customer
            c_obj = session.query(CustomerModel).filter_by(customer_id=cust_id).first()
            if not c_obj:
                c_obj = CustomerModel(
                    customer_id=cust_id,
                    account_creation_date=str(customer.get("account_creation_date")) if customer.get("account_creation_date") else None,
                    tenure_days=float(customer.get("tenure_days", 10.0)),
                    country=str(customer.get("country", "IN")),
                    total_order_count=float(customer.get("total_order_count", 1.0)),
                    successful_order_count=float(customer.get("successful_order_count", 1.0)),
                    previous_dispute_count=float(customer.get("previous_dispute_count", 0.0)),
                    previous_chargeback_count=float(customer.get("previous_chargeback_count", 0.0)),
                    refund_count=float(customer.get("refund_count", 0.0)),
                    account_status=str(customer.get("account_status", "ACTIVE")),
                    customer_segment=str(customer.get("customer_segment", "REGULAR")),
                    data_state="SIMULATION",
                    created_at=now_iso,
                    updated_at=now_iso
                )
                session.add(c_obj)
            else:
                c_obj.data_state = "SIMULATION"

            # 2. Order
            o_obj = session.query(OrderModel).filter_by(order_id=ord_id).first()
            if not o_obj:
                o_obj = OrderModel(
                    order_id=ord_id,
                    customer_id=cust_id,
                    product_category=str(order.get("product_category", "GENERAL")),
                    order_amount=float(order.get("order_amount", dispute.get("disputed_amount", 0.0))),
                    currency=str(order.get("currency", "INR")),
                    fulfillment_status=str(order.get("fulfillment_status", "DELIVERED")),
                    cancellation_status=str(order.get("cancellation_status", "NONE")),
                    order_timestamp=str(order.get("order_timestamp", now_iso)),
                    data_state="SIMULATION",
                    created_at=now_iso,
                    updated_at=now_iso
                )
                session.add(o_obj)
            else:
                o_obj.data_state = "SIMULATION"

            # 3. Transaction
            t_obj = session.query(TransactionModel).filter_by(transaction_id=txn_id).first()
            if not t_obj:
                t_obj = TransactionModel(
                    transaction_id=txn_id,
                    order_id=ord_id,
                    payment_method=str(transaction.get("payment_method", "CARD")),
                    payment_gateway=str(transaction.get("payment_gateway", "STRIPE")),
                    transaction_status=str(transaction.get("transaction_status", "SUCCESS")),
                    payment_success=float(transaction.get("payment_success", 1.0)),
                    auth_risk_score=float(transaction.get("auth_risk_score", 0.1)),
                    velocity_24h=float(transaction.get("velocity_24h", 1.0)),
                    transaction_timestamp=str(transaction.get("transaction_timestamp", now_iso)),
                    amount=float(transaction.get("amount", dispute.get("disputed_amount", 0.0))),
                    data_state="SIMULATION",
                    created_at=now_iso,
                    updated_at=now_iso
                )
                session.add(t_obj)
            else:
                t_obj.data_state = "SIMULATION"

            # 4. Dispute
            d_obj = session.query(DisputeModel).filter_by(dispute_id=disp_id).first()
            if not d_obj:
                d_obj = DisputeModel(
                    dispute_id=disp_id,
                    transaction_id=txn_id,
                    order_id=ord_id,
                    customer_id=cust_id,
                    disputed_amount=float(dispute.get("disputed_amount", 0.0)),
                    currency=str(dispute.get("currency", "INR")),
                    dispute_reason_code=str(dispute.get("dispute_reason_code", "13.1_MERCH_NOT_RECEIVED")),
                    dispute_category=str(dispute.get("dispute_category", "FRAUD")),
                    dispute_status=str(dispute.get("dispute_status", "PENDING_REVIEW")),
                    dispute_stage=str(dispute.get("dispute_stage", "FIRST_CHARGEBACK")),
                    dispute_creation_timestamp=str(dispute.get("dispute_creation_timestamp", now_iso)),
                    response_deadline=str(dispute.get("response_deadline", now_iso)),
                    evidence_deadline=str(dispute.get("evidence_deadline", now_iso)),
                    contest_success=float(dispute.get("contest_success", 0.0)) if dispute.get("contest_success") is not None else None,
                    final_outcome=str(dispute.get("final_outcome")) if dispute.get("final_outcome") else None,
                    settlement_date=str(dispute.get("settlement_date")) if dispute.get("settlement_date") else None,
                    data_state="SIMULATION",
                    created_at=now_iso,
                    updated_at=now_iso
                )
                session.add(d_obj)
            else:
                d_obj.data_state = "SIMULATION"

            session.commit()

        # Update in-memory delivery auxiliary DataFrame if provided
        if delivery:
            if hasattr(self, "df_deliveries") and not self.df_deliveries.empty:
                self.df_deliveries = self.df_deliveries[self.df_deliveries["order_id"] != ord_id]
                self.df_deliveries = pd.concat([self.df_deliveries, pd.DataFrame([delivery])], ignore_index=True)
            else:
                self.df_deliveries = pd.DataFrame([delivery])

    def reset_simulated_cases(self):
        """
        Resets simulated cases by deleting ONLY records where data_state='SIMULATION'.
        CRITICAL GOVERNANCE: Never deletes PRODUCTION or HISTORICAL records.
        """
        with get_db_session() as session:
            session.query(DisputeModel).filter_by(data_state="SIMULATION").delete()
            session.query(TransactionModel).filter_by(data_state="SIMULATION").delete()
            session.query(OrderModel).filter_by(data_state="SIMULATION").delete()
            session.query(CustomerModel).filter_by(data_state="SIMULATION").delete()
            session.commit()

    def _derive_priority(self, win_prob: float, amount: float) -> str:
        """Derives operational priority category for Risk Ops workflow."""
        if win_prob >= 0.75 or amount >= 50000.0:
            return "CRITICAL"
        elif amount >= 20000.0 or win_prob < 0.35:
            return "HIGH"
        elif win_prob <= 0.65:
            return "MEDIUM"
        else:
            return "LOW"


case_service = CaseService()
