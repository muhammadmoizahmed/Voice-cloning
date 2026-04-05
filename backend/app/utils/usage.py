"""
Usage tracking and limits enforcement
"""
from sqlalchemy.orm import Session
from app.config import get_settings
from app.database import User, PlanType

settings = get_settings()


class UsageTracker:
    """Track and enforce usage limits"""
    
    PLAN_LIMITS = {
        PlanType.FREE: settings.free_plan_minutes,
        PlanType.PRO: settings.pro_plan_minutes,
        PlanType.BUSINESS: settings.business_plan_minutes
    }
    
    @staticmethod
    def get_plan_limit(plan: PlanType) -> int:
        """Get minute limit for plan"""
        return UsageTracker.PLAN_LIMITS.get(plan, settings.free_plan_minutes)
    
    @staticmethod
    def check_minutes_available(user: User, requested_minutes: float = 0) -> dict:
        """Check if user has minutes available"""
        limit = UsageTracker.get_plan_limit(user.plan)
        used = user.monthly_minutes_used
        remaining = limit - used
        
        return {
            "has_minutes": remaining >= requested_minutes,
            "total_limit": limit,
            "used": used,
            "remaining": max(0, remaining),
            "requested": requested_minutes,
            "plan": user.plan.value
        }
    
    @staticmethod
    def add_usage(db: Session, user: User, minutes: float) -> bool:
        """Add usage to user's account"""
        user.total_minutes_used += minutes
        user.monthly_minutes_used += minutes
        db.commit()
        return True
    
    @staticmethod
    def reset_monthly_usage(db: Session) -> int:
        """Reset monthly usage for all users (call at month start)"""
        from app.database import User
        
        users = db.query(User).all()
        count = 0
        for user in users:
            user.monthly_minutes_used = 0.0
            count += 1
        db.commit()
        return count
    
    @staticmethod
    def estimate_audio_duration(script_text: str, language: str = "en") -> float:
        """Estimate audio duration from script text"""
        # Rough estimation: ~130 words per minute
        # Average word length varies by language
        
        words = len(script_text.split())
        
        # Language-specific speech rates
        speech_rates = {
            "en": 130,
            "hi": 120,
            "ur": 120,
            "ar": 110,
            "zh": 160,
            "es": 130,
            "fr": 130,
            "de": 120,
            "ja": 140,
        }
        
        rate = speech_rates.get(language, 130)
        minutes = words / rate
        
        return round(minutes, 2)


def can_generate_audio(user: User, script_text: str, language: str = "en") -> dict:
    """Check if user can generate audio for given script"""
    estimated_minutes = UsageTracker.estimate_audio_duration(script_text, language)
    return UsageTracker.check_minutes_available(user, estimated_minutes)
