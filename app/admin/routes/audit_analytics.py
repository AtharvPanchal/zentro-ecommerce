from flask import render_template, session, request
from app.admin import admin_bp
from app.admin.decorators import admin_required
from app.models import AdminActivityLog
from sqlalchemy import func
from app.extensions import db
from datetime import datetime, timedelta, timezone
from app.utils.audit_recommendations_engine import generate_recommendations
from app.models import AuditInsight


# -------------------------------------------------
#   AI STYLE AUDIT INSIGHTS (RULE BASED)
# -------------------------------------------------
def generate_audit_insights(query, days=7):

    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)
    prev_start = start - timedelta(days=days)

    insights = []

    # -------------------------------
    # TOTAL COUNTS
    # -------------------------------
    total_actions = query.filter(AdminActivityLog.created_at >= start).count()

    high_count = query.filter(
        AdminActivityLog.severity == "HIGH",
        AdminActivityLog.created_at >= start
    ).count()

    admin_count = query.filter(
        AdminActivityLog.actor_type == "admin",
        AdminActivityLog.created_at >= start
    ).count()

    system_count = query.filter(
        AdminActivityLog.actor_type == "system",
        AdminActivityLog.created_at >= start
    ).count()

    # -------------------------------
    # SAFE PERCENTAGE CALCULATION
    # -------------------------------
    if total_actions > 0:
        high_pct = round((high_count / total_actions) * 100)
        admin_pct = round((admin_count / total_actions) * 100)
        system_pct = round((system_count / total_actions) * 100)
    else:
        high_pct = admin_pct = system_pct = 0

    # -------------------------------
    # GROWTH % HELPER
    # -------------------------------
    def growth_pct(current, previous):
        """
        Dashboard-safe growth percentage
        Always stays between 0–100
        """
        if previous <= 0:
            return 0

        ratio = current / previous

        # Convert to growth %
        growth = (ratio - 1) * 100

        # HARD CAP
        if growth < 0:
            return 0
        if growth > 100:
            return 100

        return round(growth)

    # -------------------------------
    # HIGH SEVERITY TREND (REACTIVE + PREDICTIVE)
    # -------------------------------
    previous_high = query.filter(
        AdminActivityLog.severity == "HIGH",
        AdminActivityLog.created_at >= prev_start,
        AdminActivityLog.created_at < start
    ).count()

    if previous_high > 0:
        change = growth_pct(high_count, previous_high)

        if change >= 30:
            insights.append({
                "level": "danger",
                "icon": "alert-triangle",
                "text": (
                    f"High severity actions increased by {change}% in last {days} days. "
                    "If this trend continues, security risk may increase."
                )
            })
        elif change <= -25:
            insights.append({
                "level": "success",
                "icon": "check-circle",
                "text": "High severity actions reduced compared to previous period"
            })

    # -------------------------------
    # BULK ACTION CHECK (GENERIC)
    # -------------------------------
    bulk_count = query.filter(
        AdminActivityLog.is_bulk == 1,
        AdminActivityLog.created_at >= start
    ).count()

    if bulk_count >= 3:
        insights.append({
            "level": "warning",
            "icon": "layers",
            "text": f"{bulk_count} bulk admin actions detected recently"
        })

    # -------------------------------
    # SYSTEM AUTOMATION HEALTH
    # -------------------------------
    previous_system = query.filter(
        AdminActivityLog.actor_type == "system",
        AdminActivityLog.created_at >= prev_start,
        AdminActivityLog.created_at < start
    ).count()

    system_growth = growth_pct(system_count, previous_system)

    if system_count == 0:
        insights.append({
            "level": "info",
            "icon": "info",
            "text": "No automated system activity detected in current period"
        })
    elif system_growth <= 5:
        insights.append({
            "level": "success",
            "icon": "cpu",
            "text": (
                f"System automation operating normally "
                f"({system_pct}% of total activity, {system_growth}% change)"
            )
        })
    else:
        insights.append({
            "level": "warning",
            "icon": "cpu",
            "text": (
                f"System automation activity changed by {system_growth}%. "
                "Monitor automation stability."
            )
        })

    # -------------------------------
    # ADMIN BEHAVIOR GROWTH
    # -------------------------------
    previous_admin = query.filter(
        AdminActivityLog.actor_type == "admin",
        AdminActivityLog.created_at >= prev_start,
        AdminActivityLog.created_at < start
    ).count()

    admin_growth = growth_pct(admin_count, previous_admin)

    if admin_growth >= 35:
        insights.append({
            "level": "warning",
            "icon": "shield",
            "text": (
                f"Admin activity increased by {admin_growth}%. "
                "Unusual admin behavior may require review."
            )
        })

    # -------------------------------
    # ACTIVITY SPIKE (PAST)
    # -------------------------------
    previous_total = query.filter(
        AdminActivityLog.created_at >= prev_start,
        AdminActivityLog.created_at < start
    ).count()

    if previous_total > 0:
        spike = growth_pct(total_actions, previous_total)
        if spike >= 40:
            insights.append({
                "level": "danger",
                "icon": "trending-up",
                "text": f"Audit activity spiked by {spike}% compared to previous period"
            })


    # -------------------------------
    # PERCENTAGE BASED EXPLANATIONS
    # -------------------------------
    if high_pct >= 15:
        insights.append({
            "level": "danger",
            "icon": "percent",
            "text": f"High severity actions form {high_pct}% of total audit activity"
        })

    if admin_pct >= 70:
        insights.append({
            "level": "warning",
            "icon": "user",
            "text": f"Admin actions account for {admin_pct}% of total activity"
        })

    # =================================================
    #  PRIORITY-3 STEP-3 : ENTITY-AWARE INSIGHTS
    # =================================================

    # -------------------------------
    # ADMIN-WISE HIGH SEVERITY DOMINANCE
    # -------------------------------
    actor_rows = (
        query.with_entities(
            AdminActivityLog.actor_type,
            func.count(AdminActivityLog.id)
        )
        .filter(
            AdminActivityLog.severity == "HIGH",
            AdminActivityLog.created_at >= start
        )
        .group_by(AdminActivityLog.actor_type)
        .all()
    )

    for actor_type, count in actor_rows:
        pct = round((count / high_count) * 100) if high_count else 0
        if pct >= 60:
            insights.append({
                "level": "danger",
                "icon": "users",
                "text": (
                    f"{actor_type.capitalize()} actions account for {pct}% of HIGH severity events "
                    f"({count} out of {high_count})"
                )
            })

    # -------------------------------
    # ACTION-WISE BULK DETECTION
    # -------------------------------
    action_rows = (
        query.with_entities(
            AdminActivityLog.action,
            func.count(AdminActivityLog.id)
        )
        .filter(AdminActivityLog.created_at >= start)
        .group_by(AdminActivityLog.action)
        .all()
    )

    for action, count in action_rows:
        if count >= 10:
            insights.append({
                "level": "warning",
                "icon": "repeat",
                "text": f"Bulk '{action}' actions detected ({count} times)"
            })



    return insights


# -------------------------------------------------
#   AUDIT ANALYTICS DASHBOARD
# -------------------------------------------------
@admin_bp.route("/audit-analytics")
@admin_required
def audit_analytics():

    is_super_admin = session.get("is_super_admin", False)
    query = AdminActivityLog.query

    if not is_super_admin:
        query = query.filter(
            AdminActivityLog.actor_type == "admin",
            AdminActivityLog.is_bulk == 0
        )

    metrics = {
        "total": query.count(),
        "active": query.filter(AdminActivityLog.is_archived == 0).count(),
        "archived": query.filter(AdminActivityLog.is_archived == 1).count(),
        "high": query.filter(AdminActivityLog.severity == "HIGH").count(),
        "system": query.filter(AdminActivityLog.actor_type == "system").count(),
        "last_24h": query.filter(
            AdminActivityLog.created_at >=
            datetime.now(timezone.utc) - timedelta(hours=24)
        ).count()
    }

    trend = (
        query.with_entities(
            func.date(AdminActivityLog.created_at).label("day"),
            func.count().label("count")
        )
        .group_by(func.date(AdminActivityLog.created_at))
        .order_by(func.date(AdminActivityLog.created_at))
        .limit(7)
        .all()
    )

    severity = (
        query.with_entities(
            AdminActivityLog.severity,
            func.count()
        )
        .group_by(AdminActivityLog.severity)
        .all()
    )

    actors = (
        query.with_entities(
            AdminActivityLog.actor_type,
            func.count()
        )
        .group_by(AdminActivityLog.actor_type)
        .all()
    )

    insights = generate_audit_insights(query, days=7)
    insights = generate_recommendations(insights)

    # =================================================
    # PRIORITY-3 STEP-5 : INSIGHT GOVERNANCE (STORE)
    # =================================================
    for i in insights:
        exists = AuditInsight.query.filter_by(
            message=i["text"]
        ).first()

        if not exists:
            db.session.add(
                AuditInsight(
                    insight_type=i.get("type", "OPERATIONAL"),
                    severity=i.get("level", "info").upper(),
                    message=i["text"],
                    recommendation=i.get("recommendation"),
                    confidence=i.get("confidence", 0.0)
                )
            )

    db.session.commit()

    # Fetch only ACTIVE insights (not archived)
    stored_insights = AuditInsight.query.filter_by(
        is_archived=False
    ).order_by(
        AuditInsight.generated_at.desc()
    ).all()

    return render_template(
        "admin/audit_analytics.html",
        metrics=metrics,
        trend=trend,
        severity=severity,
        actors=actors,
        insights=stored_insights  
    )


# -------------------------------------------------
#   ADMIN VS SYSTEM ACTIONS TREND (API)
# -------------------------------------------------
@admin_bp.route("/audit-analytics/actor-trend")
@admin_required
def audit_actor_trend():

    if not session.get("is_super_admin", False):
        return {"error": "Unauthorized"}, 403

    days = int(request.args.get("days", 7))
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=days)

    rows = (
        db.session.query(
            func.date(AdminActivityLog.created_at).label("day"),
            AdminActivityLog.actor_type,
            func.count(AdminActivityLog.id)
        )
        .filter(AdminActivityLog.created_at >= start_date)
        .group_by(
            func.date(AdminActivityLog.created_at),
            AdminActivityLog.actor_type
        )
        .order_by(func.date(AdminActivityLog.created_at))
        .all()
    )

    data = {}
    for day, actor, count in rows:
        day = str(day)
        data.setdefault(day, {"admin": 0, "system": 0})
        data[day][actor] = count

    return {
        "labels": list(data.keys()),
        "admin": [v["admin"] for v in data.values()],
        "system": [v["system"] for v in data.values()]
    }
