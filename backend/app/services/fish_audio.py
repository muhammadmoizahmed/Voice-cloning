"""
Fish.Audio API Integration for Voice Cloning
"""
import os
import httpx
import logging
from typing import Optional
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class FishAudioService:
    """Voice cloning and TTS using Fish.Audio API"""
    
    def __init__(self):
        self.api_key = settings.fish_audio_api_key
        self.base_url = "https://api.fish.audio"
        
        if not self.api_key:
            logger.warning("Fish.Audio API key not configured!")
    
    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
    
    async def clone_voice(self, name: str, audio_path: str, description: str = "") -> Optional[str]:
        """Clone a voice from audio file using Fish.Audio"""
        try:
            if not self.api_key:
                raise ValueError("Fish.Audio API key not configured")
            
            url = f"{self.base_url}/v1/voices"
            
            with open(audio_path, "rb") as f:
                files = {"file": (os.path.basename(audio_path), f, "audio/mpeg")}
                data = {
                    "name": name,
                    "description": description or f"Voice: {name}"
                }
                headers = {"Authorization": f"Bearer {self.api_key}"}
                
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
            voice_id = result.get("id")
            logger.info(f"Voice cloned successfully with Fish.Audio: {voice_id}")
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
        language: str = "en",
        latency: str = "normal"
    ) -> bool:
        """Generate speech from text using Fish.Audio"""
        try:
            if not self.api_key:
                raise ValueError("Fish.Audio API key not configured")
            
            url = f"{self.base_url}/v1/tts"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "text": text,
                "reference_id": voice_id,
                "latency": latency
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
            
            logger.info(f"TTS generated with Fish.Audio: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            return False
    
    async def delete_voice(self, voice_id: str) -> bool:
        """Delete a voice from Fish.Audio"""
        try:
            url = f"{self.base_url}/v1/voices/{voice_id}"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
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
            url = f"{self.base_url}/v1/voices"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
            
            return response.json().get("items", [])
            
        except Exception as e:
            logger.error(f"List voices failed: {e}")
            return []


# Singleton
fish_audio_service = FishAudioService()
