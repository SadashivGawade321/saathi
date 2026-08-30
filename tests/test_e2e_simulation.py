"""
SAATHI ONE — End-to-End Simulation Test
Simulates the complete customer-AI receptionist flow:
Business Setup -> Call Start -> Hindi Appointment Request -> Function Call -> DB Mutation -> Hindi Response
"""

import sys
import os
import io

# Set UTF-8 encoding for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from database import (
    get_db,
    businesses_col,
    services_col,
    resources_col,
    bookings_col,
    customers_col,
    ai_employees_col,
    calls_col,
    conversations_col,
    tool_executions_col,
    ensure_indexes,
)
from models import (
    new_business,
    new_service,
    new_resource,
    new_ai_employee,
)
from telephony.provider import demo_provider
from ai.gemini import GeminiAgent


def run_e2e_simulation():
    print("=== 1. INITIALIZING DATABASE & INDEXES ===")
    ensure_indexes()

    # Clean previous test business if any
    test_biz = businesses_col().find_one({"name": "Test Mumbai Barbers"})
    if test_biz:
        biz_id_str = str(test_biz["_id"])
        businesses_col().delete_one({"_id": test_biz["_id"]})
        services_col().delete_many({"business_id": biz_id_str})
        resources_col().delete_many({"business_id": biz_id_str})
        bookings_col().delete_many({"business_id": biz_id_str})
        customers_col().delete_many({"business_id": biz_id_str})
        ai_employees_col().delete_many({"business_id": biz_id_str})
        calls_col().delete_many({"business_id": biz_id_str})
        tool_executions_col().delete_many({"business_id": biz_id_str})

    print("=== 2. CREATING BUSINESS PROFILE ===")
    biz_doc = new_business(
        owner_id="test_owner_1",
        name="Test Mumbai Barbers",
        business_type="Barber",
        description="Premium grooming & hair styling salon in Bandra West.",
        address="12 Hill Road, Bandra West, Mumbai",
        phone="+91 98200 12345",
        email="contact@mumbaibarbers.test",
    )
    biz_res = businesses_col().insert_one(biz_doc)
    biz_id = str(biz_res.inserted_id)
    print(f"Business created with ID: {biz_id}")

    # Assign Demo Number
    demo_info = demo_provider.assign_number(biz_id)
    print(f"Assigned Demo Number: {demo_info['number']}")

    print("=== 3. ADDING SERVICES & RESOURCES ===")
    svc1 = new_service(biz_id, "Classic Haircut", 30, 300.0, "Professional hair styling & wash")
    svc2 = new_service(biz_id, "Beard Grooming", 20, 150.0, "Beard trim and hot towel shave")
    services_col().insert_many([svc1, svc2])

    res1 = new_resource(biz_id, "Barber Rohit", "Barber", 1)
    res2 = new_resource(biz_id, "Barber Amit", "Barber", 1)
    resources_col().insert_many([res1, res2])

    print("=== 4. CREATING AI EMPLOYEE ===")
    ai_emp = new_ai_employee(biz_id, name="Maya", role="AI Receptionist")
    ai_employees_col().insert_one(ai_emp)

    print("=== 5. INITIALIZING GEMINI RECEPTIONIST AGENT ===")
    agent = GeminiAgent(biz_id)
    call_id = agent.start_call()
    print(f"Call started with Call ID: {call_id}")

    print("\n=== 6. SIMULATING MULTILINGUAL CUSTOMER INTERACTION (HINDI) ===")
    user_msg_1 = "Mujhe kal shaam 5 baje Classic Haircut ke liye appointment chahiye, mera naam Rohan Verma hai."
    print(f"\n[Customer]: {user_msg_1}")

    result_1 = agent.process_message(user_msg_1)
    print(f"\n[Detected Language]: {result_1['language_name']} ({result_1['language_confidence']:.0%})")
    print(f"[Tool Calls Made]: {len(result_1['tool_calls'])}")
    for tc in result_1['tool_calls']:
        print(f"   -> Tool: {tc['tool']} | Success: {tc['success']} | Result: {tc['result']}")
    print(f"\n[AI Maya]: {result_1['response']}")

    print("\n=== 7. CUSTOMER CONFIRMS BOOKING ===")
    user_msg_2 = "Haan bilkul, confirm kar dijiye."
    print(f"\n[Customer]: {user_msg_2}")

    result_2 = agent.process_message(user_msg_2)
    print(f"\n[Detected Language]: {result_2['language_name']} ({result_2['language_confidence']:.0%})")
    print(f"[Tool Calls Made]: {len(result_2['tool_calls'])}")
    for tc in result_2['tool_calls']:
        print(f"   -> Tool: {tc['tool']} | Success: {tc['success']} | Result: {tc['result']}")
    print(f"\n[AI Maya]: {result_2['response']}")

    agent.end_call("booking_completed")

    print("\n=== 8. VERIFYING MONGODB DATABASE MUTATIONS ===")
    bookings = list(bookings_col().find({"business_id": biz_id}))
    customers = list(customers_col().find({"business_id": biz_id}))
    calls = list(calls_col().find({"business_id": biz_id}))
    executions = list(tool_executions_col().find({"business_id": biz_id}))

    print(f"Total Bookings in MongoDB: {len(bookings)}")
    for b in bookings:
        print(f"   - Booking: Date={b.get('date')} Time={b.get('start_time')} Status={b.get('status')} Source={b.get('source')}")

    print(f"Total Customers in MongoDB: {len(customers)}")
    for c in customers:
        print(f"   - Customer: Name={c.get('name')}")

    print(f"Total Calls Logged: {len(calls)}")
    print(f"Total Tool Executions Logged: {len(executions)}")

    assert len(bookings) >= 1, "Expected at least 1 confirmed booking in MongoDB!"
    print("\n=== SUCCESS: END-TO-END DEMO FLOW FULLY VERIFIED ===")


if __name__ == "__main__":
    run_e2e_simulation()
