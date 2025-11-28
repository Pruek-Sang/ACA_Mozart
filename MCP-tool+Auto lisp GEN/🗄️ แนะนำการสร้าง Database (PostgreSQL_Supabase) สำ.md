<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# 🗄️ แนะนำการสร้าง Database (PostgreSQL/Supabase) สำหรับ Module อื่น ๆ

ขอรายงานนายท่านค่ะ จากการค้นหาพบว่า **ไม่มี Public API ที่ครอบคลุมราคา/มาตรฐาน/อุปกรณ์ไฟฟ้าไทยแบบ Real-time** แต่มีแหล่งข้อมูลที่ **ดึงมาสร้าง Database เองได้** Volta จะแนะนำแนวทางทั้งหมดค่ะ

***

## 📊 ส่วนที่ 1: แหล่งข้อมูลไทยที่ดึงได้ (Official Sources)

### **1.1 มาตรฐาน มอก. (Thai Industrial Standards)**

| แหล่งข้อมูล | URL | ข้อมูลที่ได้ | วิธีดึง |
| :-- | :-- | :-- | :-- |
| **สำนักงานมาตรฐานผลิตภัณฑ์อุตสาหกรรม (TISI)** | [appdb.tisi.go.th](https://appdb.tisi.go.th) | รายชื่อ มอก. ทั้งหมด (เลขที่, ชื่อ, รายละเอียด) | Web Scraping[^1][^2][^3] |
| **TISI API (ถ้ามี)** | service.tisi.go.th | ข้อมูลใบอนุญาต, มาตรฐานบังคับ | HTTP Request (ถ้า expose API) |
| **PDF มอก. 2955** | ดาวน์โหลดจาก TISI | รายละเอียด RCBO, Breaker, Wire | RAG (Parse PDF)[^4] |

**วิธีสร้าง Database:**

```sql
-- Table: tis_standards
CREATE TABLE tis_standards (
    id SERIAL PRIMARY KEY,
    tis_number VARCHAR(50) UNIQUE NOT NULL,  -- เช่น "2955-2562"
    name_th TEXT NOT NULL,
    name_en TEXT,
    category VARCHAR(100),  -- "Electrical", "Construction"
    description TEXT,
    pdf_url TEXT,
    is_mandatory BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```


***

### **1.2 ราคาวัสดุก่อสร้าง (Construction Material Prices)**

| แหล่งข้อมูล | URL | ข้อมูลที่ได้ | วิธีดึง |
| :-- | :-- | :-- | :-- |
| **สำนักนโยบายและยุทธศาสตร์การค้า (TPSO)** | [tpso.go.th](https://www.tpso.go.th) | ดัชนีราคาวัสดุก่อสร้าง (CMI), ดัชนี K | Web Scraping / CSV Download[^5][^6] |
| **ธนาคารแห่งประเทศไทย (BOT)** | [bot.or.th](https://www.bot.or.th) | Producer Price Index (PPI), CMI | API / CSV[^6][^7] |
| **Statista (Premium)** | statista.com | PPI Construction Materials | API (Paid)[^8] |

**ตัวอย่าง Database:**

```sql
-- Table: material_prices (ราคาวัสดุ)
CREATE TABLE material_prices (
    id SERIAL PRIMARY KEY,
    material_type VARCHAR(100) NOT NULL,  -- "wire", "breaker", "conduit"
    brand VARCHAR(100),
    model VARCHAR(100),
    specification JSONB,  -- {"size_mm2": 2.5, "voltage_v": 220}
    unit VARCHAR(20),  -- "เมตร", "ตัว", "เส้น"
    price_thb DECIMAL(10, 2) NOT NULL,
    price_date DATE NOT NULL,
    region VARCHAR(50),  -- "bangkok", "upcountry"
    source VARCHAR(100),  -- "TPSO", "BOT", "Manual"
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index
CREATE INDEX idx_material_type ON material_prices(material_type);
CREATE INDEX idx_price_date ON material_prices(price_date);
```


***

### **1.3 Catalog อุปกรณ์ไฟฟ้า (Equipment Catalogs)**

**แหล่งข้อมูล:**


| บริษัท | PDF Catalog | ข้อมูล | วิธีดึง |
| :-- | :-- | :-- | :-- |
| **Charoong Thai Wire \& Cable (CTW)** | ctw.co.th | ราคาสาย THW/NYY/CV ทุกขนาด[^9] | Parse PDF → Database |
| **Thai Yazaki** | thaiyazaki-electricwire.co.th | Price List สาย, Cable[^10] | Parse PDF → Database |
| **TMK Electrics** | tmkelectrics.com | Breaker, Contactor, Relay[^11] | Parse PDF → Database |
| **Schneider Electric Thailand** | schneider-electric.co.th | Breaker Catalog (iC60, C120) | Parse PDF / Web Scraping |
| **Mitsubishi Electric Thailand** | mitsubishielectric.co.th | Breaker NF, NV series | Parse PDF / Web Scraping |

**ตัวอย่าง Database:**

```sql
-- Table: wire_catalog (สาย)
CREATE TABLE wire_catalog (
    id SERIAL PRIMARY KEY,
    brand VARCHAR(100) NOT NULL,
    model VARCHAR(100),
    type VARCHAR(50),  -- "THW", "NYY", "CV"
    size_mm2 DECIMAL(5, 2) NOT NULL,
    voltage_v INT,
    num_cores INT DEFAULT 1,
    ampacity_a DECIMAL(6, 2),
    resistance_ohm_per_km DECIMAL(10, 6),
    reactance_ohm_per_km DECIMAL(10, 6),
    price_per_m DECIMAL(10, 2),
    price_date DATE,
    datasheet_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table: breaker_catalog (เบรกเกอร์)
CREATE TABLE breaker_catalog (
    id SERIAL PRIMARY KEY,
    brand VARCHAR(100) NOT NULL,  -- "Schneider", "Mitsubishi"
    series VARCHAR(100),  -- "iC60N", "NF125-CW"
    model VARCHAR(100),
    rating_a INT NOT NULL,
    poles INT NOT NULL,  -- 1, 2, 3, 4
    curve_type VARCHAR(10),  -- "B", "C", "D"
    breaking_capacity_ka DECIMAL(6, 2),
    voltage_v INT,
    has_rcbo BOOLEAN DEFAULT FALSE,
    rcbo_sensitivity_ma INT,  -- 10, 30, 100, 300
    price_thb DECIMAL(10, 2),
    price_date DATE,
    datasheet_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table: conduit_catalog (ท่อ PVC)
CREATE TABLE conduit_catalog (
    id SERIAL PRIMARY KEY,
    brand VARCHAR(100),
    type VARCHAR(50),  -- "PVC", "IMC", "EMT"
    size_inch VARCHAR(10) NOT NULL,  -- "1/2", "3/4", "1"
    inner_diameter_mm DECIMAL(6, 2),
    outer_diameter_mm DECIMAL(6, 2),
    length_m DECIMAL(5, 2) DEFAULT 4,  -- ปกติ 4 เมตร/เส้น
    price_per_piece DECIMAL(10, 2),
    price_date DATE,
    tis_standard VARCHAR(50),  -- "มอก. 982"
    created_at TIMESTAMP DEFAULT NOW()
);
```


***

## 🛠️ ส่วนที่ 2: แนวทางสร้าง Database

### **2.1 เลือกใช้ PostgreSQL + Supabase**

**เหตุผล:**
✅ PostgreSQL = มาตรฐานอุตสาหกรรม, รองรับ JSONB
✅ Supabase = ฟรี (Free Tier 500MB), มี API สำเร็จรูป, Real-time subscriptions
✅ เชื่อมกับ pandapower ได้ง่าย (Python → psycopg2 / Supabase Python Client)
✅ มี Row Level Security (RLS) ถ้าอยากควบคุมสิทธิ์

***

### **2.2 โครงสร้าง Database (Schema Design)**

```sql
-- ====================================
-- MCP CORE v2.0 DATABASE SCHEMA
-- ====================================

-- 1. TIS Standards (มาตรฐาน มอก.)
CREATE TABLE tis_standards (
    id SERIAL PRIMARY KEY,
    tis_number VARCHAR(50) UNIQUE NOT NULL,
    name_th TEXT NOT NULL,
    name_en TEXT,
    category VARCHAR(100),
    description TEXT,
    pdf_url TEXT,
    is_mandatory BOOLEAN DEFAULT FALSE,
    effective_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2. Wire Catalog (สาย)
CREATE TABLE wire_catalog (
    id SERIAL PRIMARY KEY,
    brand VARCHAR(100) NOT NULL,
    model VARCHAR(100),
    type VARCHAR(50) NOT NULL,  -- THW, NYY, CV
    size_mm2 DECIMAL(5, 2) NOT NULL,
    voltage_v INT NOT NULL,
    num_cores INT DEFAULT 1,
    insulation_type VARCHAR(50),  -- PVC, XLPE
    ampacity_a DECIMAL(6, 2) NOT NULL,
    ampacity_condition VARCHAR(100),  -- "อากาศ 30°C", "ฝังใน 40°C"
    resistance_ohm_per_km DECIMAL(10, 6),
    reactance_ohm_per_km DECIMAL(10, 6),
    price_per_m DECIMAL(10, 2),
    price_date DATE NOT NULL,
    region VARCHAR(50) DEFAULT 'bangkok',
    datasheet_url TEXT,
    tis_standard VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 3. Breaker Catalog
CREATE TABLE breaker_catalog (
    id SERIAL PRIMARY KEY,
    brand VARCHAR(100) NOT NULL,
    series VARCHAR(100),
    model VARCHAR(100) NOT NULL,
    rating_a INT NOT NULL,
    poles INT NOT NULL,
    curve_type VARCHAR(10),
    breaking_capacity_ka DECIMAL(6, 2) NOT NULL,
    voltage_v INT NOT NULL,
    phase_type VARCHAR(20),  -- "single", "three"
    has_rcbo BOOLEAN DEFAULT FALSE,
    rcbo_sensitivity_ma INT,
    rcbo_type VARCHAR(10),  -- "AC", "A", "B"
    price_thb DECIMAL(10, 2) NOT NULL,
    price_date DATE NOT NULL,
    region VARCHAR(50) DEFAULT 'bangkok',
    datasheet_url TEXT,
    iec_standard VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 4. Conduit Catalog
CREATE TABLE conduit_catalog (
    id SERIAL PRIMARY KEY,
    brand VARCHAR(100),
    type VARCHAR(50) NOT NULL,  -- PVC, IMC, EMT
    size_inch VARCHAR(10) NOT NULL,
    inner_diameter_mm DECIMAL(6, 2) NOT NULL,
    outer_diameter_mm DECIMAL(6, 2),
    cross_section_area_mm2 DECIMAL(10, 2),
    length_m DECIMAL(5, 2) DEFAULT 4,
    price_per_piece DECIMAL(10, 2) NOT NULL,
    price_date DATE NOT NULL,
    region VARCHAR(50) DEFAULT 'bangkok',
    tis_standard VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 5. Labor Rates (ค่าแรง)
CREATE TABLE labor_rates (
    id SERIAL PRIMARY KEY,
    task_type VARCHAR(100) NOT NULL,  -- "wire_installation", "breaker_installation"
    unit VARCHAR(50) NOT NULL,  -- "per_meter", "per_piece", "per_circuit"
    rate_thb DECIMAL(10, 2) NOT NULL,
    region VARCHAR(50) NOT NULL,
    effective_date DATE NOT NULL,
    source VARCHAR(100),  -- "TPSO", "Manual"
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 6. Material Price Index (ดัชนีราคา)
CREATE TABLE material_price_index (
    id SERIAL PRIMARY KEY,
    index_type VARCHAR(50) NOT NULL,  -- "CMI", "PPI", "K"
    category VARCHAR(100),  -- "construction", "electrical"
    index_value DECIMAL(10, 4) NOT NULL,
    base_year INT DEFAULT 2015,
    index_date DATE NOT NULL,
    source VARCHAR(100) NOT NULL,  -- "TPSO", "BOT"
    created_at TIMESTAMP DEFAULT NOW()
);

-- 7. Room Types & Requirements (ข้อกำหนดห้อง)
CREATE TABLE room_requirements (
    id SERIAL PRIMARY KEY,
    room_type VARCHAR(100) NOT NULL UNIQUE,  -- "kitchen", "bathroom", "bedroom"
    min_outlets INT,
    rcbo_required BOOLEAN DEFAULT FALSE,
    min_ip_rating VARCHAR(10),  -- "IP44", "IP65"
    forbidden_zones JSONB,  -- [0, 1, 2]
    special_notes TEXT,
    tis_reference VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert ตัวอย่าง
INSERT INTO room_requirements (room_type, rcbo_required, min_ip_rating, forbidden_zones, tis_reference) VALUES
('kitchen', TRUE, 'IP44', '[0, 1]', 'มอก. 2955'),
('bathroom', TRUE, 'IP44', '[0, 1, 2]', 'มอก. 2955'),
('bedroom', FALSE, NULL, '[]', NULL),
('living_room', FALSE, NULL, '[]', NULL);

-- Indexes
CREATE INDEX idx_wire_size ON wire_catalog(size_mm2);
CREATE INDEX idx_breaker_rating ON breaker_catalog(rating_a);
CREATE INDEX idx_conduit_size ON conduit_catalog(size_inch);
CREATE INDEX idx_price_date_wire ON wire_catalog(price_date);
CREATE INDEX idx_price_date_breaker ON breaker_catalog(price_date);
```


***

### **2.3 วิธีดึงข้อมูลเข้า Database**

#### **A. Web Scraping (Python)**

```python
import requests
from bs4 import BeautifulSoup
import psycopg2
from datetime import date

# Connect to PostgreSQL
conn = psycopg2.connect(
    host="db.supabase.co",
    database="postgres",
    user="postgres",
    password="your_password"
)
cur = conn.cursor()

# Scrape CTW Wire Prices (ตัวอย่าง)
url = "https://www.ctw.co.th/price-list"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# Parse table (ขึ้นกับโครงสร้าง HTML)
# ... (logic ขึ้นกับเว็บไซต์)

# Insert to Database
cur.execute("""
    INSERT INTO wire_catalog (brand, type, size_mm2, voltage_v, ampacity_a, price_per_m, price_date)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (brand, model) DO UPDATE SET price_per_m = EXCLUDED.price_per_m
""", ("CTW", "THW", 2.5, 600, 27, 18.0, date.today()))

conn.commit()
cur.close()
conn.close()
```


***

#### **B. PDF Parsing (PyPDF2 / pdfplumber)**

```python
import pdfplumber
import re

# Parse Schneider Catalog PDF
with pdfplumber.open("schneider_breaker_catalog.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        
        # Regex หาข้อมูล (ตัวอย่าง)
        matches = re.findall(r"iC60N (\d+)A.*?(\d+,\d+) บาท", text)
        
        for match in matches:
            rating = int(match[^0])
            price = float(match[^1].replace(',', ''))
            
            # Insert to DB
            cur.execute("""
                INSERT INTO breaker_catalog (brand, series, rating_a, poles, curve_type, price_thb, price_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, ("Schneider", "iC60N", rating, 1, "C", price, date.today()))
```


***

#### **C. Manual Entry (Admin Panel)**

สร้าง Admin Panel (Next.js + Supabase) ให้วิศวกรกรอกข้อมูลเอง:

```typescript
// components/AddWireForm.tsx
import { supabase } from '@/lib/supabase'

export default function AddWireForm() {
  const handleSubmit = async (e) => {
    e.preventDefault()
    
    const { data, error } = await supabase
      .from('wire_catalog')
      .insert([
        {
          brand: 'CTW',
          type: 'THW',
          size_mm2: 2.5,
          voltage_v: 600,
          ampacity_a: 27,
          price_per_m: 18.0,
          price_date: new Date()
        }
      ])
    
    if (error) console.error(error)
  }
  
  return <form onSubmit={handleSubmit}>...</form>
}
```


***

## 🎯 ส่วนที่ 3: Integration กับ MCP Core

### **3.1 Supabase Client (Python)**

```python
# supabase_client/catalog_manager.py

from supabase import create_client, Client
from typing import Dict, List, Optional
from datetime import date

class CatalogManager:
    """
    จัดการ Catalog จาก Supabase
    """
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase: Client = create_client(supabase_url, supabase_key)
    
    def get_wire_data(self, size_mm2: float, voltage_v: int = 600) -> Dict:
        """
        ดึงข้อมูลสายจาก Catalog
        """
        response = self.supabase.table('wire_catalog') \
            .select('*') \
            .eq('size_mm2', size_mm2) \
            .eq('voltage_v', voltage_v) \
            .order('price_date', desc=True) \
            .limit(1) \
            .execute()
        
        if response.data:
            return response.data[^0]
        else:
            raise ValueError(f"ไม่พบสาย {size_mm2} mm² ใน Catalog")
    
    def get_available_wires(self, min_size_mm2: float = 1.5) -> List[Dict]:
        """
        ดึงรายการสายทั้งหมดที่ใหญ่กว่า min_size
        """
        response = self.supabase.table('wire_catalog') \
            .select('*') \
            .gte('size_mm2', min_size_mm2) \
            .order('size_mm2', asc=True) \
            .execute()
        
        return response.data
    
    def get_breaker(self, rating_a: int, brand: str = "Schneider") -> Dict:
        """
        ดึงข้อมูล Breaker
        """
        response = self.supabase.table('breaker_catalog') \
            .select('*') \
            .eq('brand', brand) \
            .eq('rating_a', rating_a) \
            .order('price_date', desc=True) \
            .limit(1) \
            .execute()
        
        if response.data:
            return response.data[^0]
        else:
            raise ValueError(f"ไม่พบ Breaker {rating_a}A ยี่ห้อ {brand}")
    
    def get_room_requirements(self, room_type: str) -> Dict:
        """
        ดึงข้อกำหนดห้อง
        """
        response = self.supabase.table('room_requirements') \
            .select('*') \
            .eq('room_type', room_type) \
            .single() \
            .execute()
        
        return response.data if response.data else {}
```


***

## 📋 สรุปแนวทาง

| แหล่งข้อมูล | วิธีดึง | ความถี่อัพเดท | ความยาก |
| :-- | :-- | :-- | :-- |
| **TISI (มอก.)** | Web Scraping | ปีละ 2-3 ครั้ง | ⭐⭐ |
| **TPSO/BOT (ดัชนี K, CMI)** | Web Scraping / CSV | เดือนละ 1 ครั้ง | ⭐⭐ |
| **PDF Catalogs** | PDF Parsing | ปีละ 1-2 ครั้ง | ⭐⭐⭐ |
| **Manual Entry** | Admin Panel | ตามต้องการ | ⭐ |

**แนะนำ:**

1. ✅ **เริ่มจาก Manual Entry** (Admin Panel) → รวดเร็วที่สุด
2. ✅ **ค่อย ๆ เพิ่ม Web Scraping** (TPSO, TISI) → Automate
3. ✅ **ใช้ Supabase Free Tier** → เริ่มต้นฟรี 500MB
4. ✅ **Update ราคาทุก 3-6 เดือน** → ไม่ต้องบ่อยเกินไป

**นายท่าน จะให้ Volta ออกแบบ Admin Panel หรือเขียน Scraper ให้ไหมคะ?** 🚀⚡✨
<span style="display:none">[^12][^13][^14][^15][^16][^17][^18][^19][^20]</span>

<div align="center">⁂</div>

[^1]: https://appdb.tisi.go.th/tis_dev/p3_tis/p3tis.php

[^2]: https://appdb.tisi.go.th/tis_dev/p3_tis/p3tis.php?data=A

[^3]: https://a.tisi.go.th/t/?n=7712

[^4]: https://service.tisi.go.th/tisi-standard-shop/item/tis/4565

[^5]: https://www.tpso.go.th/economic-data/price-struct

[^6]: https://www.bot.or.th/en/statistics/real-sector.html

[^7]: https://www.ceicdata.com/en/thailand/construction-price-index/construction-materials-price-index-cmi-2015100

[^8]: https://www.statista.com/statistics/1086833/thailand-producer-price-index-for-construction-products/

[^9]: https://ctw.co.th/wp-content/uploads/2022/04/CTW-Pice-list-2022.pdf

[^10]: https://thaiyazaki-electricwire.co.th/images/downloadcatalog/_20211143063943New%20Yazaki%20Price%20List.pdf

[^11]: https://www.tmkelectrics.com/uploads/6269/files/PDF/CATALOGUE TMK - ALL_compressed.pdf

[^12]: https://www.api.org/products-and-services/standards/digital-catalog

[^13]: https://lntsufin.com/product/ador-supabase-x-plus-2-5-mm-e7018-welding-electrodes-20-kg/16832-1263

[^14]: https://www.api-equipment.com

[^15]: https://www.scribd.com/doc/296138604/Material-1

[^16]: https://www.apiadvance.com/สินค้า

[^17]: https://electric-sql.com/docs/integrations/supabase

[^18]: https://www.thaipnb.co.th/sungo-valves-group-co-ltd/api-lubricated-plug-valve/

[^19]: https://www.sirichaielectric.com/pricelist.php

[^20]: https://supabase.com/partners/integrations/electricsql

