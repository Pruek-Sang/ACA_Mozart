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
    SEARCH_TERMS = {
        "COMP-OUTLET-16A": ["เต้ารับ 16A", "ปลั๊กไฟ 16A", "outlet 16A"],
        "COMP-DOWNLIGHT-9W": ["ดาวน์ไลท์ 9W", "downlight 9W LED"],
        "COMP-CEILING-24W": ["โคมไฟเพดาน 24W", "ceiling light 24W"],
        "CB-1P-16A": ["เบรกเกอร์ 16A", "MCB 16A", "circuit breaker 16A"],
        "WIRE-THW-2.5": ["สาย THW 2.5", "สายไฟ 2.5 sq.mm"],
        "WIRE-THW-4.0": ["สาย THW 4.0", "สายไฟ 4 sq.mm"],
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
        """Scrape ThaiWatsadu website."""
        if not HAS_SCRAPING:
            return None
            
        try:
            # ThaiWatsadu search URL
            url = f"https://www.thaiwatsadu.com/th/search?q={search_term}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find first product (adjust selectors based on actual site)
                product = soup.find('div', class_='product-item')
                if product:
                    price_elem = product.find('span', class_='price')
                    if price_elem:
                        price_text = price_elem.text.strip()
                        # Parse price like "฿120.00"
                        price = float(price_text.replace('฿', '').replace(',', ''))
                        
                        return {
                            'price': price,
                            'url': url,
                            'source': 'ThaiWatsadu'
                        }
        except Exception as e:
            logger.warning(f"ThaiWatsadu scrape failed: {e}")
        
        return None
    
    def scrape_homepro(self, search_term: str) -> Optional[Dict[str, Any]]:
        """Scrape HomePro website."""
        if not HAS_SCRAPING:
            return None
            
        try:
            url = f"https://www.homepro.co.th/search?q={search_term}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # HomePro uses JSON-LD for product data
                script = soup.find('script', type='application/ld+json')
                if script:
                    data = json.loads(script.string)
                    if 'offers' in data:
                        price = float(data['offers']['price'])
                        return {
                            'price': price,
                            'url': url,
                            'source': 'HomePro'
                        }
        except Exception as e:
            logger.warning(f"HomePro scrape failed: {e}")
        
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
        """Scrape all sources for a device."""
        results = []
        search_terms = self.SEARCH_TERMS.get(device_code, [device_code])
        
        for term in search_terms:
            # Try each source
            for scraper, source in [
                (self.scrape_thaiwatsadu, 'ThaiWatsadu'),
                (self.scrape_homepro, 'HomePro'),
                (self.scrape_lazada, 'Lazada'),
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
    
    MOCK_PRICES = {
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
        "CB-1P-16A": [
            ("Schneider Official", 150.0),
            ("ABB Official", 148.0),
            ("Lazada", 120.0),
        ],
        "WIRE-THW-2.5": [
            ("Yazaki", 12.50),
            ("Phelps Dodge", 14.00),
            ("BCC", 11.80),
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
