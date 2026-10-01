import sqlite3
import os
from openai import OpenAI

DB_PATH = os.path.join(os.path.dirname(__file__), 'hotels.db')

def fetch_hotels_from_db(max_price=None, min_rating=None):
    """從 SQLite 撈出符合條件的飯店資料"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = "SELECT title, price_num, rating FROM hotels WHERE 1=1"
    params = []
    
    if max_price:
        query += " AND price_num <= ?"
        params.append(max_price)
    if min_rating:
        query += " AND rating >= ?"
        params.append(min_rating)
        
    query += " ORDER BY rating DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    hotels = []
    for r in rows:
        hotels.append({
            "title": r[0],
            "price": r[1],
            "rating": r[2]
        })
    return hotels

def run_hotel_agent(user_prompt, max_price=3000, min_rating=7.5):
    """使用 OpenAI GPT 機制進行飯店推薦分析"""
    print(f"🤖 Agent 正在從資料庫查詢飯店（條件：預算 <= ${max_price}，評分 >= {min_rating}）...")
    hotels = fetch_hotels_from_db(max_price, min_rating)
    
    if not hotels:
        print("❌ 資料庫中沒有符合條件的飯店。")
        return

    # 將資料庫資料格式化為文字，供 GPT 閱讀
    hotels_str = "\n".join([f"- {h['title']}: 價格 TWD {h['price']}, 評分 {h['rating']}" for h in hotels])
    
    system_instruction = (
        "你是一個專業且貼心的旅遊訂房 AI 顧問。請分析提供給你的飯店資料庫清單，"
        "並針對使用者的需求，推薦前 3 名 CP 值最高或最適合的飯店，說明推薦理由（價格優勢、評分高低等）。"
    )
    
    user_input = f"【使用者需求】: {user_prompt}\n\n【候選飯店清單】:\n{hotels_str}"

    # 初始化 OpenAI Client (預設會讀取環境變數 OPENAI_API_KEY)
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # 速度快且成本低，專題展示非常適合
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7
        )

        print("\n" + "="*20 + " 🤖 OpenAI Agent 決策推薦 " + "="*20)
        print(response.choices[0].message.content)
        print("="*55)

    except Exception as e:
        print(f"\n❌ 呼叫 OpenAI API 發生錯誤：{e}")
        print("請確認是否已設定 OPENAI_API_KEY 環境變數或 API 金鑰是否有效。")

if __name__ == "__main__":
    # 測試情境：搜尋預算 3000 以下、評價 8.0 以上的飯店
    user_query = "我想找平價且評價不錯的飯店，預算要在 3000 元以下，請幫我分析哪幾間最划算？"
    run_hotel_agent(user_query, max_price=3000, min_rating=8.0)