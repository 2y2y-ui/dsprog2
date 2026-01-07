import sqlite3

# データベースの初期設定を行う関数
def init_database():
    # データベースファイルに接続する
    # 'weather.db' というファイルがなければ新しく作られ、あればそのファイルを開く
    conn = sqlite3.connect('weather.db')
    
    # SQL（データベースへの命令文）を実行するためのカーソル（操作役）を作成する
    cursor = conn.cursor()

    # --- 1. 地域情報用テーブル（areas）の作成 ---
    # executeメソッドを使って、SQL文をデータベースに送る
    # CREATE TABLE IF NOT EXISTS: テーブルがまだなければ作る、という意味
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS areas (
            area_code TEXT PRIMARY KEY,  -- 地域コード（重複しない主キーとして扱う）
            area_name TEXT               -- 地域名（例：東京都）
        )
    """)

    # --- 2. 天気予報データ用テーブル（forecasts）の作成 ---
    # 取得した天気をどんどん保存していくためのテーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS forecasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, -- 自動で番号が振られるID（主キー）
            area_code TEXT,                       -- どの地域の天気かを記録する（areasテーブルと対応）
            target_date TEXT,                     -- 予報の日付（例：2026-01-04）
            weather_text TEXT,                    -- 天気の説明（例：晴れ 時々 くもり）
            weather_code TEXT,                    -- 天気コード（アイコン判定などに使う）
            fetched_at TEXT                       -- データを取り込んだ日時（過去の履歴管理用）
        )
    """)

    
    # 完了したことをコンソールに表示する
    print("データベース（weather.db）とテーブルの作成が完了しました。")

# このファイルを直接実行した時だけ、init_database関数を動かす
if __name__ == "__main__":
    init_database()