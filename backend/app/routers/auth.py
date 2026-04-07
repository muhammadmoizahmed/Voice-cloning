from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db, User, UserRole, PlanType
from app.schemas.schemas import (
    UserCreate, UserResponse, Token, UserLogin, UserUpdate,
    ConsentForm
)
from app.utils.auth import (
    create_user, authenticate_user, create_access_token,
    update_last_login, get_current_user
)
from app.utils.email import email_service

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/signup")
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register new user - sends OTP for email verification"""
    from datetime import datetime, timedelta
    
    # Validate email is not empty
    if not user_data.email or not user_data.email.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required"
        )
    
    # Validate email format (basic check)
    email = user_data.email.strip().lower()
    if '@' not in email or '.' not in email.split('@')[-1]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please enter a valid email address"
        )
    
    # Validate full_name
    if not user_data.full_name or not user_data.full_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Full name is required"
        )
    
    # Validate password
    if not user_data.password or len(user_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    # Check if user exists and is already verified
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user and existing_user.is_otp_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email is already registered. Please login instead."
        )
    
    # Check consent
    if not user_data.consent_given:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must agree to the Terms of Service and Privacy Policy to continue"
        )
    
    # Generate OTP
    otp_code = email_service.generate_otp()
    otp_expires = datetime.utcnow() + timedelta(minutes=10)
    
    if existing_user:
        # Update existing unverified user
        user = existing_user
        user.full_name = user_data.full_name.strip()
        from app.utils.auth import get_password_hash
        user.hashed_password = get_password_hash(user_data.password)
        user.consent_given = user_data.consent_given
        user.consent_date = datetime.utcnow()
    else:
        # Create new user (unverified)
        from app.utils.auth import get_password_hash
        user = User(
            email=email,
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name.strip(),
            role=UserRole.USER,
            plan=PlanType.FREE,
            consent_given=user_data.consent_given,
            consent_date=datetime.utcnow(),
            is_active=True,
            is_verified=False,
            email_verified=False,
            is_otp_verified=False,
            total_audios_generated=0,
            monthly_audios_used=0,
            purchased_credits=0
        )
        db.add(user)
    
    # Save OTP
    user.otp_code = otp_code
    user.otp_expires_at = otp_expires
    db.commit()
    db.refresh(user)
    
    # Send OTP email
    email_sent = email_service.send_otp_email(user.email, otp_code, user.full_name)
    
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again."
        )
    
    return {
        "message": "Verification code sent to your email. Please verify to complete registration.",
        "user_id": user.id,
        "email": user.email,
        "requires_verification": True,
        "success": True
    }


@router.post("/verify-otp")
async def verify_otp(
    email: str = Form(...),
    otp_code: str = Form(...),
    db: Session = Depends(get_db)
):
    """Verify OTP code and complete registration"""
    from datetime import datetime
    
    print(f"DEBUG: Received verify-otp request - email: {email}, otp_code: {otp_code}")
    
    if not email or not email.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required"
        )
    
    if not otp_code or not otp_code.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP code is required"
        )
    
    email = email.strip().lower()
    otp_code = otp_code.strip()
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if already verified
    if user.is_otp_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified. Please login."
        )
    
    # Validate OTP
    if user.otp_code != otp_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    # Check OTP expiry
    if user.otp_expires_at and user.otp_expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired. Please request a new one."
        )
    
    # Mark user as verified
    user.is_otp_verified = True
    user.email_verified = True
    user.is_verified = True
    user.otp_code = None
    user.otp_expires_at = None
    db.commit()
    db.refresh(user)
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email})
    
    return {
        "message": "Email verified successfully! Registration complete.",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value
        }
    }


@router.post("/resend-otp")
async def resend_otp(email: str = Form(...), db: Session = Depends(get_db)):
    """Resend OTP code to user's email"""
    from datetime import datetime, timedelta
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_otp_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified. Please login."
        )
    
    # Generate new OTP
    otp_code = email_service.generate_otp()
    user.otp_code = otp_code
    user.otp_expires_at = datetime.utcnow() + timedelta(minutes=10)
    db.commit()
    
    # Send OTP email
    email_sent = email_service.send_otp_email(user.email, otp_code, user.full_name)
    
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )
    
    return {
        "message": "New verification code sent to your email.",
        "email": user.email
    }


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """User login - requires OTP verification for unverified emails"""
    from datetime import datetime, timedelta
    
    print(f"DEBUG LOGIN: username={form_data.username}, password={'*' * len(form_data.password) if form_data.password else 'empty'}")
    
    # Normalize email to lowercase
    email = form_data.username.strip().lower() if form_data.username else ""
    
    user = authenticate_user(db, email, form_data.password)
    if not user:
        # Check if user exists to debug
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"DEBUG: User found but password mismatch. Stored hash: {existing_user.hashed_password[:20]}...")
        else:
            print(f"DEBUG: User not found with email: {email}")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Check if email is OTP verified
    if not user.is_otp_verified:
        # Generate and send OTP for login verification
        otp_code = email_service.generate_otp()
        user.otp_code = otp_code
        user.otp_expires_at = datetime.utcnow() + timedelta(minutes=10)
        db.commit()
        
        # Send login OTP email
        email_service.send_login_otp(user.email, otp_code, user.full_name)
        
        return {
            "message": "Email not verified. Please check your email for OTP code.",
            "requires_otp": True,
            "email": user.email
        }
    
    # Update last login
    update_last_login(db, user)
    
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


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    if update_data.full_name:
        current_user.full_name = update_data.full_name
    
    if update_data.email:
        # Check if email is taken
        existing = db.query(User).filter(
            User.email == update_data.email,
            User.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = update_data.email
    
    if update_data.password:
        from app.utils.auth import get_password_hash
        current_user.hashed_password = get_password_hash(update_data.password)
    
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/consent")
async def submit_consent(
    consent: ConsentForm,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit consent form"""
    if not all([
        consent.consent_given,
        consent.voice_ownership_confirmed,
        consent.agree_to_terms,
        consent.agree_to_privacy
    ]):
        raise HTTPException(
            status_code=400,
            detail="All consent fields must be agreed to"
        )
    
    current_user.consent_given = True
    from datetime import datetime
    current_user.consent_date = datetime.utcnow()
    db.commit()
    
    return {"message": "Consent recorded successfully"}


@router.post("/logout")
async def logout():
    """Logout (client should discard token)"""
    return {"message": "Logged out successfully"}


@router.post("/forgot-password")
async def forgot_password(email: str = Form(...), db: Session = Depends(get_db)):
    """Request password reset - sends reset token to email"""
    from datetime import datetime, timedelta
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Don't reveal if email exists
        return {"message": "If this email exists, you will receive a password reset link."}
    
    # Generate reset token
    reset_token = email_service.generate_reset_token()
    user.reset_token = reset_token
    user.reset_token_expires_at = datetime.utcnow() + timedelta(hours=1)
    db.commit()
    
    # Send reset email
    email_sent = email_service.send_password_reset_email(user.email, reset_token, user.full_name)
    
    if not email_sent:
        raise HTTPException(status_code=500, detail="Failed to send reset email")
    
    return {"message": "If this email exists, you will receive a password reset link."}


@router.post("/reset-password")
async def reset_password(token: str = Form(...), new_password: str = Form(...), db: Session = Depends(get_db)):
    """Reset password using reset token"""
    from datetime import datetime
    from app.utils.auth import get_password_hash
    
    user = db.query(User).filter(User.reset_token == token).first()
    
    if not user or not user.reset_token_expires_at:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    # Check token expiry
    if user.reset_token_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Reset token has expired")
    
    # Update password
    user.hashed_password = get_password_hash(new_password)
    user.reset_token = None
    user.reset_token_expires_at = None
    db.commit()
    
    return {"message": "Password reset successful. Please login with your new password."}
