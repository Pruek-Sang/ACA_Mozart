import os
import re
import datetime
from mistralai import Mistral

# ==========================================
# [CONFIG]
# ==========================================
SOURCE_DIRECTORIES = [
    r"/home/builder/Desktop/ACA_Mozart/Copilot-Mozart/ACA_Mozart-copilot[RAG]/docs",
    r"/home/builder/Desktop/ACA_Mozart/MCP-tool+Auto lisp GEN"
]
OUTPUT_DIR = r"/home/builder/Desktop/ACA_Mozart/Copilot-Mozart/ACA_Mozart-copilot[RAG]/QC_ACA"
FINAL_FILENAME = "PROJECT_UNIVERSAL_CONTEXT.md" # ชื่อไฟล์ผลลัพธ์

api_key = "m9B58kJJRee8mpBjEbMRkuSpN13fqsdS"
client = Mistral(api_key=api_key)

# ขยะที่ไม่เอา
IGNORE_FILES = {'.DS_Store', 'Thumbs.db', FINAL_FILENAME}
IGNORE_DIRS = {'.git', '__pycache__', 'node_modules'}

def clean_ocr_text(text):
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def process_universal():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    final_path = os.path.join(OUTPUT_DIR, FINAL_FILENAME)
    
    print(f"🍽️  เริ่มภารกิจ 'นักชิม' (Auto-Detect Content)...")
    print("-" * 60)

    master_content = []
    master_content.append(f"# PROJECT KNOWLEDGE BASE\nGenerated: {datetime.datetime.now()}\n---\n")
    
    count_text = 0
    count_ocr = 0

    for source_dir in SOURCE_DIRECTORIES:
        if not os.path.exists(source_dir):
            print(f"❌ หาโฟลเดอร์ไม่เจอ: {source_dir}")
            continue

        for root, dirs, files in os.walk(source_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

            for filename in files:
                if filename in IGNORE_FILES: continue
                
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, start=os.path.dirname(source_dir))

                # --- 🔍 ขั้นตอนการ "ชิม" (Content Detection) ---
                is_binary = False
                content_text = ""
                
                try:
                    # ลองอ่านแบบ Text (UTF-8) ดูสักนิด
                    with open(full_path, "r", encoding="utf-8") as f:
                        content_text = f.read() # ถ้าอ่านผ่าน แปลว่าเป็น Text
                        is_binary = False
                except UnicodeDecodeError:
                    # ถ้าอ่านแล้ว Error แปลว่าเป็น Binary (Word/PDF/Image)
                    is_binary = True
                except Exception as e:
                    print(f"⚠️  อ่านไฟล์ไม่ได้ {filename}: {e}")
                    continue

                # --- 🛠️ ตัดสินใจทำอะไรต่อ ---
                try:
                    # CASE 1: เป็น Binary (Word/PDF หรือ .docx ที่เปลี่ยนชื่อเป็น .md) -> ส่ง OCR
                    if is_binary:
                        print(f"👁️  [OCR] ตรวจพบไฟล์ Binary: {filename}")
                        
                        uploaded = client.files.upload(
                            file={"file_name": filename, "content": open(full_path, "rb")},
                            purpose="ocr"
                        )
                        url = client.files.get_signed_url(file_id=uploaded.id).url
                        ocr_res = client.ocr.process(
                            model="mistral-ocr-latest",
                            document={"type": "document_url", "document_url": url},
                            include_image_base64=False 
                        )
                        
                        raw_md = "\n".join([page.markdown for page in ocr_res.pages])
                        cleaned = clean_ocr_text(raw_md)
                        
                        entry = f"\n<file name=\"{filename}\" type=\"OCR\">\n{cleaned}\n</file>\n"
                        master_content.append(entry)
                        count_ocr += 1

                    # CASE 2: เป็น Text ธรรมดา (Code/Markdown แท้) -> Copy เลย
                    else:
                        print(f"💾 [Text] อ่านไฟล์ปกติ: {filename}")
                        # ห่อ Code Block ให้สวยงาม
                        entry = f"\n<file name=\"{filename}\" type=\"CODE\">\n```\n{content_text}\n```\n</file>\n"
                        master_content.append(entry)
                        count_text += 1

                except Exception as e:
                    print(f"❌ Error Processing {filename}: {e}")

    # Save Final File
    with open(final_path, "w", encoding="utf-8") as f:
        f.write("".join(master_content))

    print("-" * 60)
    print(f"🎉 เสร็จแล้วเจ้าค่ะ! (Text: {count_text} | OCR: {count_ocr})")
    print(f"📂 ไฟล์รวมอยู่ที่: {final_path}")

if __name__ == "__main__":
    process_universal()
