from fastapi import APIRouter, Depends, HTTPException, Query, status, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.database import get_db, User, UserRole, PlanType, Voice, AudioGeneration, Plan
from app.schemas.schemas import (
    AdminStats, AdminUserList, AdminVoiceModeration,
    ModerationAction, UserResponse
)
from app.utils.auth import get_admin_user, authenticate_user, create_access_token

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


# Plan Management Schemas
class PlanCreateRequest(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    price_monthly: float
    price_yearly: Optional[float] = None
    audio_limit: int
    video_limit: Optional[int] = None
    voice_clone_limit: Optional[int] = None
    features: Optional[str] = None  # JSON array as string
    is_active: bool = True
    is_popular: bool = False


class PlanUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    price_monthly: Optional[float] = None
    price_yearly: Optional[float] = None
    audio_limit: Optional[int] = None
    video_limit: Optional[int] = None
    voice_clone_limit: Optional[int] = None
    features: Optional[str] = None
    is_active: Optional[bool] = None
    is_popular: Optional[bool] = None


class AdminLoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
async def admin_login(
    data: AdminLoginRequest,
    db: Session = Depends(get_db)
):
    """Admin login endpoint"""
    from app.database import UserRole
    
    # Try with provided value (could be email or username)
    user = authenticate_user(db, data.username, data.password)
    
    # If not found and no @ in username, try appending default domain
    if not user and "@" not in data.username:
        user = authenticate_user(db, f"{data.username}@voiceforge.ai", data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    if user.role not in [UserRole.ADMIN, UserRole.MODERATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Create token
    access_token = create_access_token(data={"sub": user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value
        }
    }


@router.get("/stats", response_model=AdminStats)
async def get_admin_stats(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get platform statistics for admin"""
    
    # User stats
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    recent_signups = db.query(User).filter(
        User.created_at >= datetime.utcnow() - timedelta(days=7)
    ).count()
    
    # Content stats
    total_voices = db.query(Voice).filter(Voice.is_active == True).count()
    total_generations = db.query(AudioGeneration).count()
    
    # Pending verifications
    pending_ownership = db.query(Voice).filter(
        Voice.ownership_verified == False
    ).count()
    
    # Revenue (placeholder - integrate with Stripe)
    total_revenue = 0.0
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "recent_signups": recent_signups,
        "total_voices": total_voices,
        "total_generations": total_generations,
        "total_revenue": total_revenue,
        "flagged_content": pending_ownership
    }


@router.get("/users", response_model=AdminUserList)
async def list_all_users(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    role: Optional[UserRole] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """List all users with filtering"""
    
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (User.email.ilike(search_filter)) | 
            (User.full_name.ilike(search_filter))
        )
    
    total = query.count()
    
    # Count by status
    active_count = db.query(User).filter(User.is_active == True).count()
    pending_verification = db.query(User).filter(User.is_verified == False).count()
    
    users = query.order_by(User.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    return {
        "users": users,
        "total": total,
        "active_count": active_count,
        "pending_verification": pending_verification
    }


@router.get("/users/{user_id}")
async def get_user_details(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get detailed user information"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's voices
    voices = db.query(Voice).filter(Voice.user_id == user_id).all()
    
    # Get user's generations count
    generations_count = db.query(AudioGeneration).filter(
        AudioGeneration.user_id == user_id
    ).count()
    
    return {
        "user": user,
        "voices": voices,
        "generations_count": generations_count
    }


@router.post("/users/{user_id}/action")
async def perform_user_action(
    user_id: int,
    action: ModerationAction,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Perform moderation action on user"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if action.action == "suspend":
        user.is_active = False
    elif action.action == "activate":
        user.is_active = True
    elif action.action == "verify":
        user.is_verified = True
    elif action.action == "delete":
        db.delete(user)
        db.commit()
        return {"message": f"User {user_id} deleted"}
    elif action.action == "make_admin":
        user.role = UserRole.ADMIN
    elif action.action == "remove_admin":
        user.role = UserRole.USER
    elif action.action == "make_moderator":
        user.role = UserRole.MODERATOR
    elif action.action == "remove_moderator":
        user.role = UserRole.USER
    else:
        raise HTTPException(status_code=400, detail="Unknown action")
    
    db.commit()
    
    return {
        "message": f"Action '{action.action}' performed on user {user_id}",
        "reason": action.reason
    }


@router.post("/create-sub-admin")
async def create_sub_admin(
    email: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new sub-admin or moderator user (Admin only)"""
    
    # Only ADMIN can create sub-admins, not MODERATOR
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only full administrators can create sub-admin users")
    
    # Convert role string to UserRole enum
    if role == "admin":
        user_role = UserRole.ADMIN
    elif role == "moderator":
        user_role = UserRole.MODERATOR
    else:
        raise HTTPException(status_code=400, detail="Role must be either 'moderator' or 'admin'")
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Import password hashing
    from app.utils.auth import get_password_hash
    
    # Create new user
    new_user = User(
        email=email,
        hashed_password=get_password_hash(password),
        full_name=full_name,
        role=user_role,
        plan=PlanType.FREE,
        is_active=True,
        is_verified=True,
        email_verified=True,
        consent_given=True,
        consent_date=datetime.utcnow()
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "message": f"{user_role.value.capitalize()} user created successfully",
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "role": new_user.role.value,
            "created_at": new_user.created_at
        }
    }


@router.get("/sub-admins")
async def list_sub_admins(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """List all sub-admin and moderator users"""
    
    # Only ADMIN can see all sub-admins
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only full administrators can view sub-admin list")
    
    sub_admins = db.query(User).filter(
        User.role.in_([UserRole.MODERATOR, UserRole.ADMIN])
    ).order_by(User.created_at.desc()).all()
    
    return {
        "sub_admins": [
            {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "is_active": user.is_active,
                "last_login": user.last_login,
                "created_at": user.created_at
            }
            for user in sub_admins
        ],
        "total": len(sub_admins)
    }


@router.get("/voices/pending-verification")
async def get_pending_voice_verifications(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get voices pending ownership verification"""
    
    voices = db.query(Voice).filter(
        Voice.ownership_verified == False,
        Voice.is_active == True
    ).order_by(Voice.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    total = db.query(Voice).filter(Voice.ownership_verified == False).count()
    
    return {
        "voices": voices,
        "total": total,
        "pending_ownership_verification": total
    }


@router.post("/voices/{voice_id}/verify")
async def verify_voice_ownership(
    voice_id: int,
    approved: bool,
    notes: Optional[str] = None,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Verify or reject voice ownership"""
    
    voice = db.query(Voice).filter(Voice.id == voice_id).first()
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    
    voice.ownership_verified = approved
    if notes:
        voice.ownership_notes = notes
    
    db.commit()
    
    return {
        "message": f"Voice {voice_id} ownership {'approved' if approved else 'rejected'}",
        "notes": notes
    }


@router.get("/audit-logs")
async def get_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=500),
    action: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get audit logs"""
    from app.database import AuditLog
    
    query = db.query(AuditLog).filter(
        AuditLog.created_at >= datetime.utcnow() - timedelta(days=days)
    )
    
    if action:
        query = query.filter(AuditLog.action == action)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    total = query.count()
    logs = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    return {
        "logs": logs,
        "total": total
    }


@router.post("/system/reset-monthly-usage")
async def reset_monthly_usage(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Reset monthly usage for all users (monthly cron job)"""
    from app.utils.usage import UsageTracker
    
    count = UsageTracker.reset_monthly_usage(db)
    
    return {
        "message": f"Monthly usage reset for {count} users",
        "reset_at": datetime.utcnow()
    }


@router.get("/analytics/revenue")
async def get_revenue_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get revenue analytics and profit/loss data"""
    from app.database import Payment
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all completed payments in date range
    payments = db.query(Payment).filter(
        Payment.created_at >= start_date,
        Payment.status == "completed"
    ).all()
    
    total_revenue = sum(p.amount for p in payments)
    total_transactions = len(payments)
    
    # Calculate by plan type
    plan_revenue = {}
    for payment in payments:
        plan = payment.plan_type or 'credits'
        plan_revenue[plan] = plan_revenue.get(plan, 0) + payment.amount
    
    # Daily breakdown
    daily_revenue = {}
    for payment in payments:
        day = payment.created_at.strftime('%Y-%m-%d')
        daily_revenue[day] = daily_revenue.get(day, 0) + payment.amount
    
    # Calculate costs (estimate based on ElevenLabs API usage)
    total_generations = db.query(AudioGeneration).filter(
        AudioGeneration.created_at >= start_date
    ).count()
    
    # Estimate cost: ~$0.10 per generation on average
    estimated_costs = total_generations * 0.10
    profit = total_revenue - estimated_costs
    
    return {
        "total_revenue": total_revenue,
        "total_transactions": total_transactions,
        "estimated_costs": estimated_costs,
        "profit": profit,
        "profit_margin": (profit / total_revenue * 100) if total_revenue > 0 else 0,
        "plan_breakdown": plan_revenue,
        "daily_revenue": daily_revenue,
        "period_days": days
    }


@router.get("/analytics/users")
async def get_user_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get detailed user activity analytics"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # New users
    new_users = db.query(User).filter(User.created_at >= start_date).count()
    
    # Active users (made at least one generation)
    active_users = db.query(AudioGeneration.user_id).filter(
        AudioGeneration.created_at >= start_date
    ).distinct().count()
    
    # User retention (users who signed up and were active)
    total_users = db.query(User).count()
    
    # Daily signups
    daily_signups = {}
    users = db.query(User).filter(User.created_at >= start_date).all()
    for user in users:
        day = user.created_at.strftime('%Y-%m-%d')
        daily_signups[day] = daily_signups.get(day, 0) + 1
    
    # Plan distribution
    plan_distribution = {}
    for plan in PlanType:
        count = db.query(User).filter(User.plan == plan).count()
        plan_distribution[plan.value] = count
    
    return {
        "total_users": total_users,
        "new_users_period": new_users,
        "active_users_period": active_users,
        "user_retention_rate": (active_users / new_users * 100) if new_users > 0 else 0,
        "daily_signups": daily_signups,
        "plan_distribution": plan_distribution,
        "period_days": days
    }


@router.get("/analytics/activity")
async def get_activity_analytics(
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get platform activity analytics"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Generations stats
    generations = db.query(AudioGeneration).filter(
        AudioGeneration.created_at >= start_date
    ).all()
    
    total_generations = len(generations)
    successful_generations = sum(1 for g in generations if g.status == 'completed')
    failed_generations = sum(1 for g in generations if g.status == 'failed')
    
    # Daily generation count
    daily_generations = {}
    for gen in generations:
        day = gen.created_at.strftime('%Y-%m-%d')
        daily_generations[day] = daily_generations.get(day, 0) + 1
    
    # Top users by generation count
    top_users = db.query(
        User.id,
        User.full_name,
        User.email,
        func.count(AudioGeneration.id).label('gen_count')
    ).join(AudioGeneration, User.id == AudioGeneration.user_id).filter(
        AudioGeneration.created_at >= start_date
    ).group_by(User.id).order_by(func.count(AudioGeneration.id).desc()).limit(10).all()
    
    return {
        "total_generations": total_generations,
        "successful_generations": successful_generations,
        "failed_generations": failed_generations,
        "success_rate": (successful_generations / total_generations * 100) if total_generations > 0 else 0,
        "daily_generations": daily_generations,
        "top_users": [
            {"id": u.id, "name": u.full_name, "email": u.email, "generations": u.gen_count}
            for u in top_users
        ],
        "period_days": days
    }


@router.get("/users/{user_id}/activity")
async def get_user_detailed_activity(
    user_id: int,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get detailed activity for a specific user"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # User's generations
    generations = db.query(AudioGeneration).filter(
        AudioGeneration.user_id == user_id,
        AudioGeneration.created_at >= start_date
    ).all()
    
    # User's voices
    voices = db.query(Voice).filter(
        Voice.user_id == user_id,
        Voice.created_at >= start_date
    ).all()
    
    # User's payments
    from app.database import Payment
    payments = db.query(Payment).filter(
        Payment.user_id == user_id,
        Payment.created_at >= start_date
    ).all()
    
    total_spent = sum(p.amount for p in payments)
    
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "plan": user.plan.value,
            "created_at": user.created_at,
            "is_active": user.is_active
        },
        "activity_summary": {
            "generations_count": len(generations),
            "voices_uploaded": len(voices),
            "total_spent": total_spent,
            "payments_made": len(payments)
        },
        "generations": [
            {
                "id": g.id,
                "script_preview": g.script_text[:100] if g.script_text else None,
                "status": g.status,
                "created_at": g.created_at
            }
            for g in generations[-10:]  # Last 10
        ],
        "period_days": days
    }


@router.get("/system/stats")
async def get_system_stats(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive system statistics"""
    
    # Storage usage estimate
    voices = db.query(Voice).all()
    total_storage = sum(v.file_size for v in voices) / (1024 * 1024 * 1024)  # GB
    
    # Generation stats
    generations = db.query(AudioGeneration).all()
    total_generations = len(generations)
    completed_generations = sum(1 for g in generations if g.status == 'completed')
    
    # Average generation time (if stored)
    avg_duration = db.query(func.avg(AudioGeneration.duration_seconds)).scalar() or 0
    
    return {
        "storage": {
            "total_voices": len(voices),
            "estimated_storage_gb": round(total_storage, 2),
            "active_voices": sum(1 for v in voices if v.is_active)
        },
        "generations": {
            "total": total_generations,
            "completed": completed_generations,
            "success_rate": round(completed_generations / total_generations * 100, 2) if total_generations > 0 else 0,
            "average_duration_seconds": round(avg_duration, 2)
        },
        "users": {
            "total": db.query(User).count(),
            "active": db.query(User).filter(User.is_active == True).count(),
            "admins": db.query(User).filter(User.role == UserRole.ADMIN).count(),
            "verified": db.query(User).filter(User.is_verified == True).count()
        }
    }


@router.post("/change-password")
async def admin_change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Allow admin/moderator to change their own password"""
    from app.utils.auth import verify_password, get_password_hash
    
    # Verify current password
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Validate new password length
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters long")
    
    # Update password
    current_user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    return {"message": "Password changed successfully. Please login again with your new password."}


# ==========================================
# PLAN MANAGEMENT ENDPOINTS
# ==========================================

@router.get("/plans")
async def get_all_plans(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get all plans for admin panel"""
    plans = db.query(Plan).order_by(Plan.sort_order).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "display_name": p.display_name,
            "description": p.description,
            "price_monthly": p.price_monthly,
            "price_yearly": p.price_yearly,
            "audio_limit": p.audio_limit,
            "video_limit": p.video_limit,
            "voice_clone_limit": p.voice_clone_limit,
            "features": p.features,
            "is_active": p.is_active,
            "is_popular": p.is_popular,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
        }
        for p in plans
    ]


@router.post("/plans")
async def create_plan(
    data: PlanCreateRequest,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new plan"""
    # Check if plan name already exists
    existing = db.query(Plan).filter(Plan.name == data.name.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Plan with this name already exists")
    
    plan = Plan(
        name=data.name.upper(),
        display_name=data.display_name,
        description=data.description,
        price_monthly=data.price_monthly,
        price_yearly=data.price_yearly,
        audio_limit=data.audio_limit,
        video_limit=data.video_limit,
        voice_clone_limit=data.voice_clone_limit,
        features=data.features,
        is_active=data.is_active,
        is_popular=data.is_popular,
    )
    
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    return {"message": "Plan created successfully", "plan_id": plan.id}


@router.put("/plans/{plan_id}")
async def update_plan(
    plan_id: int,
    data: PlanUpdateRequest,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Update an existing plan"""
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Update fields if provided
    if data.display_name is not None:
        plan.display_name = data.display_name
    if data.description is not None:
        plan.description = data.description
    if data.price_monthly is not None:
        plan.price_monthly = data.price_monthly
    if data.price_yearly is not None:
        plan.price_yearly = data.price_yearly
    if data.audio_limit is not None:
        plan.audio_limit = data.audio_limit
    if data.video_limit is not None:
        plan.video_limit = data.video_limit
    if data.voice_clone_limit is not None:
        plan.voice_clone_limit = data.voice_clone_limit
    if data.features is not None:
        plan.features = data.features
    if data.is_active is not None:
        plan.is_active = data.is_active
    if data.is_popular is not None:
        plan.is_popular = data.is_popular
    
    db.commit()
    db.refresh(plan)
    
    return {"message": "Plan updated successfully", "plan_id": plan.id}


@router.delete("/plans/{plan_id}")
async def delete_plan(
    plan_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Delete a plan"""
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Check if any users are on this plan
    users_on_plan = db.query(User).filter(User.plan_id == plan_id).count()
    if users_on_plan > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete plan: {users_on_plan} users are currently on this plan"
        )
    
    db.delete(plan)
    db.commit()
    
    return {"message": "Plan deleted successfully"}
