from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.database import get_db, User, Voice, AudioGeneration, PlanType
from app.schemas.schemas import (
    DashboardStats, UsageReport, UsageChartData,
    PlanInfo
)
from app.utils.auth import get_current_user
from app.utils.usage_v2 import UsageTracker

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics for current user"""
    
    # Count voices
    total_voices = db.query(Voice).filter(
        Voice.user_id == current_user.id,
        Voice.is_active == True
    ).count()
    
    # Count generations
    total_generations = db.query(AudioGeneration).filter(
        AudioGeneration.user_id == current_user.id
    ).count()
    
    # Get recent generations
    recent_generations = db.query(AudioGeneration).filter(
        AudioGeneration.user_id == current_user.id
    ).order_by(AudioGeneration.created_at.desc()).limit(5).all()
    
    # Get available credits
    available = UsageTracker.get_available_generations(current_user)
    
    # Calculate minutes-based stats (using seconds/60 for now)
    total_seconds = sum(gen.duration_seconds or 0 for gen in recent_generations)
    total_minutes_used = round(total_seconds / 60, 2)
    monthly_minutes_used = round(current_user.monthly_audios_used * 0.5, 2)  # Estimate
    plan_minutes_limit = int(available["subscription_limit"] * 0.5)  # Convert to int
    remaining_minutes = int(available["total_available"] * 0.5)  # Convert to int
    
    return {
        "total_voices": total_voices,
        "total_generations": total_generations,
        "total_audios_generated": current_user.total_audios_generated,
        "monthly_audios_used": current_user.monthly_audios_used,
        "subscription_limit": available["subscription_limit"],
        "purchased_credits": available["purchased_credits"],
        "remaining_credits": available["total_available"],
        "total_minutes_used": total_minutes_used,
        "monthly_minutes_used": monthly_minutes_used,
        "plan_minutes_limit": plan_minutes_limit,
        "remaining_minutes": remaining_minutes,
        "recent_generations": recent_generations
    }


@router.get("/usage-report", response_model=UsageReport)
async def get_usage_report(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get usage report for charting"""
    from datetime import datetime, timedelta
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get daily stats
    daily_stats = db.query(
        func.date(AudioGeneration.created_at).label('date'),
        func.sum(AudioGeneration.duration_seconds).label('total_seconds'),
        func.count(AudioGeneration.id).label('count')
    ).filter(
        AudioGeneration.user_id == current_user.id,
        AudioGeneration.created_at >= start_date
    ).group_by(
        func.date(AudioGeneration.created_at)
    ).order_by('date').all()
    
    chart_data = []
    total_minutes = 0
    total_generations = 0
    
    for stat in daily_stats:
        minutes = (stat.total_seconds or 0) / 60
        chart_data.append(UsageChartData(
            date=str(stat.date),
            minutes=round(minutes, 2),
            generations=stat.count
        ))
        total_minutes += minutes
        total_generations += stat.count
    
    return {
        "chart_data": chart_data,
        "total_minutes": round(total_minutes, 2),
        "total_generations": total_generations
    }


@router.get("/plans")
async def get_available_plans(
    current_user: User = Depends(get_current_user)
):
    """Get available subscription plans with audio-based pricing"""
    from app.config import get_settings
    settings = get_settings()
    
    plans = [
        PlanInfo(
            plan=PlanType.FREE,
            name="Free",
            price_monthly=0,
            minutes_limit=settings.free_plan_audios,  # Using minutes_limit field for audios
            features=[
                f"{settings.free_plan_audios} audio generations",
                "Basic quality audio",
                "Watermark on output",
                "Email support"
            ],
            is_current_plan=current_user.plan == PlanType.FREE
        ),
        PlanInfo(
            plan=PlanType.STARTER,
            name="Starter",
            price_monthly=settings.starter_plan_price,
            minutes_limit=settings.starter_plan_audios,
            features=[
                f"{settings.starter_plan_audios} audio/month",
                "High quality audio",
                "No watermark",
                "Priority support"
            ],
            is_current_plan=current_user.plan == PlanType.STARTER
        ),
        PlanInfo(
            plan=PlanType.PRO,
            name="Pro",
            price_monthly=settings.pro_plan_price,
            minutes_limit=settings.pro_plan_audios,
            features=[
                f"{settings.pro_plan_audios} audio/month",
                "Ultra quality audio",
                "API access",
                "24/7 support"
            ],
            is_current_plan=current_user.plan == PlanType.PRO
        ),
        PlanInfo(
            plan=PlanType.BUSINESS,
            name="Business",
            price_monthly=settings.business_plan_price,
            minutes_limit=settings.business_plan_audios,
            features=[
                f"{settings.business_plan_audios} audio/month",
                "Ultra quality audio",
                "Full API access",
                "Team collaboration",
                "Custom integrations"
            ],
            is_current_plan=current_user.plan == PlanType.BUSINESS
        )
    ]
    
    return {"plans": plans, "current_plan": current_user.plan}


@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recent activity feed"""
    
    # Get recent generations
    generations = db.query(AudioGeneration).filter(
        AudioGeneration.user_id == current_user.id
    ).order_by(AudioGeneration.created_at.desc()).limit(limit).all()
    
    activity = []
    for gen in generations:
        activity.append({
            "type": "generation",
            "title": f"Generated audio: {gen.script_text[:50]}...",
            "timestamp": gen.created_at,
            "details": {
                "generation_id": gen.id,
                "voice_id": gen.voice_id,
                "duration": gen.duration_seconds
            }
        })
    
    return {"activity": activity}
