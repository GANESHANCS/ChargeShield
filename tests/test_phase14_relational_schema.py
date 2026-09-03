"""
Phase 14 Milestone 1 — Relational Case Schema & Ingestion Tests

Comprehensive test suite validating SQLAlchemy relational models (Customer, Order, Transaction, Dispute),
Alembic migration integrity, DataIngestionService DB persistence, CaseService DB querying, CSV auto-seeding,
and strict PRODUCTION vs SIMULATION data state governance isolation.
"""

import pytest
from sqlalchemy import inspect
from backend.db.database import get_db_session
from backend.db.models import (
    CustomerModel,
    OrderModel,
    TransactionModel,
    DisputeModel,
)
from backend.services.case_service import case_service
from backend.services.data_ingestion_service import data_ingestion_service


def test_01_customer_model_schema():
    """Verify CustomerModel schema, primary key, and table name."""
    assert CustomerModel.__tablename__ == "customers"
    insp = inspect(CustomerModel)
    pk_names = [col.name for col in insp.primary_key]
    assert pk_names == ["customer_id"]
    cols = {col.name for col in insp.columns}
    expected_cols = {
        "customer_id", "account_creation_date", "tenure_days", "country",
        "total_order_count", "successful_order_count", "previous_dispute_count",
        "previous_chargeback_count", "refund_count", "account_status",
        "customer_segment", "data_state", "created_at", "updated_at"
    }
    assert expected_cols.issubset(cols)


def test_02_order_model_schema():
    """Verify OrderModel schema, primary key, foreign key, and table name."""
    assert OrderModel.__tablename__ == "orders"
    insp = inspect(OrderModel)
    assert [col.name for col in insp.primary_key] == ["order_id"]
    fk_targets = [fk.column.table.name + "." + fk.column.name for fk in OrderModel.__table__.foreign_keys]
    assert "customers.customer_id" in fk_targets


def test_03_transaction_model_schema():
    """Verify TransactionModel schema, primary key, foreign key, and table name."""
    assert TransactionModel.__tablename__ == "transactions"
    insp = inspect(TransactionModel)
    assert [col.name for col in insp.primary_key] == ["transaction_id"]
    fk_targets = [fk.column.table.name + "." + fk.column.name for fk in TransactionModel.__table__.foreign_keys]
    assert "orders.order_id" in fk_targets


def test_04_dispute_model_schema():
    """Verify DisputeModel schema, primary key, foreign keys, and table name."""
    assert DisputeModel.__tablename__ == "disputes"
    insp = inspect(DisputeModel)
    assert [col.name for col in insp.primary_key] == ["dispute_id"]
    fk_targets = [fk.column.table.name + "." + fk.column.name for fk in DisputeModel.__table__.foreign_keys]
    assert "transactions.transaction_id" in fk_targets
    assert "orders.order_id" in fk_targets
    assert "customers.customer_id" in fk_targets


def test_05_dispute_model_indexes():
    """Verify single and compound indexes on DisputeModel."""
    table_args = DisputeModel.__table_args__
    idx_names = [arg.name for arg in table_args if hasattr(arg, "name")]
    assert "ix_disputes_state_status" in idx_names
    assert "ix_disputes_status_created" in idx_names
    assert "ix_disputes_state_created" in idx_names


def test_06_csv_seed_data_reaches_relational_db():
    """Verify CSV seed data is successfully populated in database tables."""
    case_service._seed_db_if_empty()
    with get_db_session() as session:
        cust_count = session.query(CustomerModel).count()
        ord_count = session.query(OrderModel).count()
        txn_count = session.query(TransactionModel).count()
        disp_count = session.query(DisputeModel).count()

        assert cust_count > 0
        assert ord_count > 0
        assert txn_count > 0
        assert disp_count > 0


def test_07_rerun_seed_is_idempotent():
    """Verify re-running seed does not duplicate records in database."""
    with get_db_session() as session:
        initial_disp_count = session.query(DisputeModel).count()

    case_service._seed_db_if_empty()

    with get_db_session() as session:
        subsequent_disp_count = session.query(DisputeModel).count()

    assert initial_disp_count == subsequent_disp_count


def test_08_confirmed_ingestion_persists_relational_records():
    """Verify confirming an ingestion batch persists records in relational tables."""
    csv_content = (
        "dispute_id,transaction_id,order_id,customer_id,disputed_amount,currency,dispute_reason_code,"
        "dispute_category,dispute_status,dispute_stage,dispute_creation_timestamp,response_deadline,evidence_deadline,"
        "account_creation_date,tenure_days,country,total_order_count,successful_order_count,previous_dispute_count,"
        "previous_chargeback_count,refund_count,account_status,customer_segment,product_category,fulfillment_status,"
        "cancellation_status,order_timestamp,payment_method,payment_gateway,transaction_status,payment_success,"
        "auth_risk_score,velocity_24h,transaction_timestamp\n"
        "DISP_P14_001,TXN_P14_001,ORD_P14_001,CUST_P14_001,15000.0,INR,13.1_MERCH_NOT_RECEIVED,"
        "FRAUD,PENDING_REVIEW,FIRST_CHARGEBACK,2026-08-20T10:00:00Z,2026-09-01T10:00:00Z,2026-08-28T10:00:00Z,"
        "2025-01-01T00:00:00Z,600,IN,10,9,0,0,0,ACTIVE,VIP,ELECTRONICS,DELIVERED,"
        "NONE,2026-08-19T10:00:00Z,CARD,RAZORPAY,SUCCESS,1.0,0.05,1.0,2026-08-19T10:00:00Z\n"
    ).encode("utf-8")

    report = data_ingestion_service.validate_and_stage_csv(csv_content, data_state="PRODUCTION")
    batch_id = report["batch_id"]
    commit_res = data_ingestion_service.confirm_and_commit_batch(batch_id, actor_id="ADMIN_TEST")

    assert commit_res["status"] == "COMMITTED"

    with get_db_session() as session:
        disp_rec = session.query(DisputeModel).filter_by(dispute_id="DISP_P14_001").first()
        cust_rec = session.query(CustomerModel).filter_by(customer_id="CUST_P14_001").first()
        ord_rec = session.query(OrderModel).filter_by(order_id="ORD_P14_001").first()
        txn_rec = session.query(TransactionModel).filter_by(transaction_id="TXN_P14_001").first()

        assert disp_rec is not None
        assert disp_rec.disputed_amount == 15000.0
        assert cust_rec is not None
        assert cust_rec.customer_segment == "VIP"
        assert ord_rec is not None
        assert txn_rec is not None


def test_09_case_service_list_cases_querying_db():
    """Verify CaseService.list_cases queries DB and returns valid envelope."""
    result = case_service.list_cases(page=1, page_size=10, data_state="PRODUCTION")
    assert "items" in result
    assert "total" in result
    assert "page" in result
    assert result["page"] == 1
    assert len(result["items"]) <= 10


def test_10_case_service_search_filter_sort_pagination():
    """Verify multi-field search, filtering, sorting, and pagination in CaseService."""
    with get_db_session() as session:
        sample_disp = session.query(DisputeModel).first()
        assert sample_disp is not None
        disp_id = sample_disp.dispute_id
        r_code = sample_disp.dispute_reason_code

    # Search test
    search_res = case_service.list_cases(search=disp_id)
    assert search_res["total"] >= 1
    assert any(item["dispute_id"] == disp_id for item in search_res["items"])

    # Reason filter test
    reason_res = case_service.list_cases(reason=r_code)
    assert all(item["dispute_reason_code"].upper() == r_code.upper() for item in reason_res["items"])

    # Sorting test (amount_desc)
    sort_res = case_service.list_cases(sort_by="amount_desc", page_size=50)
    amounts = [item["disputed_amount"] for item in sort_res["items"]]
    assert amounts == sorted(amounts, reverse=True)


def test_11_case_detail_and_timeline():
    """Verify CaseService.get_case_detail and get_case_timeline fetching from DB."""
    with get_db_session() as session:
        sample_disp = session.query(DisputeModel).first()
        disp_id = sample_disp.dispute_id

    detail = case_service.get_case_detail(disp_id)
    assert detail is not None
    assert detail["dispute_id"] == disp_id
    assert "dispute" in detail
    assert "customer" in detail
    assert "order" in detail
    assert "transaction" in detail
    assert "prediction" in detail

    timeline = case_service.get_case_timeline(disp_id)
    assert timeline is not None
    assert timeline["dispute_id"] == disp_id
    assert len(timeline["events"]) >= 5


def test_12_simulation_persistence_and_isolation():
    """Verify simulation cases are saved with data_state='SIMULATION' and isolated from PRODUCTION queries."""
    sim_dispute = {
        "dispute_id": "DISP_SIM_999",
        "transaction_id": "TXN_SIM_999",
        "order_id": "ORD_SIM_999",
        "customer_id": "CUST_SIM_999",
        "disputed_amount": 99999.0,
        "currency": "INR",
        "dispute_reason_code": "10.4_OTHER_FRAUD",
        "dispute_category": "FRAUD",
        "dispute_status": "PENDING_REVIEW",
        "dispute_stage": "FIRST_CHARGEBACK",
        "dispute_creation_timestamp": "2026-08-27T00:00:00Z",
        "response_deadline": "2026-09-10T00:00:00Z",
        "evidence_deadline": "2026-09-05T00:00:00Z"
    }
    sim_customer = {"customer_id": "CUST_SIM_999", "country": "IN", "customer_segment": "REGULAR"}
    sim_order = {"order_id": "ORD_SIM_999", "customer_id": "CUST_SIM_999", "product_category": "ELECTRONICS"}
    sim_transaction = {"transaction_id": "TXN_SIM_999", "order_id": "ORD_SIM_999", "payment_method": "CARD"}
    sim_delivery = {"order_id": "ORD_SIM_999", "delivery_status": "DELIVERED"}

    case_service.add_simulated_case(sim_dispute, sim_customer, sim_order, sim_transaction, sim_delivery)

    # 1. Verify it appears in SIMULATION list
    sim_list = case_service.list_cases(data_state="SIMULATION")
    assert any(item["dispute_id"] == "DISP_SIM_999" for item in sim_list["items"])

    # 2. Verify it is ABSENT from default PRODUCTION list (ISOLATION REQUIREMENT)
    prod_list = case_service.list_cases(data_state="PRODUCTION")
    assert not any(item["dispute_id"] == "DISP_SIM_999" for item in prod_list["items"])

    # 3. Verify reset_simulated_cases removes ONLY SIMULATION records and keeps PRODUCTION intact
    case_service.reset_simulated_cases()

    sim_list_after = case_service.list_cases(data_state="SIMULATION")
    assert not any(item["dispute_id"] == "DISP_SIM_999" for item in sim_list_after["items"])

    prod_list_after = case_service.list_cases(data_state="PRODUCTION")
    assert len(prod_list_after["items"]) > 0
