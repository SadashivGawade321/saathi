"""
SAATHI ONE — Speech-to-Text
Abstraction layer for speech recognition with multilingual support.
"""

import io
import speech_recognition as sr
from config import LANGUAGE_CODES_STT


class SpeechToText:
    """Base STT abstraction."""

    def transcribe(self, audio_data) -> dict:
        """Transcribe audio to text. Returns {"text": str, "language": str, "success": bool}."""
        raise NotImplementedError


class GoogleSpeechToText(SpeechToText):
    """Google Web Speech API via SpeechRecognition library."""

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 1.0

    def transcribe_from_mic(self, language: str = "hi-IN", timeout: int = 10) -> dict:
        """Record from microphone and transcribe."""
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=15)
                return self._recognize(audio, language)
        except sr.WaitTimeoutError:
            return {"text": "", "success": False, "error": "No speech detected. Please try again."}
        except Exception as e:
            return {"text": "", "success": False, "error": str(e)}

    def transcribe_from_audio_data(self, audio_bytes: bytes, language: str = "hi-IN") -> dict:
        """Transcribe from raw audio bytes (WAV format)."""
        try:
            audio = sr.AudioData(audio_bytes, sample_rate=16000, sample_width=2)
            return self._recognize(audio, language)
        except Exception as e:
            return {"text": "", "success": False, "error": str(e)}

    def transcribe_from_wav(self, wav_path: str, language: str = "hi-IN") -> dict:
        """Transcribe from a WAV file."""
        try:
            with sr.AudioFile(wav_path) as source:
                audio = self.recognizer.record(source)
                return self._recognize(audio, language)
        except Exception as e:
            return {"text": "", "success": False, "error": str(e)}

    def _recognize(self, audio, language: str) -> dict:
        """Run Google speech recognition with multilingual fallback."""
        # Try the specified language first
        try:
            text = self.recognizer.recognize_google(audio, language=language)
            return {"text": text, "language": language, "success": True}
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            return {"text": "", "success": False, "error": f"Google API error: {e}"}

        # Fallback: try all supported languages
        for lang_code, stt_code in LANGUAGE_CODES_STT.items():
            if stt_code == language:
                continue  # Already tried
            try:
                text = self.recognizer.recognize_google(audio, language=stt_code)
                return {"text": text, "language": stt_code, "success": True}
            except (sr.UnknownValueError, sr.RequestError):
                continue

        return {"text": "", "success": False, "error": "Could not understand audio in any supported language."}


# Singleton
stt_engine = GoogleSpeechToText()
