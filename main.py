import os
import uuid
import logging
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings, ensure_directories
from app.models.schemas import (
    VoiceCloneRequest, 
    LipSyncRequest, 
    ProcessingResponse,
    TaskStatus
)
from app.services.voice_cloning_api import voice_cloning_service
from app.services.lip_sync_api import lip_sync_service
from app.utils.video_utils import VideoUtils, AudioUtils

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# In-memory task store (replace with Redis/DB in production)
tasks = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info("Starting VoiceForge AI...")
    ensure_directories()
    yield
    # Shutdown
    logger.info("Shutting down VoiceForge AI...")


app = FastAPI(
    title="VoiceForge AI",
    description="Voice Cloning and Lip-Sync Deepfake API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_unique_filename(original_filename: str) -> str:
    """Generate unique filename"""
    ext = os.path.splitext(original_filename)[1]
    return f"{uuid.uuid4().hex}{ext}"


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": "VoiceForge AI",
        "version": "1.0.0",
        "endpoints": {
            "voice_clone": "/api/v1/voice/clone",
            "lip_sync_video": "/api/v1/lipsync/video",
            "lip_sync_image": "/api/v1/lipsync/image",
            "full_pipeline": "/api/v1/generate/talking-head",
            "task_status": "/api/v1/tasks/{task_id}"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# =============================================================================
# Voice Cloning Endpoints
# =============================================================================

@app.post("/api/v1/voice/clone", response_model=ProcessingResponse)
async def clone_voice(
    background_tasks: BackgroundTasks,
    text: str = Form(..., description="Text to synthesize"),
    language: str = Form("en", description="Language code (en, hi, ur, etc.)"),
    speaker_audio: UploadFile = File(..., description="Reference voice sample (WAV/MP3)")
):
    """
    Clone a voice from reference audio and generate speech from text.
    
    - **text**: Text you want the cloned voice to say
    - **language**: Language code (en, hi, ur, etc.)
    - **speaker_audio**: Audio file of the voice to clone (WAV/MP3)
    """
    try:
        settings = get_settings()
        
        # Validate file type
        allowed_types = ['audio/wav', 'audio/x-wav', 'audio/mpeg', 'audio/mp3', 'audio/wave']
        if speaker_audio.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid audio format. Allowed: {allowed_types}"
            )
        
        # Save uploaded audio
        audio_filename = get_unique_filename(speaker_audio.filename)
        audio_path = os.path.join(settings.upload_dir, audio_filename)
        
        with open(audio_path, "wb") as f:
            content = await speaker_audio.read()
            f.write(content)
        
        # Create task
        task_id = str(uuid.uuid4())
        tasks[task_id] = TaskStatus(
            task_id=task_id,
            status="processing",
            progress=0.0,
            message="Starting voice cloning...",
            created_at=datetime.now()
        )
        
        # Process in background
        def process_voice_clone():
            try:
                tasks[task_id].progress = 0.3
                tasks[task_id].message = "Generating cloned voice..."
                
                import asyncio
                output_path = asyncio.run(voice_cloning_service.clone_and_speak(
                    text=text,
                    audio_path=audio_path,
                    voice_name=f"Cloned_{task_id[:8]}"
                ))
                
                tasks[task_id].status = "completed"
                tasks[task_id].progress = 1.0
                tasks[task_id].message = "Voice cloning completed"
                tasks[task_id].output_path = output_path
                tasks[task_id].updated_at = datetime.now()
                
            except Exception as e:
                tasks[task_id].status = "failed"
                tasks[task_id].message = str(e)
                tasks[task_id].updated_at = datetime.now()
                logger.error(f"Voice cloning failed: {e}")
        
        background_tasks.add_task(process_voice_clone)
        
        return ProcessingResponse(
            success=True,
            message="Voice cloning started",
            task_id=task_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in clone_voice: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Lip Sync Endpoints
# =============================================================================

@app.post("/api/v1/lipsync/video", response_model=ProcessingResponse)
async def lip_sync_video(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(..., description="Video file with face"),
    audio: UploadFile = File(..., description="Audio file to sync")
):
    """
    Apply lip-sync to a video with the provided audio.
    
    The face in the video will be animated to match the audio.
    """
    try:
        settings = get_settings()
        
        # Validate files
        allowed_video = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-msvideo']
        allowed_audio = ['audio/wav', 'audio/x-wav', 'audio/mpeg', 'audio/mp3']
        
        if video.content_type not in allowed_video:
            raise HTTPException(status_code=400, detail=f"Invalid video format. Allowed: {allowed_video}")
        if audio.content_type not in allowed_audio:
            raise HTTPException(status_code=400, detail=f"Invalid audio format. Allowed: {allowed_audio}")
        
        # Save files
        video_filename = get_unique_filename(video.filename)
        audio_filename = get_unique_filename(audio.filename)
        video_path = os.path.join(settings.upload_dir, video_filename)
        audio_path = os.path.join(settings.upload_dir, audio_filename)
        
        with open(video_path, "wb") as f:
            f.write(await video.read())
        with open(audio_path, "wb") as f:
            f.write(await audio.read())
        
        # Create task
        task_id = str(uuid.uuid4())
        tasks[task_id] = TaskStatus(
            task_id=task_id,
            status="processing",
            progress=0.0,
            message="Starting lip-sync...",
            created_at=datetime.now()
        )
        
        # Process in background
        def process_lip_sync():
            try:
                tasks[task_id].progress = 0.2
                tasks[task_id].message = "Analyzing video and audio..."
                
                import asyncio
                output_path = asyncio.run(lip_sync_service.sync_lips(
                    video_path=video_path,
                    audio_path=audio_path
                ))
                
                tasks[task_id].status = "completed"
                tasks[task_id].progress = 1.0
                tasks[task_id].message = "Lip-sync completed"
                tasks[task_id].output_path = output_path
                tasks[task_id].updated_at = datetime.now()
                
            except Exception as e:
                tasks[task_id].status = "failed"
                tasks[task_id].message = str(e)
                tasks[task_id].updated_at = datetime.now()
                logger.error(f"Lip-sync failed: {e}")
        
        background_tasks.add_task(process_lip_sync)
        
        return ProcessingResponse(
            success=True,
            message="Lip-sync started",
            task_id=task_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in lip_sync_video: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/lipsync/image", response_model=ProcessingResponse)
async def lip_sync_image(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(..., description="Image file with face"),
    audio: UploadFile = File(..., description="Audio file to sync")
):
    """
    Create a talking head video from a single image and audio.
    
    The face in the image will be animated to match the audio (like a deepfake).
    """
    try:
        settings = get_settings()
        
        # Validate files
        allowed_image = ['image/jpeg', 'image/png', 'image/jpg', 'image/webp']
        allowed_audio = ['audio/wav', 'audio/x-wav', 'audio/mpeg', 'audio/mp3']
        
        if image.content_type not in allowed_image:
            raise HTTPException(status_code=400, detail=f"Invalid image format. Allowed: {allowed_image}")
        if audio.content_type not in allowed_audio:
            raise HTTPException(status_code=400, detail=f"Invalid audio format. Allowed: {allowed_audio}")
        
        # Save files
        image_filename = get_unique_filename(image.filename)
        audio_filename = get_unique_filename(audio.filename)
        image_path = os.path.join(settings.upload_dir, image_filename)
        audio_path = os.path.join(settings.upload_dir, audio_filename)
        
        with open(image_path, "wb") as f:
            f.write(await image.read())
        with open(audio_path, "wb") as f:
            f.write(await audio.read())
        
        # Create task
        task_id = str(uuid.uuid4())
        tasks[task_id] = TaskStatus(
            task_id=task_id,
            status="processing",
            progress=0.0,
            message="Starting talking head generation...",
            created_at=datetime.now()
        )
        
        # Process in background
        def process_talking_head():
            try:
                tasks[task_id].progress = 0.2
                tasks[task_id].message = "Creating animated video..."
                
                import asyncio
                output_path = asyncio.run(lip_sync_service.create_talking_head(
                    image_path=image_path,
                    audio_path=audio_path
                ))
                
                tasks[task_id].status = "completed"
                tasks[task_id].progress = 1.0
                tasks[task_id].message = "Talking head video created"
                tasks[task_id].output_path = output_path
                tasks[task_id].updated_at = datetime.now()
                
            except Exception as e:
                tasks[task_id].status = "failed"
                tasks[task_id].message = str(e)
                tasks[task_id].updated_at = datetime.now()
                logger.error(f"Talking head creation failed: {e}")
        
        background_tasks.add_task(process_talking_head)
        
        return ProcessingResponse(
            success=True,
            message="Talking head generation started",
            task_id=task_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in lip_sync_image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Full Pipeline Endpoint (Voice Clone + Lip Sync)
# =============================================================================

@app.post("/api/v1/generate/talking-head", response_model=ProcessingResponse)
async def generate_talking_head(
    background_tasks: BackgroundTasks,
    text: str = Form(..., description="Text to speak"),
    language: str = Form("en", description="Language code"),
    face_image: UploadFile = File(..., description="Image of the person"),
    voice_sample: UploadFile = File(..., description="Voice sample to clone")
):
    """
    Complete pipeline: Clone voice from sample, generate speech from text,
    and create a talking head video from the face image.
    
    This is the full deepfake experience - give a face image, a voice sample,
    and text, and get a video of that person saying that text with their voice.
    """
    try:
        settings = get_settings()
        
        # Validate files
        allowed_image = ['image/jpeg', 'image/png', 'image/jpg']
        allowed_audio = ['audio/wav', 'audio/x-wav', 'audio/mpeg', 'audio/mp3']
        
        if face_image.content_type not in allowed_image:
            raise HTTPException(status_code=400, detail=f"Invalid image format. Allowed: {allowed_image}")
        if voice_sample.content_type not in allowed_audio:
            raise HTTPException(status_code=400, detail=f"Invalid audio format. Allowed: {allowed_audio}")
        
        # Save files
        image_filename = get_unique_filename(face_image.filename)
        audio_filename = get_unique_filename(voice_sample.filename)
        image_path = os.path.join(settings.upload_dir, image_filename)
        voice_path = os.path.join(settings.upload_dir, audio_filename)
        
        with open(image_path, "wb") as f:
            f.write(await face_image.read())
        with open(voice_path, "wb") as f:
            f.write(await voice_sample.read())
        
        # Create task
        task_id = str(uuid.uuid4())
        tasks[task_id] = TaskStatus(
            task_id=task_id,
            status="processing",
            progress=0.0,
            message="Starting full pipeline...",
            created_at=datetime.now()
        )
        
        # Process in background
        def process_full_pipeline():
            try:
                # Step 1: Clone voice
                tasks[task_id].progress = 0.2
                tasks[task_id].message = "Cloning voice via API..."
                
                import asyncio
                cloned_audio_path = asyncio.run(voice_cloning_service.clone_and_speak(
                    text=text,
                    audio_path=voice_path,
                    voice_name=f"Cloned_{task_id[:8]}"
                ))
                
                # Step 2: Create talking head
                tasks[task_id].progress = 0.6
                tasks[task_id].message = "Generating talking head via API..."
                
                output_path = asyncio.run(lip_sync_service.create_talking_head(
                    image_path=image_path,
                    audio_path=cloned_audio_path
                ))
                
                tasks[task_id].status = "completed"
                tasks[task_id].progress = 1.0
                tasks[task_id].message = "Full pipeline completed - talking head generated"
                tasks[task_id].output_path = output_path
                tasks[task_id].updated_at = datetime.now()
                
            except Exception as e:
                tasks[task_id].status = "failed"
                tasks[task_id].message = str(e)
                tasks[task_id].updated_at = datetime.now()
                logger.error(f"Full pipeline failed: {e}")
        
        background_tasks.add_task(process_full_pipeline)
        
        return ProcessingResponse(
            success=True,
            message="Full pipeline started (voice clone + talking head)",
            task_id=task_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_talking_head: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Task Status & Download Endpoints
# =============================================================================

@app.get("/api/v1/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """Get the status of a processing task"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]


@app.get("/api/v1/download/{task_id}")
async def download_result(task_id: str):
    """Download the result file for a completed task"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    if task.status != "completed":
        raise HTTPException(status_code=400, detail="Task not yet completed")
    
    if not task.output_path or not os.path.exists(task.output_path):
        raise HTTPException(status_code=404, detail="Output file not found")
    
    return FileResponse(
        task.output_path,
        media_type='application/octet-stream',
        filename=os.path.basename(task.output_path)
    )


@app.get("/api/v1/tasks")
async def list_tasks():
    """List all tasks (for debugging/monitoring)"""
    return {
        "tasks": [
            {
                "task_id": t.task_id,
                "status": t.status,
                "progress": t.progress,
                "message": t.message,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None
            }
            for t in tasks.values()
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
