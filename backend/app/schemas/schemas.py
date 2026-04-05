from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    GUEST = "guest"
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


class PlanType(str, Enum):
    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"


# ============= User Schemas =============

class UserBase(BaseModel):
    email: str
    full_name: str


class UserCreate(UserBase):
    password: str
    consent_given: bool = False


class UserLogin(BaseModel):
    email: str
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    id: int
    role: UserRole
    plan: PlanType
    is_active: bool
    is_verified: bool
    total_audios_generated: int
    monthly_audios_used: int
    created_at: datetime
    consent_given: bool
    
    class Config:
        from_attributes = True


class UserProfileResponse(UserResponse):
    voices_count: int
    generations_count: int


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None


# ============= Voice Schemas =============

class VoiceBase(BaseModel):
    name: str
    description: Optional[str] = None
    language: str = "en"


class VoiceCreate(VoiceBase):
    ownership_verified: bool = False
    ownership_notes: Optional[str] = None


class VoiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None


class VoiceResponse(VoiceBase):
    id: int
    user_id: int
    file_name: str
    file_size: int
    duration_seconds: Optional[float]
    elevenlabs_voice_id: Optional[str]
    is_active: bool
    is_default: bool
    ownership_verified: bool
    quality_score: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True


class VoiceListResponse(BaseModel):
    voices: List[VoiceResponse]
    total: int


# ============= Audio Generation Schemas =============

class AudioGenerationBase(BaseModel):
    voice_id: int
    script_text: str
    language: str = "en"
    stability: float = 0.5
    similarity_boost: float = 0.75


class AudioGenerationCreate(AudioGenerationBase):
    tags: Optional[str] = None


class AudioGenerationResponse(AudioGenerationBase):
    id: int
    user_id: int
    output_file_name: str
    duration_seconds: Optional[float]
    file_size: Optional[int]
    status: str
    is_favorite: bool
    tags: Optional[str]
    watermark_id: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AudioGenerationDetailResponse(AudioGenerationResponse):
    voice: VoiceResponse


class AudioGenerationListResponse(BaseModel):
    generations: List[AudioGenerationResponse]
    total: int
    monthly_minutes_used: float
    plan_minutes_limit: int


class AudioGenerationUpdate(BaseModel):
    is_favorite: Optional[bool] = None
    tags: Optional[str] = None


# ============= Dashboard Schemas =============

class DashboardStats(BaseModel):
    total_voices: int
    total_generations: int
    total_minutes_used: float
    monthly_minutes_used: float
    plan_minutes_limit: int
    remaining_minutes: float
    remaining_credits: int
    recent_generations: List[AudioGenerationResponse]


class UsageChartData(BaseModel):
    date: str
    minutes: float
    generations: int


class UsageReport(BaseModel):
    chart_data: List[UsageChartData]
    total_minutes: float
    total_generations: int


# ============= Payment Schemas =============

class PaymentCreate(BaseModel):
    plan: PlanType


class PaymentResponse(BaseModel):
    id: int
    plan: PlanType
    amount: float
    currency: str
    status: str
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class PlanInfo(BaseModel):
    plan: PlanType
    name: str
    price_monthly: float
    minutes_limit: int
    features: List[str]
    is_current_plan: bool


# ============= Admin Schemas =============

class AdminUserList(BaseModel):
    users: List[UserResponse]
    total: int
    active_count: int
    pending_verification: int


class AdminVoiceModeration(BaseModel):
    voices: List[VoiceResponse]
    pending_ownership_verification: int


class AdminStats(BaseModel):
    total_users: int
    active_users: int
    total_voices: int
    total_generations: int
    total_revenue: float
    recent_signups: int
    flagged_content: int


class ModerationAction(BaseModel):
    user_id: int
    action: str  # approve, reject, suspend, delete
    reason: Optional[str] = None


# ============= Consent Schemas =============

class ConsentForm(BaseModel):
    consent_given: bool
    voice_ownership_confirmed: bool
    usage_purpose: str
    agree_to_terms: bool
    agree_to_privacy: bool


# ============= Watermark Verification =============

class WatermarkVerifyRequest(BaseModel):
    file_path: str


class WatermarkVerifyResponse(BaseModel):
    is_valid: bool
    owner_id: Optional[int]
    owner_email: Optional[str]
    generation_date: Optional[datetime]
    watermark_id: Optional[str]
