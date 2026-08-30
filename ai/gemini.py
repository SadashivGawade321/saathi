"""
SAATHI ONE — Gemini AI Agent
Wraps Google Gemini with function calling, dynamic system prompts,
conversation history, and multilingual support.
"""

import json
from datetime import datetime, timezone
from bson import ObjectId
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL, FALLBACK_MODELS, SUPPORTED_LANGUAGES
from database import (
    businesses_col,
    services_col,
    resources_col,
    ai_employees_col,
    calls_col,
    conversations_col,
    tool_executions_col,
)
from models import new_call, new_conversation_message, new_tool_execution, new_ai_employee
from ai.prompts import build_system_prompt
from ai.tools import TOOL_DECLARATIONS, TOOL_FUNCTIONS

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


class GeminiAgent:
    """
    Tenant-specific AI agent powered by Gemini with function calling.
    Each instance is bound to a single business.
    """

    def __init__(self, business_id: str):
        self.business_id = business_id
        self.business = None
        self.ai_employee = None
        self.services = []
        self.resources = []
        self.chat = None
        self.call_id = None
        self.activity_log = []  # Live AI activity for UI display
        self.detected_language = "en"
        self.language_confidence = 0.0

        self._load_tenant_context()
        self._init_gemini()

    # ------------------------------------------------------------------
    # Load tenant context
    # ------------------------------------------------------------------
    def _load_tenant_context(self):
        """Load all business data for this tenant."""
        self._log_activity("Loading tenant context...")

        self.business = businesses_col().find_one({"_id": ObjectId(self.business_id)})
        if not self.business:
            raise ValueError(f"Business not found: {self.business_id}")
        self._log_activity(f"Business loaded: {self.business['name']}")

        self.ai_employee = ai_employees_col().find_one({"business_id": self.business_id})
        if not self.ai_employee:
            # Create default AI employee
            emp = new_ai_employee(self.business_id)
            result = ai_employees_col().insert_one(emp)
            emp["_id"] = result.inserted_id
            self.ai_employee = emp
        self._log_activity(f"AI Employee: {self.ai_employee['name']}")

        self.services = list(services_col().find({
            "business_id": self.business_id,
            "active": True,
        }))
        self._log_activity(f"Services loaded: {len(self.services)}")

        self.resources = list(resources_col().find({
            "business_id": self.business_id,
            "active": True,
        }))
        self._log_activity(f"Resources loaded: {len(self.resources)}")

    # ------------------------------------------------------------------
    # Initialize Gemini
    # ------------------------------------------------------------------
    def _init_gemini(self, model_name: str | None = None):
        """Initialize Gemini model with system prompt and tools."""
        self.current_model = model_name or GEMINI_MODEL
        system_prompt = build_system_prompt(
            business=self.business,
            services=self.services,
            resources=self.resources,
            ai_employee=self.ai_employee,
        )

        # Add current date context
        today = datetime.now(timezone.utc).strftime("%A, %B %d, %Y")
        system_prompt += f"\n\nTODAY'S DATE: {today}\n"

        # Create tool objects for Gemini
        tools = []
        for decl in TOOL_DECLARATIONS:
            tools.append(genai.protos.Tool(
                function_declarations=[
                    genai.protos.FunctionDeclaration(
                        name=decl["name"],
                        description=decl["description"],
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                k: genai.protos.Schema(
                                    type=self._map_type(v.get("type", "string")),
                                    description=v.get("description", ""),
                                )
                                for k, v in decl.get("parameters", {}).get("properties", {}).items()
                            },
                            required=decl.get("parameters", {}).get("required", []),
                        ),
                    )
                ]
            ))

        model = genai.GenerativeModel(
            model_name=self.current_model,
            system_instruction=system_prompt,
            tools=tools,
        )

        # Preserve previous chat history if rotating models
        old_history = self.chat.history if hasattr(self, "chat") and self.chat else []
        self.chat = model.start_chat(history=old_history)
        self._log_activity(f"AI initialized with model: {self.current_model}")

    def _map_type(self, type_str: str):
        """Map JSON schema type to Gemini protobuf type."""
        mapping = {
            "string": genai.protos.Type.STRING,
            "integer": genai.protos.Type.INTEGER,
            "number": genai.protos.Type.NUMBER,
            "boolean": genai.protos.Type.BOOLEAN,
            "object": genai.protos.Type.OBJECT,
            "array": genai.protos.Type.ARRAY,
        }
        return mapping.get(type_str, genai.protos.Type.STRING)

    # ------------------------------------------------------------------
    # Start / End Call
    # ------------------------------------------------------------------
    def start_call(self) -> str:
        """Start a new call session. Returns call_id."""
        call = new_call(self.business_id)
        result = calls_col().insert_one(call)
        self.call_id = str(result.inserted_id)
        self._log_activity("Call started")
        self._log_activity(f"Tenant identified: {self.business['name']}")
        return self.call_id

    def end_call(self, outcome: str = "completed"):
        """End the current call."""
        if self.call_id:
            calls_col().update_one(
                {"_id": ObjectId(self.call_id)},
                {
                    "$set": {
                        "ended_at": datetime.now(timezone.utc),
                        "outcome": outcome,
                        "language": self.detected_language,
                    }
                },
            )
            self._log_activity("Call ended")

    def _send_with_retry(self, content, max_retries: int = 4):
        """Send message to Gemini chat with automatic backoff retry and model fallback on 429 rate limit."""
        import time
        models_to_try = [self.current_model] + [m for m in FALLBACK_MODELS if m != self.current_model]

        for model_idx, model_name in enumerate(models_to_try):
            if model_name != self.current_model:
                try:
                    self._log_activity(f"Switching to fallback model: {model_name}...")
                    self._init_gemini(model_name)
                except Exception:
                    continue

            for attempt in range(max_retries):
                try:
                    return self.chat.send_message(content)
                except Exception as e:
                    err_str = str(e)
                    is_quota = "429" in err_str or "ResourceExhausted" in err_str or "quota" in err_str.lower()
                    if is_quota:
                        # Extract seconds if provided in error message
                        import re
                        delay_match = re.search(r"retry in (\d+(?:\.\d+)?)s", err_str) or re.search(r"seconds:\s*(\d+)", err_str)
                        if delay_match:
                            sleep_time = min(float(delay_match.group(1)) + 1, 8.0)
                        else:
                            sleep_time = (attempt + 1) * 3

                        if attempt < max_retries - 1:
                            self._log_activity(f"Rate limit hit, waiting {sleep_time:.1f}s...")
                            time.sleep(sleep_time)
                            continue
                        else:
                            # Try next model in fallback list
                            break
                    else:
                        raise e

        # If all retries and fallbacks fail, raise last error
        raise RuntimeError("All Gemini models currently rate limited. Please retry in a few seconds.")

    # ------------------------------------------------------------------
    # Process message — the main conversation loop
    # ------------------------------------------------------------------
    def process_message(self, user_message: str) -> dict:
        """
        Process a user message through Gemini with function calling.
        Returns {"response": str, "language": str, "tool_calls": list, "activity": list}
        """
        step_activity = []

        # Detect language
        lang, confidence = self._detect_language(user_message)
        self.detected_language = lang
        self.language_confidence = confidence
        lang_name = SUPPORTED_LANGUAGES.get(lang, lang)
        self._log_activity(f"Language detected: {lang_name} ({confidence:.0%})")
        step_activity.append(f"Language detected: {lang_name}")

        # Save customer message
        self._save_message("user", user_message, lang, confidence)

        # Send to Gemini
        self._log_activity("Processing with Gemini...")
        response = self._send_with_retry(user_message)

        # Handle function calls (tool use loop)
        tool_calls_made = []
        max_iterations = 5
        iteration = 0

        while response.candidates[0].content.parts and iteration < max_iterations:
            iteration += 1
            has_function_call = False

            for part in response.candidates[0].content.parts:
                if part.function_call:
                    has_function_call = True
                    fn_name = part.function_call.name
                    fn_args = dict(part.function_call.args) if part.function_call.args else {}

                    self._log_activity(f"Tool called: {fn_name}")
                    step_activity.append(f"Tool: {fn_name}")

                    # Execute the tool
                    fn_args["business_id"] = self.business_id
                    tool_fn = TOOL_FUNCTIONS.get(fn_name)

                    if tool_fn:
                        try:
                            result = tool_fn(**fn_args)
                            success = "error" not in result
                            self._log_activity(
                                f"Tool result: {'Success' if success else 'Failed'}"
                            )
                        except Exception as e:
                            result = {"error": str(e)}
                            success = False
                            self._log_activity(f"Tool error: {e}")
                    else:
                        result = {"error": f"Unknown tool: {fn_name}"}
                        success = False

                    # Log tool execution
                    self._log_tool_execution(fn_name, fn_args, result, success)
                    tool_calls_made.append({
                        "tool": fn_name,
                        "args": {k: v for k, v in fn_args.items() if k != "business_id"},
                        "result": result,
                        "success": success,
                    })

                    # Detect specific intents from tool calls
                    if fn_name == "check_availability":
                        step_activity.append("Availability checked")
                        if result.get("available"):
                            step_activity.append("Slot found")
                    elif fn_name == "create_booking" and result.get("success"):
                        step_activity.append("Appointment created")
                        step_activity.append("MongoDB updated")
                        # Update call with booking reference
                        if self.call_id:
                            calls_col().update_one(
                                {"_id": ObjectId(self.call_id)},
                                {
                                    "$set": {
                                        "booking_id": result.get("booking_id"),
                                        "intent": "booking",
                                    }
                                },
                            )
                    elif fn_name == "cancel_booking" and result.get("success"):
                        step_activity.append("Booking cancelled")
                    elif fn_name == "reschedule_booking" and result.get("success"):
                        step_activity.append("Booking rescheduled")

                    # Send tool result back to Gemini
                    response = self._send_with_retry(
                        genai.protos.Content(
                            parts=[
                                genai.protos.Part(
                                    function_response=genai.protos.FunctionResponse(
                                        name=fn_name,
                                        response={"result": json.dumps(result, default=str)},
                                    )
                                )
                            ]
                        )
                    )
                    break  # Process one function call at a time

            if not has_function_call:
                break

        # Extract text response
        ai_response = ""
        for part in response.candidates[0].content.parts:
            if part.text:
                ai_response += part.text

        # Save AI response
        self._save_message("assistant", ai_response, self.detected_language)
        self._log_activity("Response generated")

        return {
            "response": ai_response,
            "language": self.detected_language,
            "language_name": SUPPORTED_LANGUAGES.get(self.detected_language, self.detected_language),
            "language_confidence": self.language_confidence,
            "tool_calls": tool_calls_made,
            "activity": step_activity,
        }

    # ------------------------------------------------------------------
    # Language detection
    # ------------------------------------------------------------------
    def _detect_language(self, text: str) -> tuple[str, float]:
        """Detect language of input text. Returns (lang_code, confidence)."""
        try:
            from langdetect import detect_langs
            results = detect_langs(text)
            if results:
                lang = results[0].lang
                confidence = results[0].prob

                # Map langdetect codes to our codes
                lang_map = {
                    "en": "en",
                    "hi": "hi",
                    "mr": "mr",
                    "mar": "mr",
                }
                mapped = lang_map.get(lang, "en")

                # For mixed/Hinglish text, langdetect might return unexpected results
                # If confidence is low, check for Hindi/Marathi indicators
                if confidence < 0.7:
                    mapped = self._fallback_language_detect(text)
                    confidence = 0.6

                return mapped, confidence
        except Exception:
            pass

        # Fallback
        return self._fallback_language_detect(text), 0.5

    def _fallback_language_detect(self, text: str) -> str:
        """Simple heuristic-based language detection for mixed text."""
        # Check for Devanagari script (Hindi/Marathi)
        devanagari_count = sum(1 for c in text if '\u0900' <= c <= '\u097F')
        total_alpha = sum(1 for c in text if c.isalpha())

        if total_alpha == 0:
            return "en"

        if devanagari_count > total_alpha * 0.3:
            # Marathi-specific characters / words
            marathi_indicators = ["ळ", "आहे", "नाही", "हवे", "हवी", "करा", "उद्या", "मला", "तुम्ही", "आम्ही"]
            if any(indicator in text for indicator in marathi_indicators):
                return "mr"
            return "hi"

        # Check for romanized Hindi/Hinglish words
        hindi_words = [
            "kya", "hai", "mujhe", "chahiye", "kal", "aaj", "baje",
            "haan", "nahi", "karo", "karna", "appointment", "kitne",
            "kab", "kaun", "kaise", "accha", "theek", "bilkul",
            "namaste", "shukriya", "dhanyavaad",
        ]
        words = text.lower().split()
        hindi_count = sum(1 for w in words if w in hindi_words)
        if hindi_count >= 2 or (hindi_count >= 1 and len(words) <= 4):
            return "hi"

        return "en"

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _save_message(self, role: str, content: str, language: str = "", confidence: float = 0.0):
        """Save a conversation message to MongoDB."""
        if self.call_id:
            msg = new_conversation_message(
                call_id=self.call_id,
                business_id=self.business_id,
                role=role,
                content=content,
                language=language,
                language_confidence=confidence,
            )
            conversations_col().insert_one(msg)

            # Also append to call transcript
            calls_col().update_one(
                {"_id": ObjectId(self.call_id)},
                {"$push": {"transcript": {"role": role, "content": content, "language": language}}},
            )

    def _log_tool_execution(self, tool_name: str, tool_input: dict, result: dict, success: bool):
        """Log a tool execution to MongoDB."""
        doc = new_tool_execution(
            business_id=self.business_id,
            conversation_id=self.call_id or "",
            tool_name=tool_name,
            tool_input={k: v for k, v in tool_input.items() if k != "business_id"},
            result=result,
            success=success,
        )
        tool_executions_col().insert_one(doc)

    def _log_activity(self, message: str):
        """Add to live activity log."""
        self.activity_log.append({
            "message": message,
            "timestamp": datetime.now(timezone.utc),
        })
