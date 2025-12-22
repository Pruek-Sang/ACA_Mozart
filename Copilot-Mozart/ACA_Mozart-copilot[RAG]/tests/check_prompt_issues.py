#!/usr/bin/env python3
"""
Minimal test to simulate LLM prompt and check for issues.
This doesn't call the actual LLM - just checks prompt construction.
"""

import re

# Simulated user input (similar to user's request)
TEST_INPUT = """ออกแบบระบบไฟฟ้าบ้านพักอาศัย 2 ชั้น

ตำแหน่งตู้ไฟและระยะเพื่อทำ BOQ:
- ตู้ MDB/DB อยู่ "โรงรถ ชั้น 1"
- ระยะสายเมนจากมิเตอร์ถึงตู้ MDB = 12 เมตร
- ระยะเฉลี่ยจากตู้ MDB ไปห้องชั้น 1 = 15 เมตร/วงจร
- ระยะเฉลี่ยจากตู้ MDB ไปห้องชั้น 2 = 25 เมตร/วงจร

ชั้น 1
1) ห้องนั่งเล่น 30 ตร.ม. 
   - ต้องการเต้ารับคู่ 6 จุด
   - ไฟดาวน์ไลท์ LED 20W จำนวน 4 ดวง
   - พัดลมเพดาน 60W จำนวน 1 ตัว
2) ห้องครัว 15 ตร.ม.
   - มีเตาแม่เหล็กไฟฟ้า 3000W 1 เครื่อง
   - มีไมโครเวฟ 1500W 1 เครื่อง
   - ตู้เย็น 300W 1 เครื่อง
3) ห้องน้ำ 1 
   - เครื่องทำน้ำอุ่น 4500W 1 เครื่อง
   - เต้ารับกันน้ำ 16A 1 จุด
   - ไฟ LED 10W 1 ดวง

ชั้น 2
1) ห้องนอน 1 (14 ตร.ม.)
   - เต้ารับคู่ 4 จุด
   - ไฟ LED 10W 3 ดวง
2) ห้องน้ำ 2
   - เครื่องทำน้ำอุ่น 3500W 1 เครื่อง

ระยะหม้อแปลง 10 เมตร"""

# Read the actual prompt from service.py
def get_prompt_from_service():
    """Extract the prompt template from service.py"""
    with open('app/service.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the extraction prompt
    start = content.find("extraction_prompt = f'''")
    end = content.find("'''", start + 30)
    
    if start > 0 and end > 0:
        prompt_section = content[start:end + 3]
        return prompt_section
    return None

def check_prompt_issues():
    """Check for common issues in the prompt"""
    print("=" * 60)
    print("🔍 PROMPT ANALYSIS")
    print("=" * 60)
    
    prompt = get_prompt_from_service()
    if not prompt:
        print("❌ Could not find extraction_prompt in service.py")
        return
    
    # Count characters
    print(f"📊 Prompt template length: {len(prompt)} chars")
    
    # Count {{ and }} (escaped braces)
    double_open = prompt.count("{{")
    double_close = prompt.count("}}")
    print(f"📊 Escaped braces: {{ count={double_open}, }} count={double_close}")
    
    if double_open != double_close:
        print("❌ ERROR: Mismatched escaped braces!")
    else:
        print("✅ Escaped braces match")
    
    # Check for unescaped single braces (inside f-string, excluding {{ and }})
    # This is tricky - we need to find { that aren't part of {{
    content = prompt.replace("{{", "XX").replace("}}", "YY")
    single_open = content.count("{")
    single_close = content.count("}")
    
    print(f"📊 Variable braces: {{ count={single_open}, }} count={single_close}")
    
    if single_open == single_close:
        print("✅ Variable braces match (f-string format OK)")
    else:
        print("⚠️ WARNING: Mismatched variable braces - may cause f-string error")
    
    # Check if query is inserted correctly
    if "{normalized_query}" in content:
        print("✅ Query variable found in prompt")
    else:
        print("❓ normalized_query not found as variable in this section")
    
    # Estimate total token count
    user_input_len = len(TEST_INPUT)
    total_len = len(prompt) + user_input_len
    estimated_tokens = total_len / 4  # rough estimate
    print(f"\n📊 With user input:")
    print(f"   User input: {user_input_len} chars")
    print(f"   Total: ~{int(estimated_tokens)} tokens (estimate)")
    
    if estimated_tokens > 30000:
        print("⚠️ WARNING: Input may be too long for some models!")
    else:
        print("✅ Token count seems reasonable")


def check_json_schema():
    """Check if JSON schema in prompt has issues"""
    print("\n" + "=" * 60)
    print("🔍 JSON SCHEMA CHECK")
    print("=" * 60)
    
    # The expected JSON output format
    # Looking for common issues
    with open('app/service.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find JSON schema section
    json_start = content.find('"project_name":')
    json_end = content.find('"missing_info":', json_start) + 50
    
    if json_start > 0:
        schema_section = content[json_start:json_end]
        print("📋 JSON Schema section found")
        
        # Check for common issues
        if 'จำนวนชั้น (ถ้าไม่ระบุให้ใส่ 1)' in schema_section:
            print("⚠️ WARNING: Thai text as value without quotes in JSON example")
            print("   This might confuse the LLM about proper JSON format")


if __name__ == "__main__":
    print(f"📝 User input length: {len(TEST_INPUT)} chars")
    print("")
    check_prompt_issues()
    check_json_schema()
    
    print("\n" + "=" * 60)
    print("💡 RECOMMENDATIONS")
    print("=" * 60)
    print("1. Check Cloud Run logs for: '📤 LLM extraction response'")
    print("2. Look for line: '✅ Extracted: X rooms, Y loads'")
    print("3. If X=0 and Y=0, the LLM extraction is failing")
    print("4. If JSON parse error, check LLM response format")
