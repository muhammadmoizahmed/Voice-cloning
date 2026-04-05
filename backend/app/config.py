from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "VoiceForge AI"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database
    database_url: str = "sqlite:///./voiceforge.db"
    
    # JWT
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # Frontend URL (for password reset links)
    frontend_url: str = "http://localhost:8003"
    
    # File Paths
    upload_dir: str = "uploads"
    output_dir: str = "outputs"
    max_upload_size: int = 50 * 1024 * 1024  # 50MB
    
    # External APIs
    elevenlabs_api_key: str = ""
    fish_audio_api_key: str = ""
    resemble_api_key: str = ""
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    
    # Email Configuration (for OTP & notifications)
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    from_email: str = ""
    from_name: str = "VoiceForge AI"
    
    # Pricing Strategy (Audio-based, not minutes)
    # Cost per audio: $0.15, Sell: $1.00 (6.7x markup)
    
    # Subscription Plans (number of audio generations)
    free_plan_audios: int = 3
    starter_plan_price: float = 5.0  # $5/month
    starter_plan_audios: int = 50
    pro_plan_price: float = 15.0  # $15/month
    pro_plan_audios: int = 200
    business_plan_price: float = 30.0  # $30/month
    business_plan_audios: int = 500
    
    # Pay Per Audio
    pay_per_audio_price: float = 1.0  # $1 per audio
    
    # Bulk Packages
    bulk_package_50_price: float = 20.0  # 50 audios for $20 (save $30)
    bulk_package_100_price: float = 35.0  # 100 audios for $35 (save $65)
    bulk_package_200_price: float = 60.0  # 200 audios for $60 (save $140)
    
    # API Costs (internal tracking)
    cost_per_audio_api: float = 0.15  # $0.15 per minute to ElevenLabs
    
    # Security
    watermark_enabled: bool = True
    require_voice_ownership: bool = True
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
