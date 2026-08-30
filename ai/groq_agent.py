"""
SAATHI ONE — Groq AI Agent
Ultra-fast LLaMA-based AI receptionist with OpenAI-compatible tool calling.
Primary engine replacing Gemini for zero-quota, instant responses.
"""

import json
from datetime import datetime, timezone
from bson import ObjectId

from config import GROQ_API_KEY, GROQ_MODEL, GROQ_FALLBACK_MODEL, SUPPORTED_LANGUAGES
from database import (
    businesses_col, services_col, resources_col,
    ai_employees_col, calls_col, conversations_col, tool_executions_col,
)
from models import new_call, new_conversation_message, new_tool_execution, new_ai_employee
from ai.prompts import build_system_prompt
from ai.tools import TOOL_DECLARATIONS, TOOL_FUNCTIONS


# ─── Convert SAATHI tool declarations → Groq/OpenAI tool format ──────────────
def _to_groq_tools(declarations: list) -> list:
    tools = []
    for decl in declarations:
        tools.append({
            "type": "function",
            "function": {
                "name": decl["name"],
                "description": decl["description"],
                "parameters": {
                    "type": "object",
                    "properties": {
                        k: {"type": v.get("type", "string"), "description": v.get("description", "")}
                        for k, v in decl.get("parameters", {}).get("properties", {}).items()
                    },
                    "required": decl.get("parameters", {}).get("required", []),
                },
            },
        })
    return tools


GROQ_TOOLS = _to_groq_tools(TOOL_DECLARATIONS)


def _strip_think_tags(text: str) -> str:
    """Remove <think>...</think> reasoning tokens from Qwen model output."""
    import re
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()


class GroqAgent:
    """
    Tenant-specific multilingual AI receptionist powered by Groq LLaMA.
    Bound to a single business — uses business data to attend customers.
    """

    def __init__(self, business_id: str):
        self.business_id = business_id
        self.business = None
        self.ai_employee = None
        self.services = []
        self.resources = []
        self.call_id = None
        self.activity_log = []
        self.detected_language = "hi"
        self.conversation_history = []   # OpenAI-style [{role, content}]

        self._load_tenant_context()
        self._init_groq()

    # ── Init ──────────────────────────────────────────────────────────────────
    def _load_tenant_context(self):
        self._log("Loading business data...")
        self.business = businesses_col().find_one({"_id": ObjectId(self.business_id)})
        if not self.business:
            raise ValueError(f"Business not found: {self.business_id}")
        self._log(f"Business: {self.business['name']} ({self.business.get('business_type', '?')})")

        self.ai_employee = ai_employees_col().find_one({"business_id": self.business_id})
        if not self.ai_employee:
            emp = new_ai_employee(self.business_id)
            ai_employees_col().insert_one(emp)
            self.ai_employee = emp
        self._log(f"AI Employee: {self.ai_employee.get('name', 'Maya')}")

        self.services = list(services_col().find({"business_id": self.business_id, "active": True}))
        self._log(f"Services loaded: {len(self.services)}")
        self.resources = list(resources_col().find({"business_id": self.business_id, "active": True}))
        self._log(f"Resources loaded: {len(self.resources)}")

    def _init_groq(self):
        from groq import Groq
        self.client = Groq(api_key=GROQ_API_KEY)
        self.current_model = GROQ_MODEL

        today = datetime.now(timezone.utc).strftime("%A, %B %d, %Y")
        system_prompt = build_system_prompt(
            business=self.business,
            services=self.services,
            resources=self.resources,
            ai_employee=self.ai_employee,
        )
        system_prompt += f"\n\nTODAY'S DATE: {today}"

        self.system_prompt = system_prompt
        self._log(f"Groq initialized: {self.current_model}")

    # ── Call lifecycle ────────────────────────────────────────────────────────
    def start_call(self) -> str:
        call = new_call(self.business_id)
        result = calls_col().insert_one(call)
        self.call_id = str(result.inserted_id)
        self._log("Call session started")
        return self.call_id

    def end_call(self, outcome: str = "completed"):
        if self.call_id:
            calls_col().update_one(
                {"_id": ObjectId(self.call_id)},
                {"$set": {"ended_at": datetime.now(timezone.utc), "outcome": outcome, "language": self.detected_language}},
            )
            self._log("Call ended")

    # ── Core: process a user message ──────────────────────────────────────────
    def process_message(self, user_message: str) -> dict:
        """
        Send user message → Groq with tools → handle tool calls → return final response.
        Returns: {response, language, tool_calls, activity}
        """
        lang = self._detect_language(user_message)
        self.detected_language = lang
        self._log(f"Language: {SUPPORTED_LANGUAGES.get(lang, lang)}")
        self._save_message("user", user_message, lang)

        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": user_message})

        # Build full messages list
        messages = [{"role": "system", "content": self.system_prompt}] + self.conversation_history

        tool_calls_made = []

        # Tool-call loop (Groq returns tool_calls, we execute and send back)
        for _ in range(8):  # Max iterations
            self._log("Calling Groq LLaMA...")
            try:
                completion = self.client.chat.completions.create(
                    model=self.current_model,
                    messages=messages,
                    tools=GROQ_TOOLS,
                    tool_choice="auto",
                    temperature=0.3,
                    max_tokens=2048,
                )
            except Exception as e:
                # Try fallback model
                err = str(e)
                self._log(f"Groq error: {err[:60]}, trying fallback...")
                try:
                    self.current_model = GROQ_FALLBACK_MODEL
                    completion = self.client.chat.completions.create(
                        model=self.current_model,
                        messages=messages,
                        tools=GROQ_TOOLS,
                        tool_choice="auto",
                        temperature=0.3,
                        max_tokens=2048,
                    )
                except Exception as e2:
                    raise RuntimeError(f"Groq unavailable: {e2}")

            choice = completion.choices[0]
            msg = choice.message

            # Append assistant message to history
            assistant_msg = {"role": "assistant"}
            if msg.content:
                assistant_msg["content"] = msg.content
            if msg.tool_calls:
                assistant_msg["tool_calls"] = [
                    {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in msg.tool_calls
                ]
            messages.append(assistant_msg)

            # If no tool calls -> final text response
            if not msg.tool_calls:
                ai_text = _strip_think_tags(msg.content or "")
                self.conversation_history.append({"role": "assistant", "content": ai_text})
                self._save_message("assistant", ai_text, lang)
                self._log("Response generated [OK]")
                return {
                    "response": ai_text,
                    "language": lang,
                    "language_name": SUPPORTED_LANGUAGES.get(lang, lang),
                    "tool_calls": tool_calls_made,
                    "activity": [a["message"] for a in self.activity_log],
                }

            # Execute each tool call
            for tc in msg.tool_calls:
                fn_name = tc.function.name
                try:
                    fn_args = json.loads(tc.function.arguments)
                except Exception:
                    fn_args = {}

                fn_args["business_id"] = self.business_id
                self._log(f"Tool: {fn_name}({list(fn_args.keys())})")

                tool_fn = TOOL_FUNCTIONS.get(fn_name)
                if tool_fn:
                    try:
                        result = tool_fn(**fn_args)
                        success = "error" not in result
                    except Exception as ex:
                        result = {"error": str(ex)}
                        success = False
                else:
                    result = {"error": f"Unknown tool: {fn_name}"}
                    success = False

                self._log(f"  Result: {'OK' if success else 'FAILED'} - {str(result)[:80]}")
                self._log_tool_execution(fn_name, fn_args, result, success)
                tool_calls_made.append({"tool": fn_name, "args": {k: v for k, v in fn_args.items() if k != "business_id"}, "result": result, "success": success})

                # Booking created -> update call record
                if fn_name == "create_booking" and result.get("success") and self.call_id:
                    calls_col().update_one(
                        {"_id": ObjectId(self.call_id)},
                        {"$set": {"booking_id": result.get("booking_id"), "intent": "booking"}},
                    )

                # Send tool result back
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, default=str),
                })

        # Fallback if loop exceeded
        fallback = "Maafi chahta hoon, mujhe thoda technical issue aaya. Kripya dobara puchiye."
        self.conversation_history.append({"role": "assistant", "content": fallback})
        return {"response": fallback, "language": lang, "tool_calls": tool_calls_made, "activity": []}

    # ── Language detection ────────────────────────────────────────────────────
    def _detect_language(self, text: str) -> str:
        try:
            from langdetect import detect_langs
            results = detect_langs(text)
            if results:
                lang = results[0].lang
                confidence = results[0].prob
                lang_map = {"en": "en", "hi": "hi", "mr": "mr", "mar": "mr"}
                mapped = lang_map.get(lang, "en")
                if confidence < 0.7:
                    return self._heuristic_detect(text)
                return mapped
        except Exception:
            pass
        return self._heuristic_detect(text)

    def _heuristic_detect(self, text: str) -> str:
        deva = sum(1 for c in text if '\u0900' <= c <= '\u097F')
        total = sum(1 for c in text if c.isalpha())
        if total == 0:
            return "en"
        if deva > total * 0.3:
            marathi_markers = ["ळ", "आहे", "नाही", "हवे", "हवी", "मला", "उद्या", "तुम्ही", "आम्ही"]
            return "mr" if any(m in text for m in marathi_markers) else "hi"
        hindi_words = ["kya", "hai", "mujhe", "chahiye", "kal", "aaj", "baje", "haan", "nahi",
                       "karo", "karna", "kitne", "kab", "accha", "theek", "namaste", "shukriya"]
        words = text.lower().split()
        if sum(1 for w in words if w in hindi_words) >= 1:
            return "hi"
        return "en"

    # ── Persistence ───────────────────────────────────────────────────────────
    def _save_message(self, role: str, content: str, language: str = ""):
        if self.call_id:
            conversations_col().insert_one(
                new_conversation_message(self.call_id, self.business_id, role, content, language)
            )
            calls_col().update_one(
                {"_id": ObjectId(self.call_id)},
                {"$push": {"transcript": {"role": role, "content": content, "language": language}}},
            )

    def _log_tool_execution(self, tool_name, tool_input, result, success):
        tool_executions_col().insert_one(
            new_tool_execution(self.business_id, self.call_id or "", tool_name,
                               {k: v for k, v in tool_input.items() if k != "business_id"}, result, success)
        )

    def _log(self, message: str):
        self.activity_log.append({"message": message, "timestamp": datetime.now(timezone.utc)})
