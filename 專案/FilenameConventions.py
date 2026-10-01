import traceback
from playwright.sync_api import sync_playwright
from db import save_hotels

def scrape_booking():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        
        page = context.new_page()

        try:
            print("1. 連線至 Booking.com 搜尋頁...")
            target_url = (
                "https://www.booking.com/searchresults.zh-tw.html?"
                "ss=%E8%87%BA%E5%8C%97"
                "&checkin=2026-11-01"
                "&checkout=2026-11-02"
                "&group_adults=2"
                "&no_rooms=1"
            )
            page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000)

            page.keyboard.press("Escape")
            page.wait_for_timeout(1000)

            print("2. 模擬滾動載入完整資料...")
            page.wait_for_selector('div[data-testid="property-card"]', timeout=30000)
            
            for _ in range(3):
                page.evaluate("window.scrollBy(0, 600)")
                page.wait_for_timeout(800)

            hotels = page.query_selector_all('div[data-testid="property-card"]')
            print(f"✅ 找到 {len(hotels)} 間飯店，開始解析與清理資料...")

            scraped_data = []
            for hotel in hotels[:10]:  # 擷取前 10 間做示範
                # 抓名稱
                title_elem = hotel.query_selector('div[data-testid="title"]')
                title = title_elem.inner_text().strip() if title_elem else "未知飯店"

                # 抓價格
                price_selectors = [
                    'span[data-testid="price-and-discounted-price"]',
                    'div[data-testid="price-and-discounted-price"]',
                    'span[data-testid="price"]',
                    'span[class*="price"]'
                ]
                price = "價格未標示"
                for selector in price_selectors:
                    price_elem = hotel.query_selector(selector)
                    if price_elem and price_elem.inner_text().strip():
                        raw_text = price_elem.inner_text().strip()
                        price = " ".join(raw_text.split())
                        break

                # 抓評分
                rating_elem = hotel.query_selector('div[aria-label*="評分"]') or hotel.query_selector('div[data-testid="review-score"]')
                rating = None
                if rating_elem:
                    rating_text = rating_elem.inner_text().strip().split('\n')[0]
                    rating = ''.join(c for c in rating_text if c.isdigit() or c == '.')

                scraped_data.append({
                    "title": title,
                    "price": price,
                    "rating": rating
                })

            # 3. 儲存入 SQLite 資料庫
            count = save_hotels(scraped_data)
            print(f"\n🎉 成功處理並存入 {count} 筆飯店資料至 SQLite 資料庫！")

        except Exception as e:
            print("\n❌ 發生錯誤：")
            traceback.print_exc()

        finally:
            if not page.is_closed():
                browser.close()

if __name__ == "__main__":
    scrape_booking()