# app/services/governance_rule_service.py
"""
STEP-4 : Governance Rule Engine

Purpose:
- Provide admin guidance based on trend + confidence
- Read-only decision support (no system action)
"""

class GovernanceRuleService:

    @staticmethod
    def evaluate(trend, confidence):
        """
        Returns governance advice for admin.
        """
        if trend == "TRENDING" and confidence >= 90:
            return "ACTION REQUIRED"

        if trend in ["REPEATED", "INCREASED"] and confidence >= 70:
            return "REVIEW"

        return "MONITOR"
