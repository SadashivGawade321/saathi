"""
SAATHI ONE — Live Call Loop Engine
Handles the continuous speak-listen-respond cycle of a real voice call.
Uses Groq LLaMA for instant responses.
"""

import time
import threading
import speech_recognition as sr


class LiveCallLoop:
    """
    Real-time voice call loop.
    Runs: AI Greet → Listen → STT → Gemini → TTS → Listen → ...
    Communicates state and messages to the Streamlit UI via shared state dicts.
    """

    def __init__(self, agent, state: dict, stop_event: threading.Event):
        self.agent = agent          # GeminiAgent instance
        self.state = state          # Shared mutable dict (UI reads this)
        self.stop_event = stop_event
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 1.2  # slightly longer pause → full sentence

    # ─── Public entry point ────────────────────────────────────────────────────
    def run(self):
        """Start the continuous call loop (runs in background thread)."""
        self.state["call_status"] = "greeting"
        self.state["call_messages"] = []
        self.state["last_audio_bytes"] = None

        # AI greets the caller
        greeting = self._ai_greet()
        self._speak(greeting, self.agent.detected_language or "hi")

        # Main loop: listen → respond → speak → repeat
        while not self.stop_event.is_set():
            self.state["call_status"] = "listening"
            stt_result = self._listen()

            if self.stop_event.is_set():
                break

            if not stt_result.get("success") or not stt_result.get("text", "").strip():
                # Silence or failed — nudge once and re-listen
                nudge = "Kya aap wahan hain? Please baat karo."
                self._push_message("system", nudge)
                self._speak(nudge, "hi")
                continue

            user_text = stt_result["text"].strip()
            self._push_message("user", user_text, stt_result.get("language", "hi"))

            self.state["call_status"] = "thinking"
            try:
                result = self.agent.process_message(user_text)
            except Exception as e:
                err_resp = "Maafi chahta hoon, mujhe ek technical problem aa gayi. Kripya dobara puchiye."
                self._push_message("assistant", err_resp)
                self._speak(err_resp, "hi")
                continue

            ai_response = result["response"]
            lang = result.get("language", "hi")
            self._push_message("assistant", ai_response, lang)
            self.state["activity"] = list(self.agent.activity_log)
            self.state["tool_calls"] = result.get("tool_calls", [])

            self.state["call_status"] = "speaking"
            self._speak(ai_response, lang)

        self.state["call_status"] = "ended"

    # ─── Private helpers ────────────────────────────────────────────────────────
    def _ai_greet(self) -> str:
        """Generate an opening greeting using the AI agent."""
        ai_name = self.agent.ai_employee.get("name", "Maya") if self.agent.ai_employee else "Maya"
        biz_name = self.agent.business.get("name", "hamare business") if self.agent.business else "hamare business"
        greeting_prompt = (
            f"Please greet the caller warmly. Say hello and introduce yourself as {ai_name}, "
            f"the AI receptionist of {biz_name}. Ask how you can help today. "
            "Reply in Hindi/Hinglish (3-4 sentences max). Be warm and professional."
        )
        try:
            result = self.agent.process_message(greeting_prompt)
            return result["response"]
        except Exception:
            return f"Namaste! Main {ai_name} hoon, {biz_name} ki AI receptionist. Aaj main aapki kya sahayata kar sakti hoon?"

    def _listen(self) -> dict:
        """Open microphone and listen for user speech. Tries auto-detect language."""
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.4)
                audio = self.recognizer.listen(source, timeout=12, phrase_time_limit=20)

            # Try in order: hi-IN, mr-IN, en-IN
            for lang_code in ["hi-IN", "mr-IN", "en-IN"]:
                if self.stop_event.is_set():
                    return {"text": "", "success": False}
                try:
                    text = self.recognizer.recognize_google(audio, language=lang_code)
                    # map STT code to internal lang code
                    lang_map = {"hi-IN": "hi", "mr-IN": "mr", "en-IN": "en"}
                    return {"text": text, "language": lang_map[lang_code], "success": True}
                except sr.UnknownValueError:
                    continue
                except sr.RequestError:
                    break

            return {"text": "", "success": False}

        except sr.WaitTimeoutError:
            return {"text": "", "success": False, "error": "timeout"}
        except Exception as e:
            return {"text": "", "success": False, "error": str(e)}

    def _speak(self, text: str, language: str = "hi"):
        """Generate TTS audio bytes and store in shared state for UI playback."""
        if not text.strip():
            return
        try:
            from voice.text_to_speech import tts_engine
            audio_bytes = tts_engine.speak_to_bytes(text, language)
            if audio_bytes:
                self.state["last_audio_bytes"] = audio_bytes
                # Block until TTS should have finished playing (approx 100 chars/sec voice)
                approx_seconds = max(2.5, len(text) / 15)
                deadline = time.time() + approx_seconds
                while time.time() < deadline and not self.stop_event.is_set():
                    time.sleep(0.1)
        except Exception as e:
            print(f"[TTS error] {e}")

    def _push_message(self, role: str, content: str, language: str = ""):
        msgs = self.state.get("call_messages", [])
        msgs.append({"role": role, "content": content, "language": language})
        self.state["call_messages"] = msgs


# ─── Module-level call state registry (one per business session) ──────────────
_active_loops: dict[str, "LiveCallLoop"] = {}
_active_threads: dict[str, threading.Thread] = {}
_stop_events: dict[str, threading.Event] = {}


def start_live_call(agent, biz_key: str) -> dict:
    """Start a live call loop for a business. Returns shared state dict."""
    # Stop any existing call
    stop_live_call(biz_key)

    state = {
        "call_status": "starting",
        "call_messages": [],
        "last_audio_bytes": None,
        "activity": [],
        "tool_calls": [],
    }
    stop_event = threading.Event()
    loop = LiveCallLoop(agent, state, stop_event)

    t = threading.Thread(target=loop.run, daemon=True)
    _active_loops[biz_key] = loop
    _active_threads[biz_key] = t
    _stop_events[biz_key] = stop_event
    t.start()
    return state


def stop_live_call(biz_key: str):
    """Signal the live call loop to stop."""
    if biz_key in _stop_events:
        _stop_events[biz_key].set()
    if biz_key in _active_loops:
        del _active_loops[biz_key]
    if biz_key in _active_threads:
        del _active_threads[biz_key]
    if biz_key in _stop_events:
        del _stop_events[biz_key]


def is_call_active(biz_key: str) -> bool:
    """Check if a live call loop is running."""
    t = _active_threads.get(biz_key)
    return t is not None and t.is_alive()


def get_call_state(biz_key: str) -> dict | None:
    """Get shared state dict for active call."""
    loop = _active_loops.get(biz_key)
    return loop.state if loop else None
