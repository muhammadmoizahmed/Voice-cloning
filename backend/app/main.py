"""
VoiceForge AI - FastAPI Backend
Full-featured voice cloning platform with authentication, dashboard, and admin panel
"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

from app.config import get_settings
from app.database import create_tables, User, UserRole
from app.routers import auth, voices, generations, dashboard, admin, payments, face_detection
from app.utils.auth import get_current_active_user, get_current_user_optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Setup templates
templates = Jinja2Templates(directory="templates")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info("Starting VoiceForge AI Platform...")
    
    # Create directories
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.output_dir, exist_ok=True)
    
    # Create database tables
    create_tables()
    logger.info("Database tables created")
    
    yield
    
    # Shutdown
    logger.info("Shutting down VoiceForge AI Platform...")


# Create FastAPI app
app = FastAPI(
    title="VoiceForge AI",
    description="AI Voice Cloning Platform - Convert your voice into a digital scalable asset",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(voices.router)
app.include_router(generations.router)
app.include_router(dashboard.router)
app.include_router(payments.router)
app.include_router(admin.router)
app.include_router(face_detection.router)

# Static files for uploads (in production, use CDN)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")
app.mount("/outputs", StaticFiles(directory=settings.output_dir), name="outputs")

# Serve static files for CSS/JS
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/api/info")
async def api_info():
    """API info endpoint"""
    return {
        "app": "VoiceForge AI",
        "version": "1.0.0",
        "description": "AI Voice Cloning Platform",
        "endpoints": {
            "auth": "/api/v1/auth",
            "voices": "/api/v1/voices",
            "generations": "/api/v1/generations",
            "dashboard": "/api/v1/dashboard",
            "payments": "/api/v1/payments",
            "admin": "/api/v1/admin"
        },
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z"
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# HTML Template Routes
@app.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    """Landing page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Signup page"""
    return templates.TemplateResponse("signup.html", {"request": request})

@app.get("/verify-otp", response_class=HTMLResponse)
async def verify_otp_page(request: Request, email: str = ""):
    """OTP verification page"""
    return templates.TemplateResponse("verify-otp.html", {"request": request, "email": email})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, user: User = Depends(get_current_user_optional)):
    """Dashboard page - redirects to login if not authenticated"""
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

@app.get("/voices", response_class=HTMLResponse)
async def voices_page(request: Request, user: User = Depends(get_current_user_optional)):
    """Voices page - requires authentication"""
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("voices.html", {"request": request, "user": user})

@app.get("/generate", response_class=HTMLResponse)
async def generate_page(request: Request, user: User = Depends(get_current_user_optional)):
    """Generate audio page - requires authentication"""
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("generate.html", {"request": request, "user": user})

@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request, user: User = Depends(get_current_user_optional)):
    """History page - requires authentication"""
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("history.html", {"request": request, "user": user})

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, user: User = Depends(get_current_user_optional)):
    """Settings page - requires authentication"""
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("settings.html", {"request": request, "user": user})

@app.get("/upgrade", response_class=HTMLResponse)
async def upgrade_page(request: Request, user: User = Depends(get_current_user_optional)):
    """Upgrade page - requires authentication"""
    print(f"DEBUG: Upgrade page accessed - user: {user}, user_id: {user.id if user else None}")
    if not user:
        print("DEBUG: No user found, redirecting to login")
        return RedirectResponse(url="/login", status_code=302)
    print(f"DEBUG: User found: {user.email}, plan: {user.plan}")
    return templates.TemplateResponse("upgrade.html", {"request": request, "user": user})

@app.get("/avatar", response_class=HTMLResponse)
async def avatar_page(request: Request, user: User = Depends(get_current_user_optional)):
    """AI Avatar video page - requires authentication"""
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("avatar.html", {"request": request, "user": user})

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Admin login page"""
    return templates.TemplateResponse("admin/login.html", {"request": request})

@app.get("/admin/logout", response_class=HTMLResponse)
async def admin_logout_page(request: Request):
    """Admin logout page - clears auth and redirects to home"""
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("access_token")
    return response

@app.get("/logout", response_class=HTMLResponse)
async def logout_page(request: Request):
    """User logout page - clears auth and redirects to login"""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, user: User = Depends(get_current_user_optional)):
    """Admin dashboard page - requires admin role"""
    if not user:
        return RedirectResponse(url="/admin/login", status_code=302)
    if user.role != UserRole.ADMIN:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("admin/dashboard.html", {"request": request, "user": user})

@app.get("/admin/users", response_class=HTMLResponse)
async def admin_users_page(request: Request, user: User = Depends(get_current_user_optional)):
    """Admin users management page - requires admin role"""
    if not user:
        return RedirectResponse(url="/admin/login", status_code=302)
    if user.role != UserRole.ADMIN:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("admin/users.html", {"request": request, "user": user})

@app.get("/admin/voices", response_class=HTMLResponse)
async def admin_voices_page(request: Request, user: User = Depends(get_current_user_optional)):
    """Admin voice moderation page - requires admin role"""
    if not user:
        return RedirectResponse(url="/admin/login", status_code=302)
    if user.role != UserRole.ADMIN:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("admin/voices.html", {"request": request, "user": user})

@app.get("/admin/sub-admins", response_class=HTMLResponse)
async def admin_sub_admins_page(request: Request, user: User = Depends(get_current_user_optional)):
    """Admin sub-admins page - requires admin role"""
    if not user:
        return RedirectResponse(url="/admin/login", status_code=302)
    if user.role != UserRole.ADMIN:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("admin/sub-admins.html", {"request": request, "user": user})

@app.get("/admin/settings", response_class=HTMLResponse)
async def admin_settings_page(request: Request, user: User = Depends(get_current_user_optional)):
    """Admin settings page - requires admin role"""
    if not user:
        return RedirectResponse(url="/admin/login", status_code=302)
    if user.role != UserRole.ADMIN:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("admin/settings.html", {"request": request, "user": user})

@app.get("/admin/plans", response_class=HTMLResponse)
async def admin_plans_page(request: Request, user: User = Depends(get_current_user_optional)):
    """Admin plans management page - requires admin role"""
    if not user:
        return RedirectResponse(url="/admin/login", status_code=302)
    if user.role != UserRole.ADMIN:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("admin/plans.html", {"request": request, "user": user})


# Sub-Admin Routes (Moderator)
@app.get("/sub-admin", response_class=HTMLResponse)
async def sub_admin_page(request: Request, user: User = Depends(get_current_user_optional)):
    """Sub-Admin dashboard page - requires moderator or admin role"""
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    if user.role not in [UserRole.MODERATOR, UserRole.ADMIN]:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("sub-admin/dashboard.html", {"request": request, "user": user})

@app.get("/sub-admin/users", response_class=HTMLResponse)
async def sub_admin_users_page(request: Request, user: User = Depends(get_current_user_optional)):
    """Sub-Admin users page - requires moderator or admin role"""
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    if user.role not in [UserRole.MODERATOR, UserRole.ADMIN]:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("sub-admin/users.html", {"request": request, "user": user})

@app.get("/sub-admin/voices", response_class=HTMLResponse)
async def sub_admin_voices_page(request: Request, user: User = Depends(get_current_user_optional)):
    """Sub-Admin voices review page - requires moderator or admin role"""
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    if user.role not in [UserRole.MODERATOR, UserRole.ADMIN]:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("sub-admin/voices.html", {"request": request, "user": user})

@app.get("/sub-admin/reports", response_class=HTMLResponse)
async def sub_admin_reports_page(request: Request, user: User = Depends(get_current_user_optional)):
    """Sub-Admin reports page - requires moderator or admin role"""
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    if user.role not in [UserRole.MODERATOR, UserRole.ADMIN]:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("sub-admin/reports.html", {"request": request, "user": user})


@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    """Forgot password page"""
    return templates.TemplateResponse("forgot-password.html", {"request": request})

@app.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request, token: str = ""):
    """Reset password page"""
    return templates.TemplateResponse("reset-password.html", {"request": request, "token": token})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
