"""
Payments and Credits Router
Handles pay-per-audio and bulk package purchases
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Literal

from app.database import get_db, User, Payment
from app.config import get_settings
from app.utils.auth import get_current_user
from app.utils.usage_v2 import UsageTracker

settings = get_settings()
router = APIRouter(prefix="/api/payments", tags=["Payments & Credits"])


@router.get("/pricing")
async def get_pricing_info():
    """Get all pricing information"""
    return UsageTracker.get_pricing_info()


@router.get("/credits")
async def get_user_credits(
    current_user: User = Depends(get_current_user)
):
    """Get user's available credits"""
    available = UsageTracker.get_available_generations(current_user)
    
    return {
        "plan": current_user.plan.value,
        "subscription": {
            "limit": available["subscription_limit"],
            "used": available["subscription_used"],
            "remaining": available["subscription_remaining"]
        },
        "purchased_credits": available["purchased_credits"],
        "total_available": available["total_available"]
    }


@router.post("/buy-credits")
async def buy_credits(
    package: Literal["single", "package_50", "package_100", "package_200"],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Buy credits (pay-per-audio or bulk packages)
    
    - single: 1 audio for $1
    - package_50: 50 audios for $20 (save $30)
    - package_100: 100 audios for $35 (save $65)
    - package_200: 200 audios for $60 (save $140)
    """
    
    # Define packages
    packages = {
        "single": {"credits": 1, "price": settings.pay_per_audio_price},
        "package_50": {"credits": 50, "price": settings.bulk_package_50_price},
        "package_100": {"credits": 100, "price": settings.bulk_package_100_price},
        "package_200": {"credits": 200, "price": settings.bulk_package_200_price}
    }
    
    if package not in packages:
        raise HTTPException(status_code=400, detail="Invalid package")
    
    pkg = packages[package]
    
    # In production, integrate with Stripe here
    # For now, simulate successful purchase
    
    # Add credits to user
    UsageTracker.add_purchased_credits(db, current_user, pkg["credits"])
    
    return {
        "message": f"Successfully purchased {pkg['credits']} credits",
        "credits_added": pkg["credits"],
        "price_paid": pkg["price"],
        "total_credits": current_user.purchased_credits
    }


@router.post("/subscribe")
async def subscribe_to_plan(
    plan: Literal["starter", "pro", "business"],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Subscribe to a plan
    
    - starter: $5/month - 50 audios
    - pro: $15/month - 200 audios
    - business: $30/month - 500 audios
    """
    from app.database import PlanType
    
    plan_map = {
        "starter": PlanType.STARTER,
        "pro": PlanType.PRO,
        "business": PlanType.BUSINESS
    }
    
    if plan not in plan_map:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    # In production, integrate with Stripe here
    # For now, simulate successful subscription
    
    # Update user plan
    current_user.plan = plan_map[plan]
    current_user.monthly_audios_used = 0  # Reset usage on plan change
    
    from datetime import datetime, timedelta
    current_user.plan_renewal_date = datetime.utcnow() + timedelta(days=30)
    
    db.commit()
    
    plan_limits = {
        "starter": settings.starter_plan_audios,
        "pro": settings.pro_plan_audios,
        "business": settings.business_plan_audios
    }
    
    return {
        "message": f"Successfully subscribed to {plan.capitalize()} plan",
        "plan": plan,
        "monthly_limit": plan_limits[plan],
        "renewal_date": current_user.plan_renewal_date
    }


@router.post("/downgrade-free")
async def downgrade_to_free(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Downgrade to free plan"""
    from app.database import PlanType
    
    current_user.plan = PlanType.FREE
    db.commit()
    
    return {
        "message": "Downgraded to Free plan",
        "plan": "free",
        "monthly_limit": settings.free_plan_audios
    }
