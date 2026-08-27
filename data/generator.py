"""
ChargeShield Synthetic Data Generator Engine.

Generates a reproducible, relational synthetic merchant environment for chargeback defense.
Includes realistic latent win-probability logic, entity relationships, data noise,
and explicit leakage boundary enforcement.
"""

import os
import json
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd

from data.schemas import DATA_DICTIONARY, FieldCategory

class SyntheticDataGenerator:
    """
    Reproducible synthetic chargeback data generator.
    Uses configurable random seeds and dataset sizing parameters.
    """
    def __init__(self, seed: int = 42):
        self.seed = seed
        self._reseed(seed)
        
    def _reseed(self, seed: int):
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)
        self.rng = np.random.default_rng(seed)

    def generate_dataset(
        self,
        num_customers: int = 500,
        dispute_rate: float = 0.08,
        output_dir: str = "data/generated"
    ) -> Dict[str, pd.DataFrame]:
        """
        Generates full relational dataset.
        Returns dictionary of pandas DataFrames and writes CSVs + summary.json to output_dir.
        """
        self._reseed(self.seed)
        
        start_date = datetime(2025, 6, 1, 10, 0, 0)
        
        # 1. Generate Customers
        customers = self._generate_customers(num_customers, start_date)
        
        # 2. Generate Orders & Transactions (approx 2.5 orders per customer)
        orders, transactions = self._generate_orders_and_transactions(customers, start_date)
        
        # 3. Generate Deliveries
        deliveries = self._generate_deliveries(orders)
        
        # 4. Generate Disputes (Subsampled based on dispute_rate)
        disputes = self._generate_disputes(transactions, orders, customers, deliveries, dispute_rate)
        
        # 5. Generate Communications
        communications = self._generate_communications(customers, orders, disputes)
        
        # 6. Generate Historical Previous Disputes
        previous_disputes = self._generate_previous_disputes(customers, disputes)
        
        # Convert list of dicts to DataFrames
        df_customers = pd.DataFrame(customers)
        df_orders = pd.DataFrame(orders)
        df_transactions = pd.DataFrame(transactions)
        df_deliveries = pd.DataFrame(deliveries)
        df_disputes = pd.DataFrame(disputes)
        df_communications = pd.DataFrame(communications)
        df_previous_disputes = pd.DataFrame(previous_disputes)
        
        datasets = {
            "customers": df_customers,
            "orders": df_orders,
            "transactions": df_transactions,
            "deliveries": df_deliveries,
            "disputes": df_disputes,
            "communications": df_communications,
            "previous_disputes": df_previous_disputes
        }
        
        # Write to output directory if specified
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            for name, df in datasets.items():
                df.to_csv(os.path.join(output_dir, f"{name}.csv"), index=False)
                
            # Generate and write statistical summary
            summary = self.compute_summary(datasets)
            with open(os.path.join(output_dir, "summary.json"), "w") as f:
                json.dump(summary, f, indent=2)
                
        return datasets

    def _generate_customers(self, count: int, start_date: datetime) -> List[Dict[str, Any]]:
        customers = []
        countries = ["IN", "IN", "IN", "IN", "US", "AE", "SG", "GB"]
        statuses = ["ACTIVE", "ACTIVE", "ACTIVE", "DORMANT", "FLAGGED"]
        segments = ["VIP", "REGULAR", "REGULAR", "REGULAR", "NEW", "HIGH_RISK"]
        
        for i in range(1, count + 1):
            cust_id = f"CUST_{i:05d}"
            signup_delay_days = self.rng.integers(0, 180)
            account_creation = start_date + timedelta(days=int(signup_delay_days))
            tenure_days = max(1, (datetime(2026, 1, 1) - account_creation).days)
            
            # Segment influence
            segment = str(random.choice(segments))
            if segment == "HIGH_RISK":
                prev_disputes = int(self.rng.choice([1, 2, 3, 4], p=[0.4, 0.3, 0.2, 0.1]))
                prev_chargebacks = int(self.rng.choice([0, 1, 2], p=[0.5, 0.3, 0.2]))
                refund_count = int(self.rng.choice([1, 2, 3]))
            elif segment == "VIP":
                prev_disputes = 0
                prev_chargebacks = 0
                refund_count = int(self.rng.choice([0, 1]))
            else:
                prev_disputes = int(self.rng.choice([0, 1, 2], p=[0.8, 0.15, 0.05]))
                prev_chargebacks = int(self.rng.choice([0, 1], p=[0.9, 0.1]))
                refund_count = int(self.rng.choice([0, 1, 2], p=[0.7, 0.2, 0.1]))

            total_orders = int(self.rng.integers(1, 30))
            successful_orders = max(0, total_orders - prev_disputes - refund_count)

            customers.append({
                "customer_id": cust_id,
                "account_creation_date": account_creation.isoformat(),
                "tenure_days": tenure_days,
                "country": random.choice(countries),
                "total_order_count": total_orders,
                "successful_order_count": successful_orders,
                "previous_dispute_count": prev_disputes,
                "previous_chargeback_count": prev_chargebacks,
                "refund_count": refund_count,
                "account_status": random.choice(statuses),
                "customer_segment": segment
            })
        return customers

    def _generate_orders_and_transactions(
        self,
        customers: List[Dict[str, Any]],
        start_date: datetime
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        orders = []
        transactions = []
        
        categories = ["ELECTRONICS", "FASHION", "DIGITAL_GOODS", "HOME", "BEAUTY"]
        pay_methods = ["UPI", "CREDIT_CARD", "DEBIT_CARD", "NET_BANKING", "WALLET"]
        
        order_counter = 1
        txn_counter = 1
        
        for cust in customers:
            # Generate between 1 and 4 orders per customer
            num_orders = self.rng.integers(1, 5)
            cust_signup = datetime.fromisoformat(cust["account_creation_date"])
            
            for _ in range(num_orders):
                order_id = f"ORD_{order_counter:06d}"
                txn_id = f"TXN_{txn_counter:06d}"
                order_counter += 1
                txn_counter += 1
                
                # Order timestamp after signup
                days_after = self.rng.integers(0, 90)
                order_time = cust_signup + timedelta(days=int(days_after), hours=int(self.rng.integers(0, 23)))
                
                category = str(random.choice(categories))
                is_digital = (category == "DIGITAL_GOODS")
                
                # Monetary amount: Lognormal distribution in INR
                if is_digital:
                    amount = round(float(self.rng.lognormal(mean=6.5, sigma=0.6)), 2) # median ~₹660
                elif category == "ELECTRONICS":
                    amount = round(float(self.rng.lognormal(mean=8.5, sigma=0.8)), 2) # median ~₹4,900
                else:
                    amount = round(float(self.rng.lognormal(mean=7.5, sigma=0.7)), 2) # median ~₹1,800
                amount = max(199.0, min(amount, 150000.0))
                
                fulfillment_status = "CANCELLED" if random.random() < 0.04 else "FULFILLED"
                cancellation_status = "CUSTOMER_CANCELLED" if fulfillment_status == "CANCELLED" else "NONE"
                refund_status = "NONE"
                
                orders.append({
                    "order_id": order_id,
                    "customer_id": cust["customer_id"],
                    "order_timestamp": order_time.isoformat(),
                    "product_category": category,
                    "order_amount": amount,
                    "fulfillment_status": fulfillment_status,
                    "cancellation_status": cancellation_status,
                    "refund_status": refund_status,
                    "is_digital_item": is_digital
                })
                
                # Transaction
                txn_time = order_time + timedelta(minutes=int(self.rng.integers(1, 10)))
                pay_method = str(random.choice(pay_methods))
                
                # Payment success
                payment_success = (fulfillment_status != "CANCELLED")
                txn_status = "CAPTURED" if payment_success else "FAILED"
                
                auth_risk = round(float(self.rng.uniform(5.0, 95.0)), 1)
                velocity = int(self.rng.choice([1, 1, 1, 2, 3, 5], p=[0.7, 0.15, 0.08, 0.04, 0.02, 0.01]))
                device_match = (random.random() > 0.12)
                ip_match = (random.random() > 0.08)
                
                transactions.append({
                    "transaction_id": txn_id,
                    "customer_id": cust["customer_id"],
                    "order_id": order_id,
                    "transaction_timestamp": txn_time.isoformat(),
                    "amount": amount,
                    "currency": "INR",
                    "payment_method": pay_method,
                    "transaction_status": txn_status,
                    "payment_success": payment_success,
                    "auth_risk_score": auth_risk,
                    "velocity_24h": velocity,
                    "device_fingerprint_match": device_match,
                    "ip_country_match": ip_match
                })
                
        return orders, transactions

    def _generate_deliveries(self, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        deliveries = []
        carriers = ["BLUEDART", "DELHIVERY", "FEDEX", "EKART"]
        del_counter = 1
        
        for ord_item in orders:
            del_id = f"DEL_{del_counter:06d}"
            del_counter += 1
            
            if ord_item["is_digital_item"] or ord_item["fulfillment_status"] == "CANCELLED":
                deliveries.append({
                    "delivery_id": del_id,
                    "order_id": ord_item["order_id"],
                    "shipment_timestamp": None,
                    "delivery_timestamp": None,
                    "delivery_status": "NOT_APPLICABLE",
                    "carrier": "NONE",
                    "tracking_available": False,
                    "pod_signature_present": False,
                    "delivery_location_match": True,
                    "fulfillment_anomaly": False
                })
                continue
                
            ord_time = datetime.fromisoformat(ord_item["order_timestamp"])
            ship_time = ord_time + timedelta(hours=int(self.rng.integers(12, 48)))
            
            # Status distribution
            del_status = str(self.rng.choice(["DELIVERED", "DELIVERED", "DELIVERED", "IN_TRANSIT", "RETURNED", "FAILED"], p=[0.82, 0.05, 0.05, 0.04, 0.02, 0.02]))
            
            if del_status == "DELIVERED":
                delivery_time = ship_time + timedelta(days=int(self.rng.integers(1, 5)))
                del_time_str = delivery_time.isoformat()
                pod_present = (random.random() > 0.15) # 15% missing POD signature noise
                anomaly = (random.random() < 0.03)
            elif del_status == "IN_TRANSIT":
                del_time_str = None
                pod_present = False
                anomaly = False
            else:
                delivery_time = ship_time + timedelta(days=int(self.rng.integers(2, 6)))
                del_time_str = delivery_time.isoformat()
                pod_present = False
                anomaly = True

            deliveries.append({
                "delivery_id": del_id,
                "order_id": ord_item["order_id"],
                "shipment_timestamp": ship_time.isoformat(),
                "delivery_timestamp": del_time_str,
                "delivery_status": del_status,
                "carrier": random.choice(carriers),
                "tracking_available": True,
                "pod_signature_present": pod_present,
                "delivery_location_match": (random.random() > 0.05),
                "fulfillment_anomaly": anomaly
            })
            
        return deliveries

    def _generate_disputes(
        self,
        transactions: List[Dict[str, Any]],
        orders: List[Dict[str, Any]],
        customers: List[Dict[str, Any]],
        deliveries: List[Dict[str, Any]],
        dispute_rate: float
    ) -> List[Dict[str, Any]]:
        disputes = []
        
        # Index lookups
        order_map = {o["order_id"]: o for o in orders}
        customer_map = {c["customer_id"]: c for c in customers}
        delivery_map = {d["order_id"]: d for d in deliveries}
        
        # Captured transactions only
        captured_txns = [t for t in transactions if t["transaction_status"] == "CAPTURED"]
        num_disputes = max(10, int(len(captured_txns) * dispute_rate))
        
        # Sample transactions to be disputed
        disputed_txns = self.rng.choice(captured_txns, size=num_disputes, replace=False)
        
        reason_codes = [
            ("13.1_MERCH_NOT_RECEIVED", "NON_RECEIPT"),
            ("10.4_UNAUTHORIZED", "FRAUD"),
            ("13.3_NOT_AS_DESCRIBED", "QUALITY"),
            ("12.6_DUPLICATE", "PROCESSING"),
            ("13.6_CREDIT_NOT_PROCESSED", "CREDIT")
        ]
        
        disp_counter = 1
        
        for txn in disputed_txns:
            disp_id = f"DSP_{disp_counter:06d}"
            disp_counter += 1
            
            ord_item = order_map[txn["order_id"]]
            cust = customer_map[txn["customer_id"]]
            del_item = delivery_map[txn["order_id"]]
            
            txn_time = datetime.fromisoformat(txn["transaction_timestamp"])
            disp_time = txn_time + timedelta(days=int(self.rng.integers(3, 20)))
            
            # Select reason code based on product category & delivery status
            if del_item["delivery_status"] in ["IN_TRANSIT", "FAILED", "RETURNED"]:
                reason_code, category = "13.1_MERCH_NOT_RECEIVED", "NON_RECEIPT"
            elif ord_item["is_digital_item"]:
                reason_code, category = random.choice([
                    ("10.4_UNAUTHORIZED", "FRAUD"),
                    ("13.3_NOT_AS_DESCRIBED", "QUALITY")
                ])
            else:
                reason_code, category = random.choice(reason_codes)
                
            response_deadline = disp_time + timedelta(days=12)
            evidence_deadline = disp_time + timedelta(days=7)
            
            # =========================================================
            # LATENT WIN PROBABILITY CALCULATION (Non-Deterministic)
            # =========================================================
            # Base logit score
            logit = 0.0
            
            # 1. Delivery & Proof of Delivery Factors
            if del_item["delivery_status"] == "DELIVERED":
                if del_item["pod_signature_present"]:
                    logit += 2.5  # Strong evidence boost
                else:
                    logit += 1.0  # Basic delivery proof
            elif del_item["delivery_status"] in ["FAILED", "IN_TRANSIT", "RETURNED"] and reason_code == "13.1_MERCH_NOT_RECEIVED":
                logit -= 3.5  # Almost un-contestable if item never arrived
                
            # 2. Digital goods & Unauthorized transactions
            if reason_code == "10.4_UNAUTHORIZED":
                if txn["device_fingerprint_match"] and txn["ip_country_match"]:
                    logit += 2.0  # Clear device consistency proof
                else:
                    logit -= 1.8  # Genuine suspicion of fraud
                    
            # 3. Customer History
            if cust["previous_chargeback_count"] > 1:
                logit -= 2.0  # Serial disputer penalty
            elif cust["successful_order_count"] > 5 and cust["previous_dispute_count"] == 0:
                logit += 1.2  # Trusted customer history
                
            # 4. Fulfillment Anomalies & Risk Scores
            if del_item["fulfillment_anomaly"]:
                logit -= 1.5
            if txn["auth_risk_score"] > 80.0:
                logit -= 1.0
                
            # 5. Gaussian Noise (simulates unpredictable card issuer decisions)
            noise = float(self.rng.normal(loc=0.0, scale=0.85))
            final_logit = logit + noise
            
            # Sigmoid activation function
            win_prob = 1.0 / (1.0 + np.exp(-final_logit))
            
            # Binary target assignment (contest_success)
            contest_success = 1 if win_prob >= 0.5 else 0
            final_outcome = "WON" if contest_success == 1 else "LOST"
            
            settlement_date = (disp_time + timedelta(days=25)).isoformat() if final_outcome == "WON" else None
            
            disputes.append({
                "dispute_id": disp_id,
                "transaction_id": txn["transaction_id"],
                "order_id": txn["order_id"],
                "customer_id": txn["customer_id"],
                "dispute_creation_timestamp": disp_time.isoformat(),
                "dispute_reason_code": reason_code,
                "dispute_category": category,
                "disputed_amount": txn["amount"],
                "dispute_status": "CLOSED",
                "response_deadline": response_deadline.isoformat(),
                "evidence_deadline": evidence_deadline.isoformat(),
                "dispute_stage": "FIRST_DISPUTE",
                "contest_success": contest_success,      # TARGET VARIABLE
                "final_outcome": final_outcome,          # POST-OUTCOME FIELD
                "settlement_date": settlement_date       # POST-OUTCOME FIELD
            })
            
        return disputes

    def _generate_communications(
        self,
        customers: List[Dict[str, Any]],
        orders: List[Dict[str, Any]],
        disputes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        communications = []
        com_counter = 1
        
        channels = ["EMAIL", "CHAT", "PHONE", "TICKET"]
        categories = ["ORDER_INQUIRY", "REFUND_REQUEST", "DELIVERY_UPDATE", "COMPLAINT"]
        
        # Link 40% of disputes with merchant support communications
        dispute_map = {d["order_id"]: d for d in disputes}
        
        for ord_item in orders:
            if random.random() < 0.25:
                com_id = f"COM_{com_counter:06d}"
                com_counter += 1
                
                ord_time = datetime.fromisoformat(ord_item["order_timestamp"])
                com_time = ord_time + timedelta(hours=int(self.rng.integers(2, 72)))
                
                linked_disp = dispute_map.get(ord_item["order_id"])
                disp_id = linked_disp["dispute_id"] if linked_disp else None
                
                cat = str(random.choice(categories))
                status = "RESOLVED" if random.random() > 0.20 else "OPEN"
                
                summary = f"Customer initiated {cat.lower().replace('_', ' ')} regarding order {ord_item['order_id']}. Ticket status: {status}."
                
                communications.append({
                    "communication_id": com_id,
                    "customer_id": ord_item["customer_id"],
                    "order_id": ord_item["order_id"],
                    "dispute_id": disp_id,
                    "timestamp": com_time.isoformat(),
                    "channel": random.choice(channels),
                    "category": cat,
                    "resolution_status": status,
                    "summary_text": summary
                })
                
        return communications

    def _generate_previous_disputes(
        self,
        customers: List[Dict[str, Any]],
        disputes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        previous_disputes = []
        prev_counter = 1
        
        reason_codes = ["13.1_MERCH_NOT_RECEIVED", "10.4_UNAUTHORIZED", "13.3_NOT_AS_DESCRIBED"]
        
        for disp in disputes:
            cust_id = disp["customer_id"]
            # Look up customer
            matching_custs = [c for c in customers if c["customer_id"] == cust_id]
            if matching_custs and matching_custs[0]["previous_dispute_count"] > 0:
                num_prev = matching_custs[0]["previous_dispute_count"]
                for _ in range(num_prev):
                    prev_id = f"HIS_{prev_counter:06d}"
                    prev_counter += 1
                    
                    hist_outcome = str(random.choice(["WON", "LOST"]))
                    res_days = int(self.rng.integers(10, 45))
                    
                    previous_disputes.append({
                        "previous_dispute_id": prev_id,
                        "customer_id": cust_id,
                        "current_dispute_id": disp["dispute_id"],
                        "historical_reason_code": random.choice(reason_codes),
                        "historical_outcome": hist_outcome,
                        "resolution_days": res_days
                    })
                    
        return previous_disputes

    def compute_summary(self, datasets: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculates dataset statistics and validation metrics."""
        df_disp = datasets["disputes"]
        df_cust = datasets["customers"]
        df_txn = datasets["transactions"]
        df_ord = datasets["orders"]
        df_del = datasets["deliveries"]
        df_com = datasets["communications"]
        df_prev = datasets["previous_disputes"]
        
        target_counts = df_disp["contest_success"].value_counts().to_dict()
        target_dist = {str(k): int(v) for k, v in target_counts.items()}
        win_rate = float(df_disp["contest_success"].mean()) if len(df_disp) > 0 else 0.0
        
        reason_dist = df_disp["dispute_reason_code"].value_counts().to_dict()
        reason_dist_clean = {str(k): int(v) for k, v in reason_dist.items()}
        
        # Missing values breakdown
        missing_stats = {}
        for name, df in datasets.items():
            null_counts = df.isnull().sum().to_dict()
            missing_stats[name] = {k: int(v) for k, v in null_counts.items() if v > 0}
            
        return {
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "random_seed": self.seed,
                "is_synthetic": True,
                "disclaimer": "All dataset entities, transactions, and outcomes are synthetically generated."
            },
            "counts": {
                "customers": len(df_cust),
                "orders": len(df_ord),
                "transactions": len(df_txn),
                "deliveries": len(df_del),
                "disputes": len(df_disp),
                "communications": len(df_com),
                "previous_disputes": len(df_prev)
            },
            "contest_success_distribution": {
                "counts": target_dist,
                "win_rate_percentage": round(win_rate * 100, 2)
            },
            "dispute_reason_distribution": reason_dist_clean,
            "monetary_stats_inr": {
                "mean_dispute_amount": round(float(df_disp["disputed_amount"].mean()), 2),
                "median_dispute_amount": round(float(df_disp["disputed_amount"].median()), 2),
                "max_dispute_amount": round(float(df_disp["disputed_amount"].max()), 2),
                "total_disputed_value": round(float(df_disp["disputed_amount"].sum()), 2)
            },
            "missing_values_summary": missing_stats
        }

if __name__ == "__main__":
    generator = SyntheticDataGenerator(seed=42)
    generator.generate_dataset(num_customers=500, dispute_rate=0.08, output_dir="data/generated")
    print("Synthetic dataset successfully generated at data/generated/")
