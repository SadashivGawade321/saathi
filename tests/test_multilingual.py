"""
SAATHI ONE — Multilingual Verification Test (Marathi & English)
Verifies Marathi and English reception workflows.
"""

import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from database import businesses_col
from ai.gemini import GeminiAgent

def test_marathi_and_english():
    biz = businesses_col().find_one({"name": "Test Mumbai Barbers"})
    if not biz:
        print("Test business not found. Run test_e2e_simulation.py first.")
        return

    biz_id = str(biz["_id"])
    agent = GeminiAgent(biz_id)
    agent.start_call()

    print("=== TEST MARATHI ===")
    marathi_msg = "मला उद्या संध्याकाळी सहा वाजता हेअरकटसाठी अपॉइंटमेंट हवी आहे. माझं नाव राहुल आहे."
    print(f"[Customer (Marathi)]: {marathi_msg}")
    res_mr = agent.process_message(marathi_msg)
    print(f"[Detected Language]: {res_mr['language_name']}")
    print(f"[AI Maya]: {res_mr['response']}")
    agent.end_call()

    agent_en = GeminiAgent(biz_id)
    agent_en.start_call()
    print("\n=== TEST ENGLISH ===")
    english_msg = "Hello, what services do you provide and what are your working hours?"
    print(f"[Customer (English)]: {english_msg}")
    res_en = agent_en.process_message(english_msg)
    print(f"[Detected Language]: {res_en['language_name']}")
    print(f"[AI Maya]: {res_en['response']}")
    agent_en.end_call()

    print("\n=== MULTILINGUAL CHECKS COMPLETED ===")

if __name__ == "__main__":
    test_marathi_and_english()
