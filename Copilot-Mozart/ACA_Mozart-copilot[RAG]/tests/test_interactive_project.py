#!/usr/bin/env python3
"""
Interactive Project Creation Test
ทดสอบการสร้างโปรเจคแบบ step-by-step conversation
"""

import requests
import json
from typing import Dict, Any

API_URL = "http://localhost:8080/api/v1/ask"

def send_question(question: str, language: str = "th") -> Dict[str, Any]:
    """ส่งคำถามไปยัง RAG API"""
    payload = {
        "query": question,
        "language": language
    }
    
    response = requests.post(API_URL, json=payload)
    response.raise_for_status()
    return response.json()

def print_response(step: int, question: str, response: Dict[str, Any]):
    """พิมพ์ response ในรูปแบบที่อ่านง่าย"""
    print(f"\n{'='*80}")
    print(f"STEP {step}: {question}")
    print(f"{'='*80}")
    print(f"\n**คำตอบจาก LLM:**")
    print(response.get("answer", ""))
    print(f"\n**Sources:** {len(response.get('sources', []))} documents")
    print(f"**Confidence:** {response.get('confidence', 0)}")
    print(f"**Model:** {response.get('model_used', 'unknown')}")

def main():
    """ทดสอบแบบ step-by-step"""
    
    print("🏠 Interactive Project Creation Test")
    print("=" * 80)
    
    # Step 1: คำถามเริ่มต้น
    step1_q = "ช่วยออกแบบระบบไฟฟ้าบ้าน 2 ชั้นหน่อย"
    print(f"\n📋 Testing Step 1: General Request")
    resp1 = send_question(step1_q)
    print_response(1, step1_q, resp1)
    
    # Check: ถามกลับมั้ย?
    answer1 = resp1.get("answer", "").lower()
    asks_clarification = any(keyword in answer1 for keyword in [
        "กรุณา", "ช่วยบอก", "ต้องการ", "ระบุ", "ข้อมูล"
    ])
    
    print(f"\n✅ Check: ถามกลับมั้ย? {'YES' if asks_clarification else 'NO'}")
    
    # Step 2: ให้ข้อมูลห้อง
    step2_q = "บ้านชื่อ 'บ้านคุณสมชาย' มีห้องนอน 3 ห้อง ห้องน้ำ 2 ห้อง ห้องครัว 1 ห้อง"
    print(f"\n📋 Testing Step 2: Room Layout")
    resp2 = send_question(step2_q)
    print_response(2, step2_q, resp2)
    
    # Check: สรุปข้อมูลที่ได้มั้ย?
    answer2 = resp2.get("answer", "")
    mentions_project_name = "สมชาย" in answer2
    
    print(f"\n✅ Check: จำชื่อโปรเจคได้มั้ย? {'YES' if mentions_project_name else 'NO'}")
    
    # Step 3: ให้ข้อมูลเครื่องใช้
    step3_q = "ห้องนอนหลักมีแอร์ 12000 BTU ห้องครัวมีเตาไฟฟ้า 3000W เครื่องทำน้ำอุ่นในห้องน้ำใหญ่ 3500W"
    print(f"\n📋 Testing Step 3: Appliances")
    resp3 = send_question(step3_q)
    print_response(3, step3_q, resp3)
    
    # Check: map device codes ถูกมั้ย?
    answer3 = resp3.get("answer", "")
    mentions_device_codes = any(code in answer3 for code in [
        "AC-12000BTU", "AC_12000BTU", "HEATER-3500W", "HEATER_3500W"
    ])
    
    print(f"\n✅ Check: Map device codes ได้มั้ย? {'YES' if mentions_device_codes else 'NO'}")
    
    # Step 4: ยืนยันและขอ JSON
    step4_q = "ข้อมูลครบแล้ว สร้าง JSON ให้หน่อย"
    print(f"\n📋 Testing Step 4: Request JSON")
    resp4 = send_question(step4_q)
    print_response(4, step4_q, resp4)
    
    # Check: มี JSON มั้ย?
    answer4 = resp4.get("answer", "")
    has_json = "{" in answer4 and "}" in answer4
    
    print(f"\n✅ Check: มี JSON output มั้ย? {'YES' if has_json else 'NO'}")
    
    # Summary
    print(f"\n{'='*80}")
    print(f"📊 TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Step 1 - Asks Clarification: {'✅' if asks_clarification else '❌'}")
    print(f"Step 2 - Remembers Data: {'✅' if mentions_project_name else '❌'}")
    print(f"Step 3 - Maps Device Codes: {'✅' if mentions_device_codes else '❌'}")
    print(f"Step 4 - Provides JSON: {'✅' if has_json else '❌'}")
    
    all_pass = asks_clarification and mentions_project_name and mentions_device_codes and has_json
    print(f"\n{'✅ ALL TESTS PASSED' if all_pass else '❌ SOME TESTS FAILED'}")

if __name__ == "__main__":
    main()
