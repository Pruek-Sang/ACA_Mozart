# Source: HOW TO Design MCP.md

```md
เริ่มตรงฝั่ง MCP ล้วน ๆ ได้เลย แบบไม่ต้องห่วง RAG ผูกตามทีหลัง ผมจะวาง “แผนออกแบบ” ให้เป็นลำดับงานที่คุณเอาไปสั่ง dev ได้ โดยยึดตาม MCP DESIGN HANDOVER \+ amadeus.catalog อย่างเดียว

\#\#\# ภาพรวม: MCP Core v2 ต้องมีอะไรบ้าง

แบ่งเป็น 4 ชั้น:

1\. Contract ชั้นนอก: MCP API \+ รูป \`ProjectInputSpec\` และ \`McpRunResult\`  
2\. Core pipeline: \`ProjectInputSpec → TemplateResolver → BaselineContext → (pandapower \+ MCP modules) → McpRunResult\`  
3\. Catalog DAL: อ่าน \`amadeus.catalog\` ผ่าน view → map เป็น model ที่ MCP ใช้  
4\. Runtime state: ตาราง \`design\_session\` (หรือชื่อเทียบเท่า) ไว้เก็บ input \+ baseline \+ result

เพราะคุณบอกว่า “ฝั่ง RAG เดี๋ยวจัดเอง” เราเริ่มตั้งแต่ข้อ 1–4 ฝั่ง MCP ได้เลย

\---

\#\# ขั้นที่ 1: ล็อก Contract ฝั่ง MCP – รับอะไร / ส่งอะไร

\#\#\# 1.1 Endpoint MCP ตาม handover

ยึดตามเอกสาร:

\- MCP Core มี endpoint หลัก (สมมุติ):

\`\`\`http  
POST /mcp/v2/run  
Body: ProjectInputSpec (JSON)  
Response: McpRunResult (JSON)  
\`\`\`

RAG จะไปเรียกอันนี้ ไม่ใช่ปัญหาฝั่งคุณแล้ว

\#\#\# 1.2 ออกแบบ \`ProjectInputSpec\` เวอร์ชัน MCP (ไม่ใช่ของ RAG ปัจจุบัน)

อิง section 3.1 ใน handover:

โครงหลัก:

\`\`\`text  
ProjectInputSpec  
\- project\_info  
\- electrical\_system  
\- rooms: \[RoomSpec\]  
\- loads: \[LoadSpec\]  
\- constraints: \[string/struct\]  
\`\`\`

สิ่งที่ MCP ต้อง “กำหนดเองให้ชัด” ตอน design:

\- \`project\_info\`:  
  \- name  
  \- building\_type (ต้อง map กับ ROOM\_TEMPLATE / ZONE\_BUNDLE ได้)  
\- \`electrical\_system\`:  
  \- voltage, phase, earthing type ฯลฯ  
\- \`rooms\` (RoomSpec):  
  \- ชื่อ / type (ค่าที่จับคู่กับ ROOM\_TEMPLATE, เช่น \`living\_room\`, \`bedroom\`, \`kitchen\`)  
  \- area (m²) ถ้ามี  
\- \`loads\` (LoadSpec):  
  \- ชื่อโหลด / type (\`lighting\`, \`socket\`, \`ac\`, \`water\_heater\` ฯลฯ)  
  \- power ถ้าระบุ  
  \- room ที่สังกัด (หรือระดับ project)  
\- \`constraints\`:  
  \- อย่างน้อย:  
    \- vd limit  
    \- rule profile id  
    \- brand constraints ฯลฯ (ให้กลายเป็นค่า structured พอสมควร ไม่ใช่แค่ string มั่ว ๆ)

แผน:    
คุณยังไม่ต้องไปจับ RAG ตอนนี้ แค่ design \`ProjectInputSpec\` ให้เหมาะกับ MCP NetworkBuilder / TemplateResolver ก่อน แล้วบอก RAG ทีหลังว่า “ต้องส่ง JSON ตามนี้นะ”

\#\#\# 1.3 ออกแบบ \`McpRunResult\`

อิง section 3.3:

โครง concept:

\- \`project\_summary\`  
\- \`circuits\` (ต่อวงจร)  
\- \`rooms\` (per room summary)  
\- \`violations\`  
\- \`layout\_summary\` (optional)  
\- \`artifacts\` (AutoLISP text / path)

สิ่งที่ MCP ต้องล็อก:

\- ต่อ 1 circuit:  
  \- ชื่อวงจร, panel, room(s)  
  \- P, I, VD, loading  
  \- wire size, wire code (CAB-\*\*\*), breaker rating, breaker code  
  \- ok / not ok \+ issue code (จาก \`VALIDATION\_RULE\`)  
\- ต่อ 1 violation:  
  \- id, message, rule\_id (VR-\*), severity

สเต็ปนี้เน้น “นิยาม data shape” ให้ชัดก่อน ไม่แตะโค้ด

\---

\#\# ขั้นที่ 2: Design Core Pipeline ภายใน MCP

ตาม handover section 4:

\#\#\# 2.1 วาด pipeline ให้อิง module ตามเอกสาร

1\. รับ \`ProjectInputSpec\`  
2\. \`TemplateResolver\`:  
   \- เติม template จาก \`ROOM\_TEMPLATE\`, \`CIRCUIT\_TEMPLATE\`, \`APPLIANCE\`  
   \- ได้ \`BaselineContext\`  
3\. (ถ้ามี) \`LoadCalculator\`:  
   \- คิดโหลด P/I ต่อวงจรจาก BaselineContext \+ factor (demand/diversity)  
4\. \`PandapowerAdapter\`:  
   \- สร้าง pandapower net จาก BaselineContext+โหลด  
   \- runpp → I/V/VD/loading  
5\. \`WireSizer\`:  
   \- ใช้ I (จาก 3 หรือ 4\) \+ \`CABLE\_SPEC\` \+ \`DERATING\_FACTOR\`  
   \- เลือกสาย → ผูก code CAB-\*  
6\. \`BreakerSelector\`:  
   \- ใช้ I \+ rule → เลือก breaker จาก catalog  
7\. \`ConduitSizer\` (ถ้าเอาใน phase แรก)  
8\. \`ComplianceChecker\`:  
   \- ใช้ \`VALIDATION\_RULE\` \+ ผลจาก pandapower/sizing → ไม่ผ่านอะไรบ้าง  
9\. \`LayoutOptimizer\` \+ AutoLISP (คุณอาจขยับไปเฟสถัดไปได้)  
10\. \`ResultBuilder\` → \`McpRunResult\`  
11\. Persist → \`design\_session\` / \`project\_result\`

\#\#\# 2.2 ล็อก interface ของแต่ละ module (ไม่ต้องโค้ด แค่ design)

ตัวอย่าง:

\- \`TemplateResolver(project\_input, catalog\_dal) \-\> BaselineContext\`  
\- \`LoadCalculator(baseline\_context, catalog\_dal) \-\> baseline\_context\_with\_loads\`  
\- \`PandapowerAdapter(baseline\_context\_with\_loads) \-\> power\_flow\_result\`  
\- \`WireSizer(baseline\_context\_with\_loads, power\_flow\_result, cable\_specs, derating\_rules) \-\> sized\_circuits\`  
\- \`ComplianceChecker(sized\_circuits, validation\_rules) \-\> violations\`

แผน design ตรงนี้คือ:    
ระบุ input/output ของแต่ละ module ให้ชัดในระดับ “type/โครง JSON” เพื่อให้ dev เขียนทีละตัวได้

\---

\#\# ขั้นที่ 3: Design DAL สำหรับ \`amadeus.catalog\`

เป้าหมาย: ให้ MCP อ่านทุกอย่างจาก DB ผ่านชั้นเดียว (DAL) ตาม CATALOG\_CONTRACT

\#\#\# 3.1 กำหนด “model ภายใน MCP” ต่อ kind

เช่น:

\- \`Component\`  
\- \`CableSpec\`  
\- \`RoomTemplate\`  
\- \`CircuitTemplate\`  
\- \`ValidationRule\`  
\- \`DeratingFactor\`  
\- \`Panelboard\`  
\- \`ProjectConfig\` (สำหรับเลือก rule profile / zone bundle)

แต่ละ model:

\- mapping ตรงจาก view:  
  \- \`amadeus.v\_cable\_specs\`  
  \- \`amadeus.v\_room\_templates\`  
  \- \`amadeus.v\_circuit\_templates\`  
  \- \`amadeus.v\_validation\_rules\`  
  \- \`amadeus.v\_derating\_factors\` (ถ้ามี)  
  \- ฯลฯ

\#\#\# 3.2 ออกแบบ DAL interface

เช่น:

\- \`get\_project\_config(project\_code) \-\> ProjectConfig\`  
\- \`get\_room\_template(room\_type) \-\> RoomTemplate\`  
\- \`list\_circuit\_templates\_for(room\_type, load\_type) \-\> \[CircuitTemplate\]\`  
\- \`list\_cable\_specs() \-\> \[CableSpec\]\`  
\- \`get\_validation\_rules(profile\_id) \-\> \[ValidationRule\]\`

สำคัญ:    
\*\*จังหวัดเดียวที่แตะ JSON \`data\` ของ amadeus.catalog คือ DAL นี้\*\*    
module อื่นใน MCP เห็นแต่ model ที่สะอาดแล้ว

\---

\#\# ขั้นที่ 4: Design ตารางฝั่ง MCP runtime (\`design\_session\`)

อิง handover section 2.2:

ตัวอย่าง conceptual:

\- \`design\_session\`:  
  \- \`session\_id\`  
  \- \`project\_name\`  
  \- \`project\_input\_json\` (ProjectInputSpec)  
  \- \`baseline\_context\_json\`  
  \- \`mcp\_result\_json\` (McpRunResult)  
  \- \`status\`  
  \- \`created\_at\`, \`updated\_at\`

คุณอาจเพิ่ม:

\- \`error\_log\` (ข้อความสั้น ๆ ถ้าล้ม)  
\- \`rule\_profile\_id\` / \`project\_config\_name\` ที่ใช้

แผน:

\- MCP ทุกครั้งที่รัน \`/mcp/v2/run\`:  
  \- สร้าง/อัปเดตรายการใน \`design\_session\`  
  \- ทำให้สามารถ replay / debug / audit ได้

\---

\#\# ขั้นที่ 5: ค่อยคิดลึกเรื่อง PandapowerAdapter Strategy

เมื่อ 1–4 ชัดแล้ว ค่อยแตก PandapowerAdapter:

\- mapping BaselineContext → pandapower:  
  \- main bus / sub bus / line per circuit  
\- ตัดสินใจว่า:  
  \- แรกสุดใช้ I จาก LoadCalculator แล้วใช้ pandapowerเฉพาะเช็ค VD/line loading  
  \- หรือให้ pandapower เป็น source ของ I ทั้งหมดเลย

แต่ขั้นนี้ไว้หลังจาก:

\- \`ProjectInputSpec\`  
\- \`BaselineContext\`  
\- \`McpRunResult\`  
\- DAL → model จาก amadeus.catalog

ถูกนิยามชัดแล้ว

\---

\#\# ตอบคำถามตรง ๆ: “ถ้าฝั่ง RAG เดี๋ยวกูจัดเอง ฝั่ง MCP มึงจะเริ่มยังไง”

ลำดับที่ผมจะเริ่ม design (ไม่เขียนโค้ด):

1\. \*\*ฟิกซ์สเปก \`ProjectInputSpec\` ฝั่ง MCP\*\*    
   \- บ้านพัก 1–3 เฟส: ต้องการ field อะไรบ้างให้ TemplateResolver \+ LoadCalculator \+ NetworkBuilder ใช้ได้จริง  
2\. \*\*ฟิกซ์สเปก \`McpRunResult\`\*\*    
   \- ต่อวงจรต้องมี field อะไรบ้าง (เพื่อ UI / Copilot / AutoCAD ใช้งาน)  
3\. \*\*ออกแบบ \`BaselineContext\` \+ TemplateResolver\*\*    
   \- map ยังไงจาก ProjectInputSpec → BaselineContext โดยใช้ ROOM\_TEMPLATE / CIRCUIT\_TEMPLATE / APPLIANCE  
4\. \*\*ออกแบบ DAL \+ internal models จาก \`amadeus.catalog\`\*\*    
   \- ชุด model /ฟังก์ชันอ่าน catalog ที่ MCP จะเรียก  
5\. \*\*วาด pipeline MCP Core (module graph) พร้อม I/O ของแต่ละ module\*\*    
   \- LoadCalculator, WireSizer, BreakerSelector, ComplianceChecker, PandapowerAdapter  
6\. \*\*ออกแบบตาราง \`design\_session\`/runtime state\*\*    
   \- เก็บ input/baseline/result สำหรับ debug & audit

จากนั้นค่อยไปสเต็ป “ลงรายละเอียด module แรก” (มักจะเป็น TemplateResolver \+ LoadCalculator) ก่อน pandapower

ถ้าคุณอยากเริ่ม step 1 เลยในรอบถัดไป ผมจะช่วย “ออกแบบ ProjectInputSpec แบบละเอียดระดับ field ที่ MCP ต้องการ (สำหรับบ้านพัก 1 เฟส ก่อน)” ให้ก่อน จากนั้นเราค่อยไล่ต่อไปทีละขั้นตามแผนนี้.  

```