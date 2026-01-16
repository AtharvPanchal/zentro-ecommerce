from datetime import datetime, timedelta
from sqlalchemy import func
from app.models import AdminActivityLog
from app.services.risk_trend_service import RiskTrendService
from app.services.confidence_score_service import ConfidenceScoreService
from app.services.governance_rule_service import GovernanceRuleService
from app.services.security_report_service import SecurityReportService


class SecurityHealthService:

    @staticmethod
    def analyze_last_24h(db):
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        prev_24h = last_24h - timedelta(hours=24)

        # ----------------------------
        # STEP-1 : RAW COUNTS (READ-ONLY)
        # ----------------------------
        last_count = db.session.query(func.count(AdminActivityLog.id)) \
            .filter(AdminActivityLog.created_at >= last_24h).scalar() or 0

        prev_count = db.session.query(func.count(AdminActivityLog.id)) \
            .filter(
                AdminActivityLog.created_at >= prev_24h,
                AdminActivityLog.created_at < last_24h
            ).scalar() or 0

        # ----------------------------
        # STEP-2 : RISK TREND VALIDATION
        # ----------------------------
        admin_activity_trend = RiskTrendService.classify_trend(
            prev_count,
            last_count
        )

        bulk_count = db.session.query(func.count(AdminActivityLog.id)) \
            .filter(
                AdminActivityLog.is_bulk.is_(True),
                AdminActivityLog.created_at >= last_24h
            ).scalar() or 0

        prev_bulk_count = max(0, bulk_count - 2)

        bulk_status = RiskTrendService.classify_trend(
            prev_bulk_count,
            bulk_count
        )

        system_events = db.session.query(func.count(AdminActivityLog.id)) \
            .filter(
                AdminActivityLog.actor_type == "SYSTEM",
                AdminActivityLog.created_at >= last_24h
            ).scalar() or 0

        prev_system_events = max(0, system_events - 1)

        automation_status = RiskTrendService.classify_trend(
            prev_system_events,
            system_events
        )

        # ----------------------------
        # STEP-3 : CONFIDENCE SCORING
        # ----------------------------
        admin_confidence = ConfidenceScoreService.get_confidence(
            admin_activity_trend
        )

        bulk_confidence = ConfidenceScoreService.get_confidence(
            bulk_status
        )

        automation_confidence = ConfidenceScoreService.get_confidence(
            automation_status
        )

        # ----------------------------
        # STEP-4 : GOVERNANCE RULE ENGINE
        # ----------------------------
        admin_governance = GovernanceRuleService.evaluate(
            admin_activity_trend,
            admin_confidence
        )

        bulk_governance = GovernanceRuleService.evaluate(
            bulk_status,
            bulk_confidence
        )

        automation_governance = GovernanceRuleService.evaluate(
            automation_status,
            automation_confidence
        )

        # ----------------------------
        # OVERALL HEALTH (READ-ONLY)
        # ----------------------------
        overall = "GREEN"
        if admin_activity_trend in ["REPEATED", "TRENDING"] or bulk_status == "REPEATED":
            overall = "YELLOW"

        # ----------------------------
        # STEP-5 : COMPLIANCE & REPORTING
        # (ALWAYS GENERATED)
        # ----------------------------
        compliance_report = SecurityReportService.build_report({
            "admin_activity": {
                "status": admin_activity_trend,
                "confidence": admin_confidence,
                "governance": admin_governance
            },
            "bulk_activity": {
                "status": bulk_status,
                "confidence": bulk_confidence,
                "governance": bulk_governance
            },
            "automation": {
                "status": automation_status,
                "confidence": automation_confidence,
                "governance": automation_governance
            },
            "overall_health": overall
        })

        # ----------------------------
        # FINAL RESPONSE
        # ----------------------------
        return {
            "admin_activity": {
                "count": last_count,
                "status": admin_activity_trend,
                "confidence": admin_confidence,
                "governance": admin_governance
            },
            "bulk_activity": {
                "count": bulk_count,
                "status": bulk_status,
                "confidence": bulk_confidence,
                "governance": bulk_governance
            },
            "automation": {
                "events": system_events,
                "status": automation_status,
                "confidence": automation_confidence,
                "governance": automation_governance
            },
            "overall_health": overall,
            "compliance_report": compliance_report
        }
