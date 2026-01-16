# app/services/security_report_service.py
"""
STEP-5 : Security Compliance & Reporting Service

Purpose:
- Prepare clean, export-ready security health reports
- Separate active vs archived insights
- Read-only, compliance-safe
"""

from datetime import datetime


class SecurityReportService:

    @staticmethod
    def build_report(health_data):
        """
        Builds final compliance-ready report structure.
        """

        report_generated_at = datetime.utcnow().isoformat() + "Z"

        active_insights = []
        archived_insights = []

        def process_section(name, data):
            entry = {
                "section": name,
                "status": data.get("status"),
                "confidence": data.get("confidence"),
                "governance": data.get("governance")
            }

            if entry["governance"] in ["REVIEW", "ACTION REQUIRED"]:
                active_insights.append(entry)
            else:
                archived_insights.append(entry)

        process_section("Admin Activity", health_data["admin_activity"])
        process_section("Bulk Operations", health_data["bulk_activity"])
        process_section("Automation", health_data["automation"])

        return {
            "generated_at": report_generated_at,
            "summary": {
                "overall_health": health_data["overall_health"],
                "active_issues": len(active_insights),
                "archived_items": len(archived_insights)
            },
            "active_insights": active_insights,
            "archived_insights": archived_insights
        }
