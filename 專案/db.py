import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'hotels.db')

def init_db():
    """初始化資料庫與建立表格"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hotels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            price_raw TEXT,
            price_num INTEGER,
            rating REAL,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_hotels(hotel_list):
    """清理資料並寫入資料庫"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    inserted_count = 0
    for h in hotel_list:
        # 1. 價格資料清理：擷取數字 (例如 'TWD 4,500' -> 4500)
        raw_price = h.get('price', '')
        clean_price = None
        if raw_price and raw_price != '價格未標示':
            digits = ''.join(filter(str.isdigit, raw_price))
            if digits:
                clean_price = int(digits)

        # 2. 評分資料清理 (例如 '8.5' -> 8.5)
        raw_rating = h.get('rating', None)
        clean_rating = None
        if raw_rating:
            try:
                clean_rating = float(raw_rating)
            except ValueError:
                pass

        # 寫入資料庫
        cursor.execute('''
            INSERT INTO hotels (title, price_raw, price_num, rating)
            VALUES (?, ?, ?, ?)
        ''', (h['title'], raw_price, clean_price, clean_rating))
        inserted_count += 1

    conn.commit()
    conn.close()
    return inserted_count