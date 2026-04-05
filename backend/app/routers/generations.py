from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from app.database import get_db, User, Voice, AudioGeneration
from app.config import get_settings
from app.schemas.schemas import (
    AudioGenerationCreate, AudioGenerationResponse, 
    AudioGenerationDetailResponse, AudioGenerationListResponse,
    AudioGenerationUpdate
)
from app.utils.auth import get_current_user
from app.utils.usage_v2 import UsageTracker
from app.utils.watermark import apply_watermark
from app.services.elevenlabs import elevenlabs_service
from app.services.fish_audio import fish_audio_service
from app.services.resemble_ai import resemble_service

settings = get_settings()
router = APIRouter(prefix="/api/generations", tags=["Audio Generations"])


@router.get("/avatar-videos")
async def list_avatar_videos(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List avatar videos for current user"""
    # Return empty list for now - avatar video generation not yet implemented
    return {
        "videos": [],
        "total": 0,
        "message": "Avatar video feature coming soon"
    }


@router.post("/", response_model=AudioGenerationResponse)
async def generate_audio(
    data: AudioGenerationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate audio from text script"""
    
    # Check consent
    if not current_user.consent_given:
        raise HTTPException(
            status_code=403,
            detail="Consent required. Please complete consent form first."
        )
    
    # Get voice
    voice = db.query(Voice).filter(
        Voice.id == data.voice_id,
        Voice.user_id == current_user.id,
        Voice.is_active == True
    ).first()
    
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    
    # Use cloned voice ID if available, otherwise use default voice
    voice_id_to_use = voice.elevenlabs_voice_id
    is_cloned_voice = voice_id_to_use is not None
    
    if not voice_id_to_use:
        # Use a default voice ID for testing (this would be a default Resemble AI voice)
        voice_id_to_use = "default-voice-001"
        print(f"Using default voice for generation (voice not cloned yet)")
    
    # Check usage limits (audio-based pricing)
    usage_check = UsageTracker.can_generate_audio(current_user)
    if not usage_check["can_generate"]:
        raise HTTPException(
            status_code=403,
            detail="No credits available. Please upgrade your plan or purchase credits."
        )
    
    # Create output directory
    os.makedirs(settings.output_dir, exist_ok=True)
    
    # Generate unique filename
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = f"gen_{current_user.id}_{voice.id}_{timestamp}.mp3"
    output_path = os.path.join(settings.output_dir, output_filename)
    
    # Generate audio with Resemble AI
    success = await resemble_service.text_to_speech(
        text=data.script_text,
        voice_id=voice_id_to_use,
        output_path=output_path,
        language=data.language
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Audio generation failed")
    
    # Get file info
    file_size = os.path.getsize(output_path)
    
    # Create database record
    generation = AudioGeneration(
        user_id=current_user.id,
        voice_id=data.voice_id,
        script_text=data.script_text,
        output_file_path=output_path,
        output_file_name=output_filename,
        duration_seconds=0,  # Will be updated
        file_size=file_size,
        language=data.language,
        stability=data.stability,
        similarity_boost=data.similarity_boost,
        status="completed",
        tags=data.tags
    )
    
    db.add(generation)
    db.flush()  # Get ID without committing
    
    # Apply watermark (always enabled for free plan)
    if settings.watermark_enabled or current_user.plan.value == "free":
        watermark_id = apply_watermark(output_path, current_user.id, generation.id)
        generation.watermark_id = watermark_id
    
    # Use one credit
    credit_used = UsageTracker.use_credit(db, current_user)
    if not credit_used:
        db.rollback()
        raise HTTPException(status_code=403, detail="Failed to use credit")
    
    db.commit()
    db.refresh(generation)
    
    return generation


@router.get("/", response_model=AudioGenerationListResponse)
async def list_generations(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    voice_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List audio generations for current user"""
    
    query = db.query(AudioGeneration).filter(
        AudioGeneration.user_id == current_user.id
    )
    
    if voice_id:
        query = query.filter(AudioGeneration.voice_id == voice_id)
    
    total = query.count()
    
    generations = query.order_by(
        AudioGeneration.created_at.desc()
    ).offset((page - 1) * limit).limit(limit).all()
    
    # Get available credits
    available = UsageTracker.get_available_generations(current_user)
    
    # Calculate minutes estimates
    monthly_minutes_used = round(current_user.monthly_audios_used * 0.5, 2)
    plan_minutes_limit = int(available["subscription_limit"] * 0.5)
    
    return {
        "generations": generations,
        "total": total,
        "monthly_audios_used": current_user.monthly_audios_used,
        "subscription_limit": available["subscription_limit"],
        "purchased_credits": available["purchased_credits"],
        "total_available": available["total_available"],
        "monthly_minutes_used": monthly_minutes_used,
        "plan_minutes_limit": plan_minutes_limit
    }


@router.get("/{generation_id}", response_model=AudioGenerationDetailResponse)
async def get_generation(
    generation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get generation details"""
    generation = db.query(AudioGeneration).filter(
        AudioGeneration.id == generation_id,
        AudioGeneration.user_id == current_user.id
    ).first()
    
    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")
    
    return generation


@router.get("/{generation_id}/download")
async def download_generation(
    generation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download generated audio file"""
    generation = db.query(AudioGeneration).filter(
        AudioGeneration.id == generation_id,
        AudioGeneration.user_id == current_user.id
    ).first()
    
    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")
    
    if not os.path.exists(generation.output_file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(
        generation.output_file_path,
        filename=generation.output_file_name,
        media_type='audio/mpeg'
    )


@router.put("/{generation_id}", response_model=AudioGenerationResponse)
async def update_generation(
    generation_id: int,
    update_data: AudioGenerationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update generation (favorite, tags)"""
    generation = db.query(AudioGeneration).filter(
        AudioGeneration.id == generation_id,
        AudioGeneration.user_id == current_user.id
    ).first()
    
    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")
    
    if update_data.is_favorite is not None:
        generation.is_favorite = update_data.is_favorite
    
    if update_data.tags is not None:
        generation.tags = update_data.tags
    
    db.commit()
    db.refresh(generation)
    return generation


@router.delete("/{generation_id}")
async def delete_generation(
    generation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a generation"""
    generation = db.query(AudioGeneration).filter(
        AudioGeneration.id == generation_id,
        AudioGeneration.user_id == current_user.id
    ).first()
    
    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")
    
    # Delete file
    if os.path.exists(generation.output_file_path):
        os.remove(generation.output_file_path)
    
    db.delete(generation)
    db.commit()
    
    return {"message": "Generation deleted successfully"}


@router.get("/{generation_id}/verify")
async def verify_generation_watermark(
    generation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify watermark on generated audio"""
    generation = db.query(AudioGeneration).filter(
        AudioGeneration.id == generation_id,
        AudioGeneration.user_id == current_user.id
    ).first()
    
    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")
    
    return {
        "watermark_id": generation.watermark_id,
        "owner_id": current_user.id,
        "owner_email": current_user.email,
        "generation_date": generation.created_at,
        "is_valid": generation.watermark_id is not None
    }
