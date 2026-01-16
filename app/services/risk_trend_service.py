# app/services/risk_trend_service.py
"""
STEP-2 : Risk Trend Validation Service

Purpose:
- Prevent unrealistic percentage spikes
- Convert raw counts into industry-safe trend labels
- READ-ONLY (no DB modification)
"""

class RiskTrendService:

    @staticmethod
    def calculate_growth(previous_count, current_count):
        """
        Calculates growth percentage with industry-safe cap.
        Growth is capped between 0% and 100%.
        """
        if previous_count <= 0:
            return 0

        raw_growth = ((current_count - previous_count) / previous_count) * 100

        # Cap unrealistic spikes
        if raw_growth < 0:
            return 0
        if raw_growth > 100:
            return 100

        return int(raw_growth)

    @staticmethod
    def classify_trend(previous_count, current_count):
        """
        Converts raw numbers into professional trend labels.
        """
        if previous_count == current_count:
            return "STABLE"

        if current_count > previous_count:
            growth = RiskTrendService.calculate_growth(previous_count, current_count)

            if growth <= 30:
                return "INCREASED"
            elif growth <= 70:
                return "REPEATED"
            else:
                return "TRENDING"

        return "STABLE"
