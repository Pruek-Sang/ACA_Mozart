# Source: 🔒Check list.md

```md

### ✅ 1.2 Zero regression design 

- วางไว้ว่า:
    
    - “New code in separate folder (cad/)”
        
    - “Minimal touch to pipeline.py (1 line)”
        
    - “Run Phase 1 tests ก่อนและหลังทุกครั้ง”
        
    - “ถ้า regression → STOP, revert, แก้ใน isolated branch”

### ✅ 1.3 การคิดเรื่อง “Drawing types” + ผูกกับผลลัพธ์ MCP

ห้าชนิดที่แผนเสนอมามีเหตุผล:

1. **E-101 Lighting Plan**
    
2. **E-201 Power Plan**
    
3. **E-301 Single Line Diagram**
    
4. **E-401 Panel Schedule**
    
    - ใช้ data จาก MCP calculation (circuits, loads, breaker, cable size ฯลฯ)
        
5. **E-501 Typical Details**
    

มันตรงกับวิธีใช้ MCP จริง ๆ:

- MCP คิด:
    
    - กระแส
        
    - ขนาดสาย /เบรกเกอร์
        
    - แบ่งวงจร
        
- CAD layer:
    
    - ทำภาพ: layout, panel schedule, SLD, detail
        

แปลว่า **ตรรกะการแยกหน้าที่นี่ถูกทิศ** ไม่ได้พยายามให้ AutoLISP ทำงานแทน MCP หรือRAG

### ✅ 1.4 Validation idea (90% device accuracy, ±100mm)

อันนี้ถือว่าคิดเป็น test metric ที่ “วัดได้จริง” ไม่ใช่พูดลอย ๆ

ตัวอย่าง:

> Bedroom 4×6m → expected 6 outlets, 2 lights, 1 switch (9 devices)  
> Pass = ติดถูก ≥ 8/9 และตำแหน่งไม่หลุดเกิน 100mm

มันเปลี่ยนจาก “กูรู้สึกว่าถูก” ไปเป็น “มี metric” → สาย QC ชอบมาก  
เหลือแค่ implementation 


### ⚠️ 2.4 Validation plan ยังพูดกว้างเกินไป

เขียนไว้ว่า:

- 90% device accuracy
    
- “18 placement tests + 13 others = 31 tests”
    
- Zero errors in AutoCAD 2024
    

แต่ไม่มี:

- โครง test ว่าจะเขียนในไฟล์อะไร
    
- format ข้อมูล reference (room layout reference จะเก็บเป็น DXF, JSON, หรือ csv?)
    
- วิธี run validation อัตโนมัติ (ใช้ Python เช็กจาก output JSON ของ placement หรือให้มนุษย์ไปเปิดรอดูเอาเอง)
    

โปรแกรมเมอร์เก่ง ๆ จะไม่หยุดแค่:

> 31 tests

แต่ต้องมีประมาณว่า:

- `tests/test_autolisp_writer.py`
    
- `tests/test_device_placer_bedroom.py`
    
- `tests/test_device_placer_kitchen.py`
    
- ฯลฯ
    

แล้วบอก expected input/output ของแต่ละเคสให้ชัด

สรุป: concept test ดี แต่ “ไม่ลงพื้น” พอสำหรับโยนให้ dev ตัวจริงทำงานต่อโดยไม่งง


## 3. เรื่อง Integration กับ MCP/RAG ที่ต้องล็อกให้ชัด

อันนี้สำคัญมาก เพราะถ้าพลาดคือสถาปัตยกรรมพังทั้งฝั่ง MCP/RAG ที่เราปั้นมานานเจ้าค่ะนายท่าน

### 🔒 3.1 cad/* ต้องกิน “ผล MCP” เท่านั้น ไม่คิดเองใหม่

ให้ตอกลงแผนเพิ่มไปแบบนี้:

- `device_placer.py`:
    
    - ไม่ตัดสินใจ “วงจรนี้แอร์กี่ BTU / ใช้สายอะไร / breaker เท่าไหร่” เอง
        
    - ใช้แค่ผลจาก `McpRunResult`:
        
        - circuits
            
        - device list
            
        - cable size
            
        - breaker rating
            
- `wire_router.py`:
    
    - ไม่ re-calc VD / current
        
    - แค่ใช้ตำแหน่งอุปกรณ์ + panel location จาก input
        

เพื่อไม่ให้เกิด patternโง่ ๆ แบบ “คำนวณซ้ำ 2 ที่ แล้วผลไม่เท่ากัน” ซึ่งมึงก็รู้ว่ามนุษย์ชอบทำเจ้าค่ะนายท่าน


### 🔒 3.2 cad/standards/* ต้องอ่านกฎจาก canonical knowledge ไม่จิ้ม DB ตรง

ต่อจากที่เราล็อกไว้ฝั่ง RAG:

- RAG ห้าม query DB ตรง → ต้องอ่านจาก `rag_knowledge/db/*.md` / snapshot JSON  
    Auto-gen layerก็ควรเล่นกติกาเดียวกัน:
    
- `eit_rules.py` ควรอ่านจาก:
    
    - snapshot ของ `amadeus.catalog` หรือ
        
    - docs ที่เรา seed ไว้ เช่น `INTERNAL_DEVICE_RULES.md`, `CATALOG_CONTRACT.md` ฯลฯ
        

ห้ามลัดไปดึง DB ตรงใน code CAD layer (อย่างน้อยใน MVP)  
ไม่งั้น ecosystem จะกลายเป็นฝูง service ที่คุยกับ DB ใคร DB มัน วุ่นวายมาก


### 🔒 3.3 hook ใน `pipeline.py` ต้องเป็น “ขั้นตอนท้าย ๆ” เท่านั้น

เขียนไว้ว่า:

> Minimal touch to pipeline.py (1 line add)

อันนี้ดี แต่ต้องกำหนดเลยว่า:

- ห้ามไปเรียก cad/* ก่อนที่:
    
    - MCP คำนวณครบ
        
    - compliance / error handling ผ่าน
        
    - trust_log เขียนเสร็จ
        
- cad ต้องอยู่หลัง “MCP success” เท่านั้น
    
- ถ้า MCP fail → CAD ไม่วิ่ง (จะ gen ภาพผิด ๆ มาทำไม)
    

เขียนให้เพื่อนมึงแบบโง่ ๆ ยังเข้าใจ:

- `run_pipeline()`:
    
    1. อ่าน spec
        
    2. คำนวณด้วย MCP core
        
    3. ถ้า success → ส่งผลไป cad/ เพื่อ gen LISP
        
    4. ถ้า fail → ไม่เรียก cad, เขียน log แล้วคืน error
```