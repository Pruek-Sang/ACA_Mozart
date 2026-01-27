"""
Price Scraper - ดึงราคาจากเว็บจริง
รองรับ: ThaiWatsadu, HomePro, Lazada, Shopee

Usage:
    python price_scraper.py --update-all
    python price_scraper.py --device "COMP-OUTLET-16A"
"""

import csv
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Try to import scraping libraries
try:
    import requests
    from bs4 import BeautifulSoup
    HAS_SCRAPING = True
except ImportError:
    HAS_SCRAPING = False
    print("⚠️ Install: pip install requests beautifulsoup4")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PriceResult:
    device_code: str
    source: str
    price: float
    unit: str
    url: str
    scraped_at: str


class PriceScraper:
    """Scrape prices from Thai e-commerce websites."""
    
    # Map device codes to search terms
    # Updated 2026-01-27: Added 3-Phase, Solar, EV components
    SEARCH_TERMS = {
        # === BASIC COMPONENTS ===
        "COMP-OUTLET-16A": ["เต้ารับ 16A", "ปลั๊กไฟ 16A", "outlet 16A"],
        "COMP-DOWNLIGHT-9W": ["ดาวน์ไลท์ 9W", "downlight 9W LED"],
        "COMP-CEILING-24W": ["โคมไฟเพดาน 24W", "ceiling light 24W"],
        "COMP-SWITCH-1GANG": ["สวิตช์ไฟ 1 ช่อง", "light switch 1 gang"],
        "COMP-JUNCTION-BOX": ["กล่องพักสาย", "junction box"],
        
        # === 1-PHASE BREAKERS ===
        "CB-1P-16A": ["เบรกเกอร์ 16A", "MCB 16A 1P"],
        "CB-1P-20A": ["เบรกเกอร์ 20A", "MCB 20A 1P"],
        "CB-1P-32A": ["เบรกเกอร์ 32A", "MCB 32A 1P"],
        "RCBO-1P-20A": ["RCBO 20A", "เบรกเกอร์กันดูด 20A"],
        "RCBO-1P-32A": ["RCBO 32A", "เบรกเกอร์กันดูด 32A"],
        
        # === 3-PHASE BREAKERS ===
        "CB-3P-20A": ["เบรกเกอร์ 3 เฟส 20A", "MCB 3P 20A"],
        "CB-3P-32A": ["เบรกเกอร์ 3 เฟส 32A", "MCB 3P 32A"],
        "CB-3P-50A": ["เบรกเกอร์ 3 เฟส 50A", "MCB 3P 50A"],
        "CB-3P-63A": ["เบรกเกอร์ 3 เฟส 63A", "MCB 3P 63A"],
        "CB-3P-100A": ["MCCB 3P 100A", "เบรกเกอร์ 3 เฟส 100A"],
        "RCBO-3P-32A": ["RCBO 3P 32A", "เบรกเกอร์กันดูด 3 เฟส 32A"],
        "RCBO-3P-40A": ["RCBO 3P 40A", "เบรกเกอร์กันดูด 3 เฟส 40A"],
        
        # === WIRES (1-Phase) ===
        "WIRE-THW-2.5": ["สาย THW 2.5", "สายไฟ 2.5 sq.mm"],
        "WIRE-THW-4.0": ["สาย THW 4.0", "สายไฟ 4 sq.mm"],
        "WIRE-THW-6.0": ["สาย THW 6", "สายไฟ 6 sq.mm"],
        "WIRE-THW-10": ["สาย THW 10", "สายไฟ 10 sq.mm"],
        
        # === WIRES (3-Phase / Heavy) ===
        "WIRE-THW-16": ["สาย THW 16", "สายไฟ 16 sq.mm"],
        "WIRE-THW-25": ["สาย THW 25", "สายไฟ 25 sq.mm"],
        "WIRE-THW-35": ["สาย THW 35", "สายไฟ 35 sq.mm"],
        "WIRE-THW-50": ["สาย THW 50", "สายไฟ 50 sq.mm"],
        "CABLE-NYY-3C-10": ["สาย NYY 3x10", "NYY 3 core 10"],
        "CABLE-NYY-3C-16": ["สาย NYY 3x16", "NYY 3 core 16"],
        "CABLE-NYY-3C-25": ["สาย NYY 3x25", "NYY 3 core 25"],
        
        # === SOLAR COMPONENTS ===
        "SOLAR-MONO-400W": ["แผงโซล่าเซลล์ 400W", "solar panel 400W mono"],
        "SOLAR-MONO-550W": ["แผงโซล่าเซลล์ 550W", "solar panel 550W mono"],
        "INVERTER-HYBRID-3KW": ["อินเวอร์เตอร์ 3kW", "hybrid inverter 3kW"],
        "INVERTER-HYBRID-5KW": ["อินเวอร์เตอร์ 5kW", "hybrid inverter 5kW"],
        "INVERTER-HYBRID-8KW": ["อินเวอร์เตอร์ 8kW", "hybrid inverter 8kW"],
        "INVERTER-HYBRID-10KW": ["อินเวอร์เตอร์ 10kW", "hybrid inverter 10kW"],
        "INVERTER-ONGRID-5KW": ["อินเวอร์เตอร์ on-grid 5kW", "grid-tie inverter 5kW"],
        "INVERTER-ONGRID-10KW": ["อินเวอร์เตอร์ on-grid 10kW", "grid-tie inverter 10kW"],
        "DC-DISCONNECT-2P": ["สวิทช์ตัดไฟ DC 2P", "DC isolator 2P"],
        "DC-DISCONNECT-4P": ["สวิทช์ตัดไฟ DC 4P", "DC isolator 4P"],
        "SPD-DC-TYPE2": ["กันฟ้าผ่า DC Type 2", "SPD DC Type II"],
        "SPD-AC-TYPE2": ["กันฟ้าผ่า AC Type 2", "SPD AC Type II"],
        "CABLE-DC-4MM": ["สาย DC 4mm solar", "PV cable 4mm"],
        "CABLE-DC-6MM": ["สาย DC 6mm solar", "PV cable 6mm"],
        "MC4-PAIR": ["MC4 connector pair", "ขั้วต่อ MC4"],
        
        # === EV CHARGER ===
        "EV-CHARGER-7KW": ["EV charger 7kW", "ที่ชาร์จรถยนต์ไฟฟ้า 7kW", "wallbox 7kW"],
        "EV-CHARGER-11KW": ["EV charger 11kW", "ที่ชาร์จรถยนต์ไฟฟ้า 11kW"],
        "EV-CHARGER-22KW": ["EV charger 22kW", "ที่ชาร์จรถยนต์ไฟฟ้า 22kW"],
        
        # === CONSUMER UNITS ===
        "CONSUMER-UNIT-12": ["ตู้คอนซูเมอร์ 12 ช่อง", "consumer unit 12 way"],
        "CONSUMER-UNIT-18": ["ตู้คอนซูเมอร์ 18 ช่อง", "consumer unit 18 way"],
        "CONSUMER-UNIT-24": ["ตู้คอนซูเมอร์ 24 ช่อง", "consumer unit 24 way"],
        "CU-3P-12WAY": ["ตู้คอนซูเมอร์ 3 เฟส 12 ช่อง", "3 phase DB 12 way"],
        "CU-3P-18WAY": ["ตู้คอนซูเมอร์ 3 เฟส 18 ช่อง", "3 phase DB 18 way"],
        "CU-3P-24WAY": ["ตู้คอนซูเมอร์ 3 เฟส 24 ช่อง", "3 phase DB 24 way"],
        
        # === GROUNDING ===
        "COMP-GROUND-ROD": ["หลักดิน 2.4 เมตร", "ground rod 8ft"],
        "WIRE-GROUND-10": ["สายดิน 10 sq.mm", "ground wire 10"],
        "WIRE-GROUND-16": ["สายดิน 16 sq.mm", "ground wire 16"],
        
        # === CONDUIT ===
        "CONDUIT-EMT-1/2": ["ท่อ EMT 1/2", "EMT conduit 1/2 inch"],
        "CONDUIT-EMT-3/4": ["ท่อ EMT 3/4", "EMT conduit 3/4 inch"],
        "CONDUIT-EMT-1": ["ท่อ EMT 1 นิ้ว", "EMT conduit 1 inch"],
    }
    
    def __init__(self, output_path: str):
        self.output_path = output_path
        self.results: List[PriceResult] = []
        self.session = requests.Session() if HAS_SCRAPING else None
        
        if self.session:
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
    
    def scrape_thaiwatsadu(self, search_term: str) -> Optional[Dict[str, Any]]:
        """Scrape ThaiWatsadu website - Updated 2026-01-27 with better headers."""
        if not HAS_SCRAPING:
            return None
            
        try:
            import re
            from urllib.parse import quote
            
            # ThaiWatsadu blocks simple requests, need better headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': 'https://www.thaiwatsadu.com/',
            }
            
            url = f"https://www.thaiwatsadu.com/th/search?q={quote(search_term)}"
            response = self.session.get(url, timeout=15, headers=headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try data-price attribute
                product = soup.find(attrs={'data-price': True})
                if product:
                    price = float(product.get('data-price', '0').replace(',', ''))
                    if price > 0:
                        return {'price': price, 'url': url, 'source': 'ThaiWatsadu'}
                
                # Try price class patterns
                price_elems = soup.find_all(class_=re.compile(r'price', re.I))
                for elem in price_elems:
                    text = elem.get_text(strip=True)
                    match = re.search(r'[\d,]+(?:\.\d+)?', text.replace('฿', ''))
                    if match:
                        price = float(match.group().replace(',', ''))
                        if price > 10:
                            return {'price': price, 'url': url, 'source': 'ThaiWatsadu'}
                            
        except Exception as e:
            logger.warning(f"ThaiWatsadu scrape failed for '{search_term}': {e}")
        
        return None
    
    def scrape_globalhouse(self, search_term: str) -> Optional[Dict[str, Any]]:
        """Scrape GlobalHouse website - Added 2026-01-27."""
        if not HAS_SCRAPING:
            return None
            
        try:
            import re
            from urllib.parse import quote
            
            url = f"https://www.globalhouse.co.th/search?q={quote(search_term)}"
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try data-price attribute
                product = soup.find(attrs={'data-price': True})
                if product:
                    price = float(product.get('data-price', '0').replace(',', ''))
                    if price > 0:
                        return {'price': price, 'url': url, 'source': 'GlobalHouse'}
                
                # Try price patterns
                price_elems = soup.find_all(class_=re.compile(r'price', re.I))
                for elem in price_elems:
                    text = elem.get_text(strip=True)
                    match = re.search(r'[\d,]+(?:\.\d+)?', text.replace('฿', ''))
                    if match:
                        price = float(match.group().replace(',', ''))
                        if price > 10:
                            return {'price': price, 'url': url, 'source': 'GlobalHouse'}
                            
        except Exception as e:
            logger.warning(f"GlobalHouse scrape failed for '{search_term}': {e}")
        
        return None
    
    def scrape_homepro(self, search_term: str) -> Optional[Dict[str, Any]]:
        """Scrape HomePro website - Updated 2026-01-27 for current HTML structure."""
        if not HAS_SCRAPING:
            return None
            
        try:
            import re
            from urllib.parse import quote
            
            url = f"https://www.homepro.co.th/search?q={quote(search_term)}"
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Method 1: Try data-price attribute (most reliable)
                product = soup.find(attrs={'data-price': True})
                if product:
                    price_str = product.get('data-price', '0')
                    price = float(price_str.replace(',', ''))
                    if price > 0:
                        return {
                            'price': price,
                            'url': url,
                            'source': 'HomePro'
                        }
                
                # Method 2: Find price class with numeric value
                price_elems = soup.find_all(class_=re.compile(r'price', re.I))
                for elem in price_elems:
                    text = elem.get_text(strip=True)
                    # Extract number from text like "164" or "3,419"
                    match = re.search(r'[\d,]+(?:\.\d+)?', text.replace('฿', ''))
                    if match:
                        price = float(match.group().replace(',', ''))
                        if price > 10:  # Ignore tiny numbers
                            return {
                                'price': price,
                                'url': url,
                                'source': 'HomePro'
                            }
                
                # Method 3: JSON-LD fallback
                script = soup.find('script', type='application/ld+json')
                if script:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'offers' in data:
                        price = float(data['offers'].get('price', 0))
                        if price > 0:
                            return {
                                'price': price,
                                'url': url,
                                'source': 'HomePro'
                            }
                            
        except Exception as e:
            logger.warning(f"HomePro scrape failed for '{search_term}': {e}")
        
        return None
    
    def scrape_lazada(self, search_term: str) -> Optional[Dict[str, Any]]:
        """Scrape Lazada via their search API."""
        if not HAS_SCRAPING:
            return None
            
        try:
            # Lazada has anti-bot, this is simplified
            url = f"https://www.lazada.co.th/catalog/?q={search_term}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                # Lazada embeds JSON in page
                soup = BeautifulSoup(response.text, 'html.parser')
                script = soup.find('script', text=lambda t: t and 'window.pageData' in t)
                
                if script:
                    # Parse the embedded JSON (simplified)
                    # In reality, need more complex parsing
                    return {
                        'price': 0,  # Would parse from JSON
                        'url': url,
                        'source': 'Lazada'
                    }
        except Exception as e:
            logger.warning(f"Lazada scrape failed: {e}")
        
        return None
    
    def scrape_device(self, device_code: str) -> List[PriceResult]:
        """Scrape all sources for a device - Updated 2026-01-27 with GlobalHouse."""
        results = []
        search_terms = self.SEARCH_TERMS.get(device_code, [device_code])
        
        for term in search_terms:
            # Try each source - ordered by reliability
            for scraper, source in [
                (self.scrape_homepro, 'HomePro'),       # Most reliable
                (self.scrape_globalhouse, 'GlobalHouse'), # Good fallback
                (self.scrape_thaiwatsadu, 'ThaiWatsadu'), # Often blocks
                (self.scrape_lazada, 'Lazada'),         # Anti-bot heavy
            ]:
                result = scraper(term)
                if result and result['price'] > 0:
                    results.append(PriceResult(
                        device_code=device_code,
                        source=result['source'],
                        price=result['price'],
                        unit='set',
                        url=result['url'],
                        scraped_at=datetime.now().strftime('%Y-%m-%d')
                    ))
                    break  # Got price from this source, move to next
            
            time.sleep(1)  # Be polite to servers
        
        return results
    
    def update_all(self):
        """Update prices for all known devices."""
        all_results = []
        
        for device_code in self.SEARCH_TERMS.keys():
            logger.info(f"Scraping {device_code}...")
            results = self.scrape_device(device_code)
            all_results.extend(results)
            time.sleep(2)  # Rate limiting
        
        self.save_results(all_results)
        return all_results
    
    def save_results(self, results: List[PriceResult]):
        """Save results to CSV."""
        with open(self.output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['device_code', 'source', 'price_thb', 'unit', 'url', 'last_updated'])
            
            for r in results:
                writer.writerow([r.device_code, r.source, r.price, r.unit, r.url, r.scraped_at])
        
        logger.info(f"Saved {len(results)} prices to {self.output_path}")


# === MOCK MODE (ใช้ตอนเว็บ block หรือ test) ===

class MockPriceScraper(PriceScraper):
    """Mock scraper that returns realistic fake prices for testing."""
    
    # Updated 2026-01-27: Added 3-Phase, Solar, EV components with realistic Thai prices
    MOCK_PRICES = {
        # === BASIC COMPONENTS ===
        "COMP-OUTLET-16A": [
            ("ThaiWatsadu", 120.0),
            ("HomePro", 135.0),
            ("Lazada", 89.0),
            ("Shopee", 95.0),
        ],
        "COMP-DOWNLIGHT-9W": [
            ("ThaiWatsadu", 250.0),
            ("HomePro", 280.0),
            ("Shopee", 199.0),
        ],
        "COMP-SWITCH-1GANG": [
            ("Panasonic", 85.0),
            ("Haco", 45.0),
            ("Lazada", 35.0),
        ],
        "COMP-JUNCTION-BOX": [
            ("ThaiWatsadu", 25.0),
            ("HomePro", 30.0),
            ("Lazada", 18.0),
        ],
        
        # === 1-PHASE BREAKERS ===
        "CB-1P-16A": [
            ("Schneider", 150.0),
            ("ABB", 148.0),
            ("Lazada", 120.0),
        ],
        "CB-1P-20A": [
            ("Schneider", 155.0),
            ("ABB", 152.0),
            ("Lazada", 125.0),
        ],
        "CB-1P-32A": [
            ("Schneider", 180.0),
            ("ABB", 175.0),
            ("Lazada", 145.0),
        ],
        "RCBO-1P-20A": [
            ("Schneider", 650.0),
            ("ABB", 620.0),
            ("Lazada", 450.0),
        ],
        "RCBO-1P-32A": [
            ("Schneider", 750.0),
            ("ABB", 720.0),
            ("Lazada", 550.0),
        ],
        
        # === 3-PHASE BREAKERS ===
        "CB-3P-20A": [
            ("Schneider", 450.0),
            ("ABB", 420.0),
            ("Lazada", 380.0),
        ],
        "CB-3P-32A": [
            ("Schneider", 550.0),
            ("ABB", 520.0),
            ("Lazada", 480.0),
        ],
        "CB-3P-50A": [
            ("Schneider", 750.0),
            ("ABB", 720.0),
            ("Lazada", 650.0),
        ],
        "CB-3P-63A": [
            ("Schneider", 950.0),
            ("ABB", 920.0),
            ("Lazada", 850.0),
        ],
        "CB-3P-100A": [
            ("Schneider MCCB", 2500.0),
            ("ABB MCCB", 2400.0),
            ("LS MCCB", 2200.0),
        ],
        "RCBO-3P-32A": [
            ("Schneider", 1850.0),
            ("ABB", 1780.0),
            ("Lazada", 1450.0),
        ],
        "RCBO-3P-40A": [
            ("Schneider", 2100.0),
            ("ABB", 2000.0),
            ("Lazada", 1650.0),
        ],
        
        # === WIRES (per meter) ===
        "WIRE-THW-2.5": [
            ("Yazaki", 12.50),
            ("Phelps Dodge", 14.00),
            ("BCC", 11.80),
        ],
        "WIRE-THW-4.0": [
            ("Yazaki", 18.0),
            ("Phelps Dodge", 20.0),
            ("BCC", 17.0),
        ],
        "WIRE-THW-6.0": [
            ("Yazaki", 28.0),
            ("Phelps Dodge", 30.0),
            ("BCC", 26.0),
        ],
        "WIRE-THW-10": [
            ("Yazaki", 45.0),
            ("Phelps Dodge", 48.0),
            ("BCC", 42.0),
        ],
        "WIRE-THW-16": [
            ("Yazaki", 70.0),
            ("Phelps Dodge", 75.0),
            ("BCC", 65.0),
        ],
        "WIRE-THW-25": [
            ("Yazaki", 110.0),
            ("Phelps Dodge", 115.0),
            ("BCC", 100.0),
        ],
        "WIRE-THW-35": [
            ("Yazaki", 150.0),
            ("Phelps Dodge", 160.0),
            ("BCC", 140.0),
        ],
        "WIRE-THW-50": [
            ("Yazaki", 210.0),
            ("Phelps Dodge", 220.0),
            ("BCC", 195.0),
        ],
        "CABLE-NYY-3C-10": [
            ("Thai Yazaki", 85.0),
            ("BCC", 80.0),
        ],
        "CABLE-NYY-3C-16": [
            ("Thai Yazaki", 120.0),
            ("BCC", 115.0),
        ],
        "CABLE-NYY-3C-25": [
            ("Thai Yazaki", 180.0),
            ("BCC", 170.0),
        ],
        
        # === SOLAR COMPONENTS ===
        "SOLAR-MONO-400W": [
            ("JA Solar", 4500.0),
            ("LONGi", 4800.0),
            ("Canadian Solar", 4600.0),
        ],
        "SOLAR-MONO-550W": [
            ("JA Solar", 5500.0),
            ("LONGi", 5800.0),
            ("Trina Solar", 5600.0),
        ],
        "INVERTER-HYBRID-3KW": [
            ("Growatt", 28000.0),
            ("Deye", 25000.0),
            ("Sofar", 26000.0),
        ],
        "INVERTER-HYBRID-5KW": [
            ("Huawei", 45000.0),
            ("Growatt", 35000.0),
            ("Deye", 32000.0),
        ],
        "INVERTER-HYBRID-8KW": [
            ("Huawei", 65000.0),
            ("Growatt", 52000.0),
            ("Deye", 48000.0),
        ],
        "INVERTER-HYBRID-10KW": [
            ("Huawei", 78000.0),
            ("Growatt", 62000.0),
            ("Deye", 58000.0),
        ],
        "INVERTER-ONGRID-5KW": [
            ("Huawei", 35000.0),
            ("Growatt", 28000.0),
            ("Sungrow", 30000.0),
        ],
        "INVERTER-ONGRID-10KW": [
            ("Huawei", 55000.0),
            ("Growatt", 45000.0),
            ("Sungrow", 48000.0),
        ],
        "DC-DISCONNECT-2P": [
            ("ZJBENY", 850.0),
            ("Tongou", 650.0),
        ],
        "DC-DISCONNECT-4P": [
            ("ZJBENY", 1200.0),
            ("Tongou", 950.0),
        ],
        "SPD-DC-TYPE2": [
            ("DEHN", 2500.0),
            ("OBO Bettermann", 2200.0),
            ("Tongou", 1200.0),
        ],
        "SPD-AC-TYPE2": [
            ("DEHN", 1800.0),
            ("OBO Bettermann", 1600.0),
            ("Schneider", 1400.0),
        ],
        "CABLE-DC-4MM": [
            ("Helukabel", 35.0),
            ("Generic Solar", 25.0),
        ],
        "CABLE-DC-6MM": [
            ("Helukabel", 45.0),
            ("Generic Solar", 35.0),
        ],
        "MC4-PAIR": [
            ("Amphenol", 45.0),
            ("Generic", 25.0),
        ],
        
        # === EV CHARGER ===
        "EV-CHARGER-7KW": [
            ("Delta", 25000.0),
            ("ABB", 28000.0),
            ("Wallbox", 22000.0),
        ],
        "EV-CHARGER-11KW": [
            ("Delta", 35000.0),
            ("ABB", 38000.0),
            ("Wallbox", 32000.0),
        ],
        "EV-CHARGER-22KW": [
            ("Delta", 55000.0),
            ("ABB", 60000.0),
            ("Wallbox", 52000.0),
        ],
        
        # === CONSUMER UNITS ===
        "CONSUMER-UNIT-12": [
            ("Schneider", 1500.0),
            ("ABB", 1400.0),
            ("Haco", 850.0),
        ],
        "CONSUMER-UNIT-18": [
            ("Schneider", 2200.0),
            ("ABB", 2100.0),
            ("Haco", 1200.0),
        ],
        "CONSUMER-UNIT-24": [
            ("Schneider", 2800.0),
            ("ABB", 2700.0),
            ("Haco", 1600.0),
        ],
        "CU-3P-12WAY": [
            ("Schneider", 3500.0),
            ("ABB", 3400.0),
            ("Haco", 2500.0),
        ],
        "CU-3P-18WAY": [
            ("Schneider", 4500.0),
            ("ABB", 4400.0),
            ("Haco", 3500.0),
        ],
        "CU-3P-24WAY": [
            ("Schneider", 5500.0),
            ("ABB", 5400.0),
            ("Haco", 4500.0),
        ],
        
        # === GROUNDING ===
        "COMP-GROUND-ROD": [
            ("Thai Standard", 450.0),
            ("Generic", 350.0),
        ],
        "WIRE-GROUND-10": [
            ("Yazaki Green", 45.0),
            ("BCC", 40.0),
        ],
        "WIRE-GROUND-16": [
            ("Yazaki Green", 70.0),
            ("BCC", 65.0),
        ],
        
        # === CONDUIT (per 3m stick) ===
        "CONDUIT-EMT-1/2": [
            ("ThaiWatsadu", 85.0),
            ("HomePro", 90.0),
        ],
        "CONDUIT-EMT-3/4": [
            ("ThaiWatsadu", 110.0),
            ("HomePro", 115.0),
        ],
        "CONDUIT-EMT-1": [
            ("ThaiWatsadu", 145.0),
            ("HomePro", 150.0),
        ],
    }
    
    def scrape_device(self, device_code: str) -> List[PriceResult]:
        """Return mock prices."""
        results = []
        mock_data = self.MOCK_PRICES.get(device_code, [])
        
        for source, price in mock_data:
            results.append(PriceResult(
                device_code=device_code,
                source=source,
                price=price,
                unit='set' if 'WIRE' not in device_code else 'meter',
                url=f"https://mock.example.com/{device_code}",
                scraped_at=datetime.now().strftime('%Y-%m-%d')
            ))
        
        return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape prices from Thai e-commerce')
    parser.add_argument('--update-all', action='store_true', help='Update all prices')
    parser.add_argument('--device', type=str, help='Scrape specific device')
    parser.add_argument('--mock', action='store_true', help='Use mock data (for testing)')
    parser.add_argument('--output', type=str, default='prices_scraped.csv', help='Output file')
    
    args = parser.parse_args()
    
    # Use mock scraper if requested or if scraping libs not available
    if args.mock or not HAS_SCRAPING:
        print("🔧 Using MOCK mode (no real web scraping)")
        scraper = MockPriceScraper(args.output)
    else:
        scraper = PriceScraper(args.output)
    
    if args.update_all:
        results = scraper.update_all()
        print(f"✅ Updated {len(results)} prices")
    elif args.device:
        results = scraper.scrape_device(args.device)
        for r in results:
            print(f"{r.source}: ฿{r.price:.2f}")
    else:
        parser.print_help()
