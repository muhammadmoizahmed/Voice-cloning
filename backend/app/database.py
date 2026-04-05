from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

from app.config import get_settings

settings = get_settings()

# Database setup
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class UserRole(str, enum.Enum):
    GUEST = "guest"
    USER = "user"
    MODERATOR = "moderator"  # Sub-admin with limited access
    ADMIN = "admin"


class PlanType(str, enum.Enum):
    FREE = "free"
    STARTER = "starter"  # $5/month - 50 audios
    PRO = "pro"          # $15/month - 200 audios
    BUSINESS = "business"  # $30/month - 500 audios


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    
    # Role & Plan
    role = Column(Enum(UserRole), default=UserRole.USER)
    plan = Column(Enum(PlanType), default=PlanType.FREE)
    # plan_id = Column(Integer, ForeignKey("plans.id"), nullable=True)  # Temporarily disabled
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    
    # Usage tracking (Audio-based pricing)
    total_audios_generated = Column(Integer, default=0)  # Lifetime count
    monthly_audios_used = Column(Integer, default=0)     # Monthly subscription usage
    purchased_credits = Column(Integer, default=0)      # Pay-per-audio credits
    
    # Plan renewal tracking
    plan_renewal_date = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Security
    consent_given = Column(Boolean, default=False)
    consent_date = Column(DateTime, nullable=True)
    
    # Email OTP Verification
    otp_code = Column(String, nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    is_otp_verified = Column(Boolean, default=False)
    
    # Password Reset
    reset_token = Column(String, nullable=True, index=True)
    reset_token_expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    voices = relationship("Voice", back_populates="user", cascade="all, delete-orphan")
    generations = relationship("AudioGeneration", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    # plan_details = relationship("Plan", foreign_keys=[plan_id])  # Temporarily disabled
    
    @property
    def credits_remaining(self):
        """Calculate remaining credits based on plan and usage"""
        from app.config import get_settings
        settings = get_settings()
        
        # Get plan limit
        plan_limits = {
            PlanType.FREE: settings.free_plan_audios,
            PlanType.STARTER: settings.starter_plan_audios,
            PlanType.PRO: settings.pro_plan_audios,
            PlanType.BUSINESS: settings.business_plan_audios,
        }
        plan_limit = plan_limits.get(self.plan, 0)
        
        # Calculate remaining
        remaining = plan_limit - self.monthly_audios_used + self.purchased_credits
        return max(0, remaining)


class Voice(Base):
    __tablename__ = "voices"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Voice details
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # File info
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    duration_seconds = Column(Float, nullable=True)
    
    # External API
    elevenlabs_voice_id = Column(String, nullable=True)  # Voice ID from ElevenLabs
    
    # Status
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # Metadata
    language = Column(String, default="en")
    quality_score = Column(Float, nullable=True)  # Cloning quality score
    
    # Ownership verification
    ownership_verified = Column(Boolean, default=False)
    ownership_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="voices")
    generations = relationship("AudioGeneration", back_populates="voice")


class AudioGeneration(Base):
    __tablename__ = "audio_generations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    voice_id = Column(Integer, ForeignKey("voices.id"), nullable=False)
    
    # Generation details
    script_text = Column(Text, nullable=False)
    output_file_path = Column(String, nullable=False)
    output_file_name = Column(String, nullable=False)
    
    # Audio properties
    duration_seconds = Column(Float, nullable=True)
    file_size = Column(Integer, nullable=True)
    
    # Settings used
    language = Column(String, default="en")
    stability = Column(Float, default=0.5)
    similarity_boost = Column(Float, default=0.75)
    
    # Watermark
    watermark_id = Column(String, nullable=True)  # Unique watermark for tracking
    watermark_data = Column(String, nullable=True)  # Encoded ownership info
    
    # Status
    status = Column(String, default="completed")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    
    # Metadata
    is_favorite = Column(Boolean, default=False)
    tags = Column(String, nullable=True)  # Comma-separated tags
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="generations")
    voice = relationship("Voice", back_populates="generations")


class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Payment details
    plan = Column(Enum(PlanType), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    
    # Stripe info
    stripe_payment_intent_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    
    # Status
    status = Column(String, default="pending")  # pending, completed, failed, refunded
    
    # Period
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="payments")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Action details
    action = Column(String, nullable=False)  # voice_upload, generation, login, etc.
    resource_type = Column(String, nullable=True)  # voice, generation, user
    resource_id = Column(Integer, nullable=True)
    
    # Metadata
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    details = Column(Text, nullable=True)  # JSON string with additional info
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)


class Plan(Base):
    __tablename__ = "plans"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Plan details
    name = Column(String, nullable=False, unique=True)  # e.g., "FREE", "STARTER"
    display_name = Column(String, nullable=False)  # e.g., "Free Plan", "Starter Plan"
    description = Column(Text, nullable=True)
    
    # Pricing
    price_monthly = Column(Float, nullable=False, default=0.0)  # Monthly price in USD
    price_yearly = Column(Float, nullable=True)  # Yearly price in USD (optional)
    currency = Column(String, default="USD")
    
    # Limits
    audio_limit = Column(Integer, nullable=False, default=0)  # Number of audios per month
    video_limit = Column(Integer, nullable=True)  # Number of videos per month (optional)
    voice_clone_limit = Column(Integer, nullable=True)  # Number of voice clones allowed
    
    # Features
    features = Column(Text, nullable=True)  # JSON array of features
    is_active = Column(Boolean, default=True)  # Whether plan is available for new subscriptions
    is_popular = Column(Boolean, default=False)  # Highlight as popular plan
    
    # Display order
    sort_order = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # users = relationship("User", back_populates="plan_details", foreign_keys="User.plan_id")  # Temporarily disabled


# Dependency for database sessions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)
    # Seed default plans after tables are created
    seed_default_plans()

def seed_default_plans():
    """Seed default plans if none exist"""
    db = SessionLocal()
    try:
        # Check if plans already exist
        existing = db.query(Plan).count()
        if existing > 0:
            return
        
        # Create default plans based on pricing page
        default_plans = [
            Plan(
                name="FREE",
                display_name="Free",
                description="Try it out",
                price_monthly=0,
                price_yearly=None,
                audio_limit=3,
                video_limit=0,
                voice_clone_limit=1,
                features='["3 audio generations", "Basic quality", "Watermark", "Email support"]',
                is_active=True,
                is_popular=False,
                sort_order=1
            ),
            Plan(
                name="STARTER",
                display_name="Starter",
                description="Perfect start",
                price_monthly=5,
                price_yearly=50,
                audio_limit=50,
                video_limit=10,
                voice_clone_limit=3,
                features='["50 audio/month", "High quality", "No watermark", "Priority support"]',
                is_active=True,
                is_popular=False,
                sort_order=2
            ),
            Plan(
                name="PRO",
                display_name="Pro",
                description="For creators",
                price_monthly=15,
                price_yearly=150,
                audio_limit=200,
                video_limit=50,
                voice_clone_limit=10,
                features='["200 audio/month", "Ultra quality", "API access", "24/7 support"]',
                is_active=True,
                is_popular=True,
                sort_order=3
            ),
            Plan(
                name="BUSINESS",
                display_name="Business",
                description="For teams",
                price_monthly=30,
                price_yearly=300,
                audio_limit=500,
                video_limit=100,
                voice_clone_limit=25,
                features='["500 audio/month", "Ultra quality", "Full API", "Team collaboration"]',
                is_active=True,
                is_popular=False,
                sort_order=4
            ),
            # Bulk Credit Packages
            Plan(
                name="CREDIT_50",
                display_name="50 Credits",
                description="Best for beginners",
                price_monthly=20,
                price_yearly=None,
                audio_limit=50,
                video_limit=0,
                voice_clone_limit=0,
                features='["50 audio credits", "Never expires", "No subscription needed", "Best for beginners"]',
                is_active=True,
                is_popular=False,
                sort_order=5
            ),
            Plan(
                name="CREDIT_100",
                display_name="100 Credits",
                description="Most popular",
                price_monthly=35,
                price_yearly=None,
                audio_limit=100,
                video_limit=0,
                voice_clone_limit=0,
                features='["100 audio credits", "Never expires", "No subscription needed", "Most popular", "Save $65"]',
                is_active=True,
                is_popular=True,
                sort_order=6
            ),
            Plan(
                name="CREDIT_200",
                display_name="200 Credits",
                description="Best value",
                price_monthly=60,
                price_yearly=None,
                audio_limit=200,
                video_limit=0,
                voice_clone_limit=0,
                features='["200 audio credits", "Never expires", "No subscription needed", "Best value", "Save $140"]',
                is_active=True,
                is_popular=False,
                sort_order=7
            )
        ]
        
        for plan in default_plans:
            db.add(plan)
        
        db.commit()
        print("✅ Default plans seeded successfully")
    except Exception as e:
        print(f"⚠️ Error seeding plans: {e}")
    finally:
        db.close()
