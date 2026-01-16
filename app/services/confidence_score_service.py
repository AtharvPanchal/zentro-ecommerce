# app/services/confidence_score_service.py
"""
STEP-3 : Confidence Scoring Service

Purpose:
- Assign AI-style confidence score to each trend
- Read-only intelligence layer
"""

class ConfidenceScoreService:

    TREND_CONFIDENCE_MAP = {
        "STABLE": 60,
        "INCREASED": 70,
        "REPEATED": 85,
        "TRENDING": 95
    }

    @staticmethod
    def get_confidence(trend_label):
        """
        Returns confidence score (0-100) based on trend label.
        """
        return ConfidenceScoreService.TREND_CONFIDENCE_MAP.get(trend_label, 50)
