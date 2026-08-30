"""
SAATHI ONE — Text-to-Speech
Abstraction layer for TTS with multilingual support (Hindi, Marathi, English).
"""

import os
import tempfile
from config import LANGUAGE_CODES_TTS


class TextToSpeech:
    """Base TTS abstraction."""

    def speak(self, text: str, language: str = "en") -> str | None:
        """Convert text to speech. Returns path to audio file or None."""
        raise NotImplementedError


class GoogleTTS(TextToSpeech):
    """Google Text-to-Speech via gTTS — supports Hindi, Marathi, English."""

    def speak(self, text: str, language: str = "en") -> str | None:
        """Generate speech audio file. Returns path to MP3."""
        try:
            from gtts import gTTS

            # Map language code
            tts_lang = LANGUAGE_CODES_TTS.get(language, "en")

            # Generate audio
            tts = gTTS(text=text, lang=tts_lang, slow=False)

            # Save to temp file
            temp_dir = os.path.join(tempfile.gettempdir(), "saathi_one_audio")
            os.makedirs(temp_dir, exist_ok=True)
            filepath = os.path.join(temp_dir, f"response_{id(text) % 100000}.mp3")
            tts.save(filepath)

            return filepath
        except Exception as e:
            print(f"gTTS error: {e}")
            return self._fallback_speak(text, language)

    def _fallback_speak(self, text: str, language: str) -> str | None:
        """Fallback to pyttsx3 for offline TTS (English only)."""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", 150)

            temp_dir = os.path.join(tempfile.gettempdir(), "saathi_one_audio")
            os.makedirs(temp_dir, exist_ok=True)
            filepath = os.path.join(temp_dir, f"response_fallback_{id(text) % 100000}.wav")
            engine.save_to_file(text, filepath)
            engine.runAndWait()
            return filepath
        except Exception as e:
            print(f"pyttsx3 fallback error: {e}")
            return None

    def speak_to_bytes(self, text: str, language: str = "en") -> bytes | None:
        """Generate speech and return raw audio bytes."""
        try:
            from gtts import gTTS
            import io

            tts_lang = LANGUAGE_CODES_TTS.get(language, "en")
            tts = gTTS(text=text, lang=tts_lang, slow=False)

            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            return audio_buffer.read()
        except Exception as e:
            print(f"gTTS bytes error: {e}")
            return None


# Singleton
tts_engine = GoogleTTS()
