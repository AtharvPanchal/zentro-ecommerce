def generate_recommendations(insights):
    """
    Adds actionable recommendations to AI audit insights
    """

    for insight in insights:
        text = insight.get("text", "").lower()
        level = insight.get("level")

        # HIGH SEVERITY / SECURITY
        if level == "danger" and "high severity" in text:
            insight["recommendation"] = (
                "Review recent high-severity admin actions and validate permissions."
            )

        # BULK ACTIONS
        elif "bulk" in text:
            insight["recommendation"] = (
                "Verify bulk operations and ensure proper approvals are documented."
            )

        # ADMIN BEHAVIOR
        elif "admin activity increased" in text or "unusual admin behavior" in text:
            insight["recommendation"] = (
                "Audit recent admin actions and consider access review."
            )

        # SYSTEM AUTOMATION
        elif "system automation" in text:
            insight["recommendation"] = (
                "No immediate action required. Continue monitoring automation health."
            )

        # ACTIVITY SPIKE / PREDICTIVE
        elif "spiked" in text or "trend continues" in text:
            insight["recommendation"] = (
                "Investigate recent activity spike and prepare operational capacity."
            )

        # DEFAULT
        else:
            insight["recommendation"] = (
                "Monitor this insight and review logs if the pattern continues."
            )

    return insights
