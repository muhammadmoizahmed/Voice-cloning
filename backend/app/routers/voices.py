from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime

from app.database import get_db, User, Voice
from app.config import get_settings
from app.schemas.schemas import VoiceCreate, VoiceResponse, VoiceUpdate, VoiceListResponse
from app.utils.auth import get_current_user
from app.services.elevenlabs import elevenlabs_service
from app.services.fish_audio import fish_audio_service
from app.services.resemble_ai import resemble_service

settings = get_settings()
router = APIRouter(prefix="/api/voices", tags=["Voices"])

ALLOWED_AUDIO_TYPES = ['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/x-wav', 'audio/wave']
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def validate_audio_file(file: UploadFile) -> None:
    """Validate uploaded audio file"""
    if file.content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {ALLOWED_AUDIO_TYPES}"
        )


@router.post("/upload", response_model=VoiceResponse)
async def upload_voice(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    language: str = Form("en"),
    ownership_verified: bool = Form(False),
    ownership_notes: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a new voice sample"""
    
    # Check consent
    if not current_user.consent_given:
        raise HTTPException(
            status_code=403,
            detail="Consent required. Please complete consent form first."
        )
    
    # Validate file
    validate_audio_file(file)
    
    # Save file
    os.makedirs(settings.upload_dir, exist_ok=True)
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"voice_{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_extension}"
    file_path = os.path.join(settings.upload_dir, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Get file size
    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail="File too large. Max 10MB.")
    
    # Clone voice with Resemble AI (optional, don't fail if cloning fails)
    resemble_voice_id = None
    try:
        resemble_voice_id = await resemble_service.clone_voice(
            name=name,
            audio_path=file_path,
            description=description or f"Voice uploaded by {current_user.email}"
        )
        if resemble_voice_id:
            print(f"Voice cloned successfully: {resemble_voice_id}")
    except Exception as e:
        print(f"Voice cloning failed (non-blocking): {e}")
        # Continue anyway - voice is uploaded even if cloning fails
    
    # Create database record (even if cloning failed)
    voice = Voice(
        user_id=current_user.id,
        name=name,
        description=description,
        file_path=file_path,
        file_name=file.filename,
        file_size=file_size,
        language=language,
        elevenlabs_voice_id=resemble_voice_id,  # Can be None if cloning failed
        ownership_verified=ownership_verified,
        ownership_notes=ownership_notes
    )
    
    # If first voice, set as default
    existing_voices = db.query(Voice).filter(Voice.user_id == current_user.id).count()
    if existing_voices == 0:
        voice.is_default = True
    
    db.add(voice)
    db.commit()
    db.refresh(voice)
    
    return voice


@router.get("/", response_model=VoiceListResponse)
async def list_voices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all voices for current user"""
    voices = db.query(Voice).filter(
        Voice.user_id == current_user.id,
        Voice.is_active == True
    ).order_by(Voice.created_at.desc()).all()
    
    return {"voices": voices, "total": len(voices)}


@router.get("/{voice_id}", response_model=VoiceResponse)
async def get_voice(
    voice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get voice details"""
    voice = db.query(Voice).filter(
        Voice.id == voice_id,
        Voice.user_id == current_user.id
    ).first()
    
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    
    return voice


@router.put("/{voice_id}", response_model=VoiceResponse)
async def update_voice(
    voice_id: int,
    update_data: VoiceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update voice details"""
    voice = db.query(Voice).filter(
        Voice.id == voice_id,
        Voice.user_id == current_user.id
    ).first()
    
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    
    if update_data.name:
        voice.name = update_data.name
    if update_data.description is not None:
        voice.description = update_data.description
    if update_data.is_default is not None:
        # Remove default from other voices
        if update_data.is_default:
            db.query(Voice).filter(
                Voice.user_id == current_user.id,
                Voice.is_default == True
            ).update({"is_default": False})
        voice.is_default = update_data.is_default
    
    db.commit()
    db.refresh(voice)
    return voice


@router.delete("/{voice_id}")
async def delete_voice(
    voice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a voice (soft delete)"""
    voice = db.query(Voice).filter(
        Voice.id == voice_id,
        Voice.user_id == current_user.id
    ).first()
    
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    
    # Delete from Resemble AI
    if voice.elevenlabs_voice_id:
        await resemble_service.delete_voice(voice.elevenlabs_voice_id)
    
    # Soft delete
    voice.is_active = False
    db.commit()
    
    return {"message": "Voice deleted successfully"}


@router.post("/{voice_id}/clone")
async def clone_pending_voice(
    voice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually trigger voice cloning for a pending voice"""
    voice = db.query(Voice).filter(
        Voice.id == voice_id,
        Voice.user_id == current_user.id
    ).first()
    
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    
    # If already cloned, return success
    if voice.elevenlabs_voice_id:
        return {"message": "Voice already cloned", "voice_id": voice.elevenlabs_voice_id}
    
    # Check if file exists
    if not os.path.exists(voice.file_path):
        raise HTTPException(status_code=404, detail="Voice file not found")
    
    # Try to clone
    try:
        resemble_voice_id = await resemble_service.clone_voice(
            name=voice.name,
            audio_path=voice.file_path,
            description=voice.description or f"Voice: {voice.name}"
        )
        
        if not resemble_voice_id:
            raise HTTPException(status_code=500, detail="Cloning failed. Please try again.")
        
        # Update voice record
        voice.elevenlabs_voice_id = resemble_voice_id
        db.commit()
        
        return {"message": "Voice cloned successfully", "voice_id": resemble_voice_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cloning failed: {str(e)}")


@router.get("/{voice_id}/download")
async def download_voice_sample(
    voice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download original voice sample"""
    from fastapi.responses import FileResponse
    
    voice = db.query(Voice).filter(
        Voice.id == voice_id,
        Voice.user_id == current_user.id
    ).first()
    
    if not voice or not os.path.exists(voice.file_path):
        raise HTTPException(status_code=404, detail="Voice file not found")
    
    return FileResponse(
        voice.file_path,
        filename=voice.file_name,
        media_type='audio/mpeg'
    )
