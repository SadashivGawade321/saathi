"""
SAATHI ONE — High-Speed Call API Server
FastAPI backend for direct, hands-free browser voice calls.
Handles real-time speech-to-speech loops with Groq and MongoDB.
"""

import os
import sys
from datetime import datetime, timezone
from bson import ObjectId
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(__file__))

from database import businesses_col, ai_employees_col, bookings_col, customers_col, services_col
from telephony.provider import demo_provider
from ai.groq_agent import GroqAgent

app = FastAPI(title="SAATHI ONE Voice Call API")

# Enable CORS for browser requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active agent sessions in memory: { call_id: GroqAgent }
active_sessions: dict[str, GroqAgent] = {}


class StartCallRequest(BaseModel):
    demo_number: str


class ProcessMessageRequest(BaseModel):
    call_id: str
    message: str


class EndCallRequest(BaseModel):
    call_id: str


@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


@app.post("/api/call/start")
def start_call(req: StartCallRequest):
    """Resolve demo number, start a call session, and return initial greeting."""
    demo_clean = req.demo_number.strip().upper()
    biz_id = demo_provider.lookup_business(demo_clean)

    if not biz_id:
        # Fallback: check if demo_clean is directly a business_id or any registered number
        biz = businesses_col().find_one({"_id": ObjectId(demo_clean)}) if ObjectId.is_valid(demo_clean) else None
        if biz:
            biz_id = str(biz["_id"])
        else:
            # Check latest business
            latest_biz = businesses_col().find_one(sort=[("created_at", -1)])
            if latest_biz:
                biz_id = str(latest_biz["_id"])
            else:
                raise HTTPException(status_code=404, detail=f"No business found for number {demo_clean}")

    try:
        agent = GroqAgent(biz_id)
        call_id = agent.start_call()
        active_sessions[call_id] = agent

        biz_doc = agent.business or {}
        biz_name = biz_doc.get("name", "our business")
        biz_type = biz_doc.get("business_type", "Business")
        ai_emp = agent.ai_employee or {}
        ai_name = ai_emp.get("name", "Maya")

        # Domain-specific warm greeting
        domain_greetings = {
            "Restaurant": f"Namaste! {biz_name} me aapka swagat hai. Main Maya bol rahi hoon. Table booking ya menu details ke liye batayein?",
            "Salon": f"Hello! Main {biz_name} se Maya hoon. Haircut, styling ya beauty appointment ke liye batayein?",
            "Barber": f"Namaste! {biz_name} me aapka swagat hai. Haircut ya beard trim appointment ke liye batayein?",
            "Clinic": f"Namaste! {biz_name} me aapka swagat hai. Doctor consultation appointment ke liye main aapki kya sahayata kar sakti hoon?",
            "Doctor": f"Namaste! Main {biz_name} se Maya hoon. Doctor consultation appointment ke liye batayein?",
            "Dentist": f"Namaste! {biz_name} me aapka swagat hai. Dental checkup ya appointment ke liye batayein?",
            "Hotel": f"Namaste! {biz_name} me aapka swagat hai. Room reservation ya check-in ke liye batayein?",
        }
        greeting = domain_greetings.get(
            biz_type,
            f"Namaste! Main {ai_name} hoon, {biz_name} ki AI receptionist. Aaj main aapki kya sahayata kar sakti hoon?"
        )

        agent._save_message("assistant", greeting, "hi")

        return {
            "call_id": call_id,
            "business_id": biz_id,
            "business_name": biz_name,
            "business_type": biz_type,
            "ai_name": ai_name,
            "greeting": greeting,
            "language": "hi",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/call/message")
def process_message(req: ProcessMessageRequest):
    """Process user utterance through Groq agent with domain tools and MongoDB updates."""
    agent = active_sessions.get(req.call_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Call session not found or ended")

    try:
        result = agent.process_message(req.message)

        # Check if booking was created during this turn
        confirmed_booking = None
        b = bookings_col().find_one({"business_id": agent.business_id}, sort=[("created_at", -1)])
        if b:
            cust = customers_col().find_one({"_id": ObjectId(b["customer_id"])}) if b.get("customer_id") else None
            svc = services_col().find_one({"_id": ObjectId(b["service_id"])}) if b.get("service_id") and b["service_id"] != "any" else None
            confirmed_booking = {
                "booking_ref": b.get("booking_ref", "BK-CONFIRMED"),
                "date": b.get("date", ""),
                "time": b.get("start_time", ""),
                "customer_name": cust.get("name", "Client") if cust else "Client",
                "service_name": svc.get("name", "Service") if svc else "Appointment",
                "status": b.get("status", "confirmed"),
            }

        return {
            "response": result["response"],
            "language": result["language"],
            "tool_calls": result.get("tool_calls", []),
            "confirmed_booking": confirmed_booking,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/call/end")
def end_call(req: EndCallRequest):
    """End the call session cleanly."""
    agent = active_sessions.pop(req.call_id, None)
    if agent:
        agent.end_call("completed")
    return {"status": "ended", "call_id": req.call_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
