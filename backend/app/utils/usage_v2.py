"""
Usage tracking and limits enforcement - Audio-based pricing model
"""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.config import get_settings
from app.database import User, PlanType

settings = get_settings()


class UsageTracker:
    """Track and enforce usage limits based on audio generations count"""
    
    # Plan limits - number of audio generations per month
    PLAN_LIMITS = {
        PlanType.FREE: settings.free_plan_audios,
        PlanType.STARTER: settings.starter_plan_audios,
        PlanType.PRO: settings.pro_plan_audios,
        PlanType.BUSINESS: settings.business_plan_audios
    }
    
    PLAN_PRICES = {
        PlanType.FREE: 0,
        PlanType.STARTER: settings.starter_plan_price,
        PlanType.PRO: settings.pro_plan_price,
        PlanType.BUSINESS: settings.business_plan_price
    }
    
    @staticmethod
    def get_plan_limit(plan: PlanType) -> int:
        """Get audio generation limit for plan"""
        return UsageTracker.PLAN_LIMITS.get(plan, settings.free_plan_audios)
    
    @staticmethod
    def get_plan_price(plan: PlanType) -> float:
        """Get plan price"""
        return UsageTracker.PLAN_PRICES.get(plan, 0)
    
    @staticmethod
    def get_available_generations(user: User) -> dict:
        """Get available audio generations for user"""
        plan_limit = UsageTracker.get_plan_limit(user.plan)
        subscription_remaining = max(0, plan_limit - user.monthly_audios_used)
        purchased_credits = user.purchased_credits
        
        return {
            "subscription_limit": plan_limit,
            "subscription_used": user.monthly_audios_used,
            "subscription_remaining": subscription_remaining,
            "purchased_credits": purchased_credits,
            "total_available": subscription_remaining + purchased_credits
        }
    
    @staticmethod
    def can_generate_audio(user: User) -> dict:
        """Check if user can generate audio"""
        available = UsageTracker.get_available_generations(user)
        
        return {
            "can_generate": available["total_available"] > 0,
            "has_subscription": available["subscription_remaining"] > 0,
            "has_credits": available["purchased_credits"] > 0,
            **available
        }
    
    @staticmethod
    def use_credit(db: Session, user: User) -> bool:
        """Use one credit for audio generation"""
        # First try subscription credits
        plan_limit = UsageTracker.get_plan_limit(user.plan)
        if user.monthly_audios_used < plan_limit:
            user.monthly_audios_used += 1
            user.total_audios_generated += 1
            db.commit()
            return True
        
        # Then try purchased credits
        if user.purchased_credits > 0:
            user.purchased_credits -= 1
            user.total_audios_generated += 1
            db.commit()
            return True
        
        return False
    
    @staticmethod
    def add_purchased_credits(db: Session, user: User, credits: int) -> bool:
        """Add purchased credits (pay-per-audio or bulk package)"""
        user.purchased_credits += credits
        db.commit()
        return True
    
    @staticmethod
    def reset_monthly_usage(db: Session) -> int:
        """Reset monthly usage for all users (call at month start via cron)"""
        from app.database import User
        
        users = db.query(User).all()
        count = 0
        for user in users:
            user.monthly_audios_used = 0
            # Update renewal date
            user.plan_renewal_date = datetime.utcnow() + timedelta(days=30)
            count += 1
        db.commit()
        return count
    
    @staticmethod
    def get_pricing_info() -> dict:
        """Get all pricing information for frontend display"""
        return {
            "plans": {
                "free": {
                    "name": "Free",
                    "price": 0,
                    "audios": settings.free_plan_audios,
                    "features": ["3 audio generations", "Basic quality", "Watermark", "Email support"]
                },
                "starter": {
                    "name": "Starter",
                    "price": settings.starter_plan_price,
                    "audios": settings.starter_plan_audios,
                    "features": ["50 audio/month", "High quality", "No watermark", "Priority support"]
                },
                "pro": {
                    "name": "Pro",
                    "price": settings.pro_plan_price,
                    "audios": settings.pro_plan_audios,
                    "features": ["200 audio/month", "Ultra quality", "API access", "24/7 support"]
                },
                "business": {
                    "name": "Business",
                    "price": settings.business_plan_price,
                    "audios": settings.business_plan_audios,
                    "features": ["500 audio/month", "Ultra quality", "Full API", "Team collaboration"]
                }
            },
            "pay_per_audio": {
                "price": settings.pay_per_audio_price,
                "description": "Buy individual credits"
            },
            "bulk_packages": {
                "package_50": {
                    "audios": 50,
                    "price": settings.bulk_package_50_price,
                    "savings": 30,
                    "description": "50 audios for $20 (save $30)"
                },
                "package_100": {
                    "audios": 100,
                    "price": settings.bulk_package_100_price,
                    "savings": 65,
                    "description": "100 audios for $35 (save $65)"
                },
                "package_200": {
                    "audios": 200,
                    "price": settings.bulk_package_200_price,
                    "savings": 140,
                    "description": "200 audios for $60 (save $140)"
                }
            }
        }


def can_user_generate(user: User) -> dict:
    """Convenience function to check if user can generate"""
    return UsageTracker.can_generate_audio(user)
