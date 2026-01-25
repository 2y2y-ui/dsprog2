import sqlite3

# 分析用のデータベースを作成する
def init_project_db():
    # 'travel_analysis.db' という新しいファイルを作る
    conn = sqlite3.connect('travel_analysis.db')
    cursor = conn.cursor()

    # ホテル情報を入れるテーブル（hotels）を作る
    # すでにあったらエラーにならないように IF NOT EXISTS をつける
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hotels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,           -- ホテル名
            total_score REAL,    -- 総合評価（4.5など、小数を扱うのでREAL）
            breakfast_score REAL,-- 朝食評価
            room_score REAL,     -- 部屋評価
            price INTEGER,       -- 最安料金（円）
            fetched_at TEXT      -- 取得日時
        )
    """)

    conn.commit()
    conn.close()
    print("分析用データベース（travel_analysis.db）の準備完了。")

if __name__ == "__main__":
    init_project_db()