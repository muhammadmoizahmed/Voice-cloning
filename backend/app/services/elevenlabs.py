"""
ElevenLabs API Integration for Voice Cloning
"""
import os
import httpx
import logging
from typing import Optional
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ElevenLabsService:
    """Voice cloning and TTS using ElevenLabs API"""
    
    def __init__(self):
        self.api_key = settings.elevenlabs_api_key
        self.base_url = "https://api.elevenlabs.io/v1"
        
        if not self.api_key:
            logger.warning("ElevenLabs API key not configured!")
    
    def _get_headers(self):
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
    
    async def clone_voice(self, name: str, audio_path: str, description: str = "") -> Optional[str]:
        """Clone a voice from audio file"""
        try:
            if not self.api_key:
                raise ValueError("ElevenLabs API key not configured")
            
            url = f"{self.base_url}/voices/add"
            
            with open(audio_path, "rb") as f:
                files = {"files": (os.path.basename(audio_path), f, "audio/mpeg")}
                data = {
                    "name": name,
                    "description": description or f"Voice: {name}"
                }
                headers = {"xi-api-key": self.api_key}
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        url, 
                        files=files, 
                        data=data, 
                        headers=headers,
                        timeout=60.0
                    )
                    response.raise_for_status()
            
            result = response.json()
            voice_id = result.get("voice_id")
            logger.info(f"Voice cloned successfully: {voice_id}")
            return voice_id
            
        except Exception as e:
            logger.error(f"Voice cloning failed: {e}")
            # Try to get more details from httpx error
            if hasattr(e, 'response'):
                try:
                    logger.error(f"Response status: {e.response.status_code}")
                    logger.error(f"Response body: {e.response.text}")
                except:
                    pass
            return None
    
    async def text_to_speech(
        self, 
        text: str, 
        voice_id: str,
        output_path: str,
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        model_id: str = "eleven_multilingual_v2"
    ) -> bool:
        """Generate speech from text"""
        try:
            if not self.api_key:
                raise ValueError("ElevenLabs API key not configured")
            
            url = f"{self.base_url}/text-to-speech/{voice_id}"
            
            payload = {
                "text": text,
                "model_id": model_id,
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost
                }
            }
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=120.0
                )
                response.raise_for_status()
            
            # Save audio
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            logger.info(f"TTS generated: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            return False
    
    async def delete_voice(self, voice_id: str) -> bool:
        """Delete a voice from ElevenLabs"""
        try:
            url = f"{self.base_url}/voices/{voice_id}"
            headers = {"xi-api-key": self.api_key}
            
            async with httpx.AsyncClient() as client:
                response = await client.delete(url, headers=headers)
                response.raise_for_status()
            
            return True
            
        except Exception as e:
            logger.error(f"Voice deletion failed: {e}")
            return False
    
    async def list_voices(self) -> list:
        """List all available voices"""
        try:
            url = f"{self.base_url}/voices"
            headers = {"xi-api-key": self.api_key}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
            
            return response.json().get("voices", [])
            
        except Exception as e:
            logger.error(f"List voices failed: {e}")
            return []


# Singleton
elevenlabs_service = ElevenLabsService()
