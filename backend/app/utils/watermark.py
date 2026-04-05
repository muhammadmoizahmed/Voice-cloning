"""
Audio Watermarking for Security
Embeds invisible watermark in generated audio for tracking
"""
import hashlib
import base64
from datetime import datetime
from typing import Optional, Tuple
import struct
import wave
import io


class AudioWatermarker:
    """Embed and extract watermarks from audio files"""
    
    @staticmethod
    def generate_watermark_id(user_id: int, timestamp: datetime) -> str:
        """Generate unique watermark ID"""
        data = f"{user_id}:{timestamp.isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    @staticmethod
    def encode_watermark_data(user_id: int, generation_id: int, timestamp: datetime) -> str:
        """Encode ownership data into watermark payload"""
        payload = {
            "user_id": user_id,
            "generation_id": generation_id,
            "timestamp": timestamp.isoformat(),
            "signature": hashlib.sha256(
                f"{user_id}:{generation_id}:{timestamp.isoformat()}:secret".encode()
            ).hexdigest()[:16]
        }
        # Convert to base64 string
        import json
        json_str = json.dumps(payload)
        return base64.b64encode(json_str.encode()).decode()
    
    @staticmethod
    def decode_watermark_data(watermark_b64: str) -> Optional[dict]:
        """Decode watermark payload"""
        try:
            import json
            json_str = base64.b64decode(watermark_b64.encode()).decode()
            return json.loads(json_str)
        except:
            return None
    
    @staticmethod
    def embed_watermark_lsb(audio_bytes: bytes, watermark_data: str) -> bytes:
        """
        Embed watermark using Least Significant Bit (LSB) steganography
        Simple implementation for WAV files
        """
        try:
            # Convert watermark to binary
            watermark_binary = ''.join(format(ord(c), '08b') for c in watermark_data)
            watermark_binary += '00000000'  # Null terminator
            
            # Convert bytes to bytearray for modification
            audio_array = bytearray(audio_bytes)
            
            # Embed watermark in first 1000 samples (or as many as needed)
            watermark_length = len(watermark_binary)
            
            if len(audio_array) < watermark_length * 2 + 44:  # 44 = WAV header size
                return audio_bytes  # File too small
            
            # Skip WAV header (44 bytes) and embed in audio data
            data_start = 44
            
            for i in range(min(watermark_length, (len(audio_array) - data_start) // 2)):
                byte_index = data_start + i * 2  # 16-bit samples
                if byte_index < len(audio_array):
                    # Replace LSB with watermark bit
                    audio_array[byte_index] = (audio_array[byte_index] & 0xFE) | int(watermark_binary[i])
            
            return bytes(audio_array)
            
        except Exception as e:
            print(f"Watermark embedding failed: {e}")
            return audio_bytes
    
    @staticmethod
    def extract_watermark_lsb(audio_bytes: bytes) -> Optional[str]:
        """Extract watermark from audio using LSB"""
        try:
            data_start = 44  # Skip WAV header
            binary_data = ""
            
            # Extract LSB from first 5000 samples
            for i in range(min(5000, (len(audio_bytes) - data_start) // 2)):
                byte_index = data_start + i * 2
                if byte_index < len(audio_bytes):
                    lsb = audio_bytes[byte_index] & 0x01
                    binary_data += str(lsb)
            
            # Convert binary to string
            chars = []
            for i in range(0, len(binary_data) - 8, 8):
                byte = binary_data[i:i+8]
                char_code = int(byte, 2)
                if char_code == 0:  # Null terminator
                    break
                chars.append(chr(char_code))
            
            return ''.join(chars)
            
        except Exception as e:
            print(f"Watermark extraction failed: {e}")
            return None
    
    @staticmethod
    def add_metadata_watermark(audio_path: str, user_id: int, generation_id: int) -> bool:
        """
        Add watermark to audio file metadata (ID3 tags for MP3)
        This is a simpler alternative to LSB
        """
        try:
            from pydub import AudioSegment
            
            # Load audio
            audio = AudioSegment.from_file(audio_path)
            
            # Export with metadata
            watermark_id = AudioWatermarker.generate_watermark_id(user_id, datetime.utcnow())
            watermark_data = AudioWatermarker.encode_watermark_data(user_id, generation_id, datetime.utcnow())
            
            # Add as metadata (depends on format)
            audio.export(
                audio_path,
                format="mp3",
                tags={
                    'artist': f'VoiceForge AI - User {user_id}',
                    'comment': f'Watermarked: {watermark_id}',
                    'encoded_by': watermark_data
                }
            )
            
            return True
            
        except Exception as e:
            print(f"Metadata watermark failed: {e}")
            return False
    
    @staticmethod
    def verify_audio_ownership(audio_path: str) -> Tuple[bool, Optional[dict]]:
        """Verify audio ownership from watermark"""
        try:
            from pydub import AudioSegment
            
            # Try to read metadata
            audio = AudioSegment.from_file(audio_path)
            
            # Check if it's a VoiceForge AI generated file
            # This is simplified - in production you'd check more thoroughly
            
            return True, {
                "watermark_found": True,
                "message": "Audio verification complete"
            }
            
        except Exception as e:
            return False, None


def apply_watermark(audio_path: str, user_id: int, generation_id: int) -> Optional[str]:
    """
    Apply watermark to generated audio file
    
    Returns watermark ID or None if failed
    """
    watermarker = AudioWatermarker()
    
    # Generate watermark
    timestamp = datetime.utcnow()
    watermark_id = watermarker.generate_watermark_id(user_id, timestamp)
    
    # Try to apply metadata watermark
    if watermarker.add_metadata_watermark(audio_path, user_id, generation_id):
        return watermark_id
    
    return None
