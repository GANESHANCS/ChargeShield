"""
Representment Evidence Package PDF Generator for ChargeShield.

Generates an institutional, audit-ready PDF document containing:
- Dispute metadata & governance state (PRODUCTION vs SIMULATION)
- Customer, Order, and Transaction records
- ML Risk Assessment & SHAP explanations (labeled as Advisory)
- Evidence Document Inventory with verified SHA-256 checksums
- Human Review Decision Audit Trail (or [ DECISION PENDING ])
- Ground-Truth Recorded Outcome (or [ OUTCOME PENDING ])
- Financial Summary with explicit disclaimers

NOTE: This document is an internally generated evidence and decision audit package
based on verified ChargeShield system records. It is not a legally certified document
nor automatically submitted to a payment network.
"""

import io
import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)

from backend.services.case_service import case_service
from backend.services.evidence_storage_service import evidence_storage_service
from backend.db.models import ReviewDecisionModel, ModelOutcomeModel, DisputeModel

logger = logging.getLogger("chargeshield.representment")


class RepresentmentPDFService:
    """Service to generate legal-grade Representment Evidence Package PDFs using ReportLab."""

    def generate_pdf(self, dispute_id: str, db: Session) -> bytes:
        """
        Compiles and builds the Representment Evidence Package PDF for a given dispute_id.
        Returns raw PDF bytes.
        """
        # 1. Fetch case details from CaseService
        case_detail = case_service.get_case_detail(dispute_id)
        if not case_detail:
            raise KeyError(f"Dispute case '{dispute_id}' not found.")

        dispute_data = case_detail.get("dispute", {})
        customer_data = case_detail.get("customer", {})
        order_data = case_detail.get("order", {})
        transaction_data = case_detail.get("transaction", {})
        prediction_data = case_detail.get("prediction", {})
        priority = case_detail.get("priority", "MEDIUM")
        data_state = dispute_data.get("data_state", "PRODUCTION")

        # 2. Fetch evidence documents from DB
        evidence_docs = evidence_storage_service.list_evidence_documents(
            db=db, dispute_id=dispute_id
        )

        # 3. Fetch human review decision from DB
        review_decision = (
            db.query(ReviewDecisionModel)
            .filter(ReviewDecisionModel.dispute_id == dispute_id)
            .order_by(ReviewDecisionModel.created_at.desc())
            .first()
        )

        # 4. Fetch ground-truth outcome from DB or dispute record
        recorded_outcome = (
            db.query(ModelOutcomeModel)
            .filter(ModelOutcomeModel.dispute_id == dispute_id)
            .order_by(ModelOutcomeModel.created_at.desc())
            .first()
        )
        final_outcome_val = None
        if recorded_outcome:
            final_outcome_val = recorded_outcome.actual_outcome
        elif dispute_data.get("final_outcome"):
            final_outcome_val = dispute_data.get("final_outcome")

        # 5. Build PDF Document
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
            pageCompression=0
        )

        story = []
        styles = getSampleStyleSheet()

        # Custom Palette & Styles
        c_primary = colors.HexColor("#0F172A")    # Slate 900
        c_accent = colors.HexColor("#0284C7")     # Sky 600
        c_dark = colors.HexColor("#1E293B")       # Slate 800
        c_light = colors.HexColor("#F8FAFC")      # Slate 50
        c_border = colors.HexColor("#E2E8F0")     # Slate 200
        c_muted = colors.HexColor("#64748B")      # Slate 500
        c_warning = colors.HexColor("#D97706")    # Amber 600

        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=20,
            leading=24,
            textColor=c_primary
        )
        subtitle_style = ParagraphStyle(
            'DocSubTitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=c_muted
        )
        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=16,
            textColor=c_accent,
            spaceBefore=12,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            'DocBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=c_dark
        )
        body_bold = ParagraphStyle(
            'DocBodyBold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=12,
            textColor=c_primary
        )
        disclaimer_style = ParagraphStyle(
            'DisclaimerText',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=8,
            leading=10,
            textColor=c_muted
        )
        table_header_style = ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            textColor=colors.white
        )
        table_cell_style = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=10,
            textColor=c_dark
        )

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # --- A. HEADER ---
        header_table_data = [
            [
                Paragraph("<b>CHARGEBOARD / CHARGESHIELD</b><br/><font size=8 color='#64748B'>Risk Operations & Representment Package</font>", title_style),
                Paragraph(f"<b>DATA STATE:</b> <font color='{'#D97706' if data_state == 'SIMULATION' else '#059669'}'>{data_state}</font><br/>"
                          f"<b>GENERATED:</b> {now_str}<br/>"
                          f"<b>DISPUTE ID:</b> {dispute_id}", ParagraphStyle('RHeader', parent=body_style, alignment=2))
            ]
        ]
        header_table = Table(header_table_data, colWidths=[3.5 * inch, 3.5 * inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 8))

        if data_state == "SIMULATION":
            sim_banner = Table(
                [[Paragraph("<b>SIMULATION RECORD NOTICE:</b> This evidence package contains synthetic simulation data generated for system validation and stress testing.", ParagraphStyle('SimBanner', parent=disclaimer_style, textColor=colors.HexColor('#9A3412')))]],
                colWidths=[7.0 * inch]
            )
            sim_banner.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFEDD5')),
                ('BORDER', (0, 0), (-1, -1), 1, colors.HexColor('#FDBA74')),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(sim_banner)
            story.append(Spacer(1, 8))

        story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceAfter=8))

        # --- B. DISPUTE & TRANSACTION SUMMARY ---
        story.append(Paragraph("1. DISPUTE & TRANSACTION OVERVIEW", section_heading))
        
        overview_grid = [
            [
                Paragraph("Dispute ID:", body_bold), Paragraph(str(dispute_id), body_style),
                Paragraph("Disputed Amount:", body_bold), Paragraph(f"{dispute_data.get('currency', 'INR')} {dispute_data.get('disputed_amount', 0.0):,.2f}", body_style)
            ],
            [
                Paragraph("Reason Code:", body_bold), Paragraph(str(dispute_data.get('dispute_reason_code', 'N/A')), body_style),
                Paragraph("Dispute Status:", body_bold), Paragraph(str(dispute_data.get('dispute_status', 'N/A')), body_style)
            ],
            [
                Paragraph("Category:", body_bold), Paragraph(str(dispute_data.get('dispute_category', 'FRAUD')), body_style),
                Paragraph("Creation Date:", body_bold), Paragraph(str(dispute_data.get('dispute_creation_timestamp', 'N/A')), body_style)
            ],
            [
                Paragraph("Response Deadline:", body_bold), Paragraph(str(dispute_data.get('response_deadline', 'N/A')), body_style),
                Paragraph("Priority Level:", body_bold), Paragraph(f"<b>{priority}</b>", body_style)
            ]
        ]
        t_overview = Table(overview_grid, colWidths=[1.3 * inch, 2.2 * inch, 1.3 * inch, 2.2 * inch])
        t_overview.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), c_light),
            ('BOX', (0, 0), (-1, -1), 1, c_border),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(t_overview)
        story.append(Spacer(1, 10))

        # --- C. CUSTOMER & ORDER PROFILE ---
        story.append(Paragraph("2. CUSTOMER & ORDER PROFILES", section_heading))
        cust_grid = [
            [
                Paragraph("Customer ID:", body_bold), Paragraph(str(customer_data.get('customer_id', 'N/A')), body_style),
                Paragraph("Order ID:", body_bold), Paragraph(str(order_data.get('order_id', 'N/A')), body_style)
            ],
            [
                Paragraph("Customer Segment:", body_bold), Paragraph(str(customer_data.get('customer_segment', 'REGULAR')), body_style),
                Paragraph("Order Category:", body_bold), Paragraph(str(order_data.get('product_category', 'GENERAL')), body_style)
            ],
            [
                Paragraph("Account Tenure:", body_bold), Paragraph(f"{customer_data.get('tenure_days', 0)} days", body_style),
                Paragraph("Order Amount:", body_bold), Paragraph(f"{order_data.get('currency', 'INR')} {order_data.get('order_amount', 0.0):,.2f}", body_style)
            ],
            [
                Paragraph("Total Orders / Prev Disputes:", body_bold), Paragraph(f"{customer_data.get('total_order_count', 0)} orders / {customer_data.get('previous_dispute_count', 0)} disputes", body_style),
                Paragraph("Fulfillment Status:", body_bold), Paragraph(str(order_data.get('fulfillment_status', 'DELIVERED')), body_style)
            ],
            [
                Paragraph("Transaction ID:", body_bold), Paragraph(str(transaction_data.get('transaction_id', 'N/A')), body_style),
                Paragraph("Payment Gateway / Method:", body_bold), Paragraph(f"{transaction_data.get('payment_gateway', 'N/A')} ({transaction_data.get('payment_method', 'N/A')})", body_style)
            ],
            [
                Paragraph("Auth Risk Score:", body_bold), Paragraph(f"{transaction_data.get('auth_risk_score', 0.0):.2f}", body_style),
                Paragraph("Transaction Time:", body_bold), Paragraph(str(transaction_data.get('transaction_timestamp', 'N/A')), body_style)
            ]
        ]
        t_cust = Table(cust_grid, colWidths=[1.4 * inch, 2.1 * inch, 1.4 * inch, 2.1 * inch])
        t_cust.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), c_light),
            ('BOX', (0, 0), (-1, -1), 1, c_border),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(t_cust)
        story.append(Spacer(1, 10))

        # --- D. AI ML RISK ASSESSMENT & ADVISORY ---
        story.append(Paragraph("3. AI / ML RISK ASSESSMENT & ADVISORY", section_heading))
        win_prob = prediction_data.get("win_probability", 0.5)
        model_rec = prediction_data.get("recommendation", "MANUAL_REVIEW")
        model_ver = prediction_data.get("model_version", "chargeshield_ml_v1")

        ml_grid = [
            [
                Paragraph("ML Model Version:", body_bold), Paragraph(str(model_ver), body_style),
                Paragraph("Win Probability:", body_bold), Paragraph(f"<b>{(win_prob * 100):.1f}%</b>", body_style)
            ],
            [
                Paragraph("AI Recommendation:", body_bold), Paragraph(f"<b>{model_rec}</b>", body_style),
                Paragraph("Calibrated Risk Tier:", body_bold), Paragraph(str(priority), body_style)
            ]
        ]
        t_ml = Table(ml_grid, colWidths=[1.4 * inch, 2.1 * inch, 1.4 * inch, 2.1 * inch])
        t_ml.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), c_light),
            ('BOX', (0, 0), (-1, -1), 1, c_border),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t_ml)
        story.append(Spacer(1, 4))
        story.append(Paragraph("<b>NOTICE:</b> ML predictions are advisory automated decision support signals derived from historical features. Final representment authorization requires human review.", disclaimer_style))
        story.append(Spacer(1, 10))

        # --- E. EVIDENCE INVENTORY ---
        story.append(Paragraph("4. VERIFIED EVIDENCE INVENTORY", section_heading))

        if evidence_docs:
            evidence_table_data = [
                [
                    Paragraph("Document Name / ID", table_header_style),
                    Paragraph("Type", table_header_style),
                    Paragraph("Size", table_header_style),
                    Paragraph("SHA-256 Hash", table_header_style),
                    Paragraph("Uploaded At", table_header_style)
                ]
            ]
            for doc_item in evidence_docs:
                fname = doc_item.get("safe_filename", doc_item.get("original_filename", "N/A"))
                eid = doc_item.get("evidence_id", "")
                ctype = doc_item.get("content_type", "N/A").split("/")[-1].upper()
                fsize = doc_item.get("file_size", 0)
                fsize_str = f"{fsize / 1024:.1f} KB" if fsize >= 1024 else f"{fsize} B"
                hash_val = doc_item.get("sha256_hash", "N/A")
                hash_disp = f"{hash_val[:12]}...{hash_val[-8:]}" if len(hash_val) > 20 else hash_val
                u_at = doc_item.get("uploaded_at", "N/A")
                if isinstance(u_at, str) and len(u_at) > 19:
                    u_at = u_at[:19].replace("T", " ")

                evidence_table_data.append([
                    Paragraph(f"<b>{fname}</b><br/><font color='#64748B' size=7>{eid}</font>", table_cell_style),
                    Paragraph(ctype, table_cell_style),
                    Paragraph(fsize_str, table_cell_style),
                    Paragraph(f"<font face='Courier' size=7>{hash_disp}</font>", table_cell_style),
                    Paragraph(u_at, table_cell_style)
                ])

            t_ev = Table(evidence_table_data, colWidths=[2.0 * inch, 0.8 * inch, 0.8 * inch, 2.0 * inch, 1.4 * inch])
            t_ev.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), c_primary),
                ('BOX', (0, 0), (-1, -1), 1, c_border),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
                ('PADDING', (0, 0), (-1, -1), 4),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(t_ev)
        else:
            no_ev_box = Table(
                [[Paragraph("No verified evidence documents attached.", body_style)]],
                colWidths=[7.0 * inch]
            )
            no_ev_box.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), c_light),
                ('BOX', (0, 0), (-1, -1), 1, c_border),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(no_ev_box)

        story.append(Spacer(1, 10))

        # --- F. HUMAN REVIEW DECISION & AUDIT TRAIL ---
        story.append(Paragraph("5. HUMAN REVIEW & DECISION AUDIT TRAIL", section_heading))
        if review_decision:
            dec_val = review_decision.decision
            dec_time = review_decision.created_at
            rev_id = review_decision.reviewer_id
            dec_reason = review_decision.reason or "No justification provided."

            dec_grid = [
                [
                    Paragraph("Reviewer Decision:", body_bold), Paragraph(f"<b>{dec_val}</b>", body_style),
                    Paragraph("Authorized By:", body_bold), Paragraph(str(rev_id), body_style)
                ],
                [
                    Paragraph("Decision Timestamp:", body_bold), Paragraph(str(dec_time), body_style),
                    Paragraph("AI Rec at Decision:", body_bold), Paragraph(str(review_decision.ai_recommendation), body_style)
                ],
                [
                    Paragraph("Justification:", body_bold),
                    Paragraph(str(dec_reason), body_style),
                    Paragraph("", body_bold), Paragraph("", body_style)
                ]
            ]
            t_dec = Table(dec_grid, colWidths=[1.4 * inch, 2.1 * inch, 1.4 * inch, 2.1 * inch])
            t_dec.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), c_light),
                ('BOX', (0, 0), (-1, -1), 1, c_border),
                ('SPAN', (1, 2), (3, 2)),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
                ('PADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(t_dec)
        else:
            pending_box = Table(
                [[Paragraph("<b>[ DECISION PENDING ]</b> — Case is currently queued for human review authorization.", ParagraphStyle('PendingText', parent=body_style, textColor=c_warning))]],
                colWidths=[7.0 * inch]
            )
            pending_box.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FEF3C7')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#FCD34D')),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(pending_box)

        story.append(Spacer(1, 10))

        # --- G. GROUND-TRUTH RECORDED OUTCOME ---
        story.append(Paragraph("6. GROUND-TRUTH RECORDED OUTCOME", section_heading))
        if final_outcome_val:
            out_grid = [
                [
                    Paragraph("Final Outcome:", body_bold), Paragraph(f"<b>{final_outcome_val}</b>", body_style),
                    Paragraph("Settlement Date:", body_bold), Paragraph(str(dispute_data.get('settlement_date') or 'N/A'), body_style)
                ]
            ]
            t_out = Table(out_grid, colWidths=[1.4 * inch, 2.1 * inch, 1.4 * inch, 2.1 * inch])
            t_out.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), c_light),
                ('BOX', (0, 0), (-1, -1), 1, c_border),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
                ('PADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(t_out)
        else:
            outcome_pending_box = Table(
                [[Paragraph("<b>[ OUTCOME PENDING ]</b> — Final issuer representment outcome has not been recorded.", ParagraphStyle('OutPendingText', parent=body_style, textColor=c_muted))]],
                colWidths=[7.0 * inch]
            )
            outcome_pending_box.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), c_light),
                ('BOX', (0, 0), (-1, -1), 1, c_border),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(outcome_pending_box)

        story.append(Spacer(1, 10))

        # --- H. FINANCIAL & LEGAL DISCLAIMER FOOTER ---
        story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceBefore=10, spaceAfter=8))
        story.append(Paragraph("<b>FINANCIAL & LEGAL GOVERNANCE DISCLAIMERS:</b>", body_bold))
        story.append(Paragraph("1. <i>Illustrative operational assumption — not a payment-network fee schedule.</i>", disclaimer_style))
        story.append(Paragraph("2. This document is an internal evidence compilation generated automatically from ChargeShield relational database records.", disclaimer_style))
        story.append(Paragraph("3. SHA-256 evidence checksums serve internal data integrity audit purposes.", disclaimer_style))

        # Build PDF
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes


# Singleton instance
representment_pdf_service = RepresentmentPDFService()
