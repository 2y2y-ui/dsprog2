import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import random
import datetime
import re # 正規表現を使うためのライブラリ（数字の抽出に便利）

TARGET_URL = "https://search.travel.rakuten.co.jp/ds/station/ensen?f_eki=0&f_page=1&f_hyoji=30&f_disp_type=hotel&f_ido=0.0&f_kdo=0.0&f_teikei=ensen&f_key=200%252C15503839%252C50887650&f_nen1=2026&f_tuki1=2&f_hi1=26&f_nen2=2026&f_tuki2=2&f_hi2=27&f_heya_su=1&f_otona_su=1&f_s1=0&f_s2=0&f_y1=0&f_y2=0&f_y3=0&f_y4=0&f_km=1.0&f_sort=hotel&f_tab=hotel&f_kin2=0&f_kin="

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36"
}
def get_detail_scores(detail_url):
    """
    詳細ページ（review.html）から「部屋」と「食事」の点数を取得する。
    """
    try:
        time.sleep(2) # マナーとして待機
        
        #  URLをクチコミページ（review.html）になおす
        review_url = re.sub(r'/[^/]+\.html.*$', '/review.html', detail_url)
        if "review.html" not in review_url:
             review_url = detail_url

        #  ページへのアクセス
        res = requests.get(review_url, headers=HEADERS, timeout=10)
        
        # クチコミページがない場合は、元のURLで再トライ
        if res.status_code != 200:
             res = requests.get(detail_url, headers=HEADERS, timeout=10)

        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 初期値（データがない場合は0.0）
        room = 0.0
        breakfast = 0.0

        #  検証で見つけた "data-test-id" を使って点数の箱を全て取得
        score_boxes = soup.find_all("div", attrs={"data-test-id": "category-score"})

        for box in score_boxes:
            try:
                # 箱の中の数字を取得
                score_value = float(box.get_text())
                
                # 親要素(p1)だけを見てラベル（部屋、朝食など）を判定
                parent = box.find_parent()
                if not parent:
                    continue
                
                # 親要素のテキスト（例: "部屋 4.56"）を取得し、空白を除去
                check_text = parent.get_text().strip()
                
                # ラベルに応じた振り分け
                if "部屋" in check_text:
                    room = score_value
                elif "朝食" in check_text:
                    breakfast = score_value
                elif "夕食" in check_text and breakfast == 0.0:
                    # 朝食がなく夕食評価がある場合は、それを食事スコアとして採用
                    breakfast = score_value
                elif "食事" in check_text and breakfast == 0.0:
                    # まれに「食事」とだけ書かれているケースへの対応
                    breakfast = score_value
                    
            except ValueError:
                continue

        return room, breakfast

    except Exception as e:
        print(f"  詳細取得エラー: {e}")
        return 0.0, 0.0

def get_score_from_text(text):
    """
    テキストの中から「4.5」のような浮動小数点数（スコア）を探し出す関数
    例: "お客さまの声 4.56" -> 4.56
    """
    match = re.search(r'(\d\.\d+)', text)
    if match:
        return float(match.group(1))
    return 0.0

def scrape_and_save():
    # DB接続
    conn = sqlite3.connect('travel_analysis.db')
    cursor = conn.cursor()
    
    # テーブルが存在しない場合に備えて作成する（エラー回避のため）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hotels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            total_score REAL,
            breakfast_score REAL,
            room_score REAL,
            price INTEGER,
            fetched_at TEXT
        )
    """)
    
    print("スクレイピングを開始する...")

    try:
        response = requests.get(TARGET_URL, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 「dl」タグを探す
        # class_ には "htlGnrlInfo" を指定する
        # （"htl-info__wrap" はスペース区切りの別クラスなので、片方指定
        hotel_sections = soup.find_all("dl", class_="htlGnrlInfo")
        
        print(f"{len(hotel_sections)} 件のホテルが見つかった。")

        if len(hotel_sections) == 0:
            print("警告: 0件です。URLが正しいか、または検索結果ページであることを確認してください。")

        for i, section in enumerate(hotel_sections): # i は進捗表示用に追加
            try:
                #  ホテル名 (h2タグ) 
                name_tag = section.find("h2")
                if not name_tag:
                    continue
                name = name_tag.get_text(strip=True)

                # 総合評価 
                # "お客さまの声" という文字の近くにある数字を探す戦略
                # 特定のクラスが見つからなくても、セクション内のテキスト全体から数字を探す
                text_content = section.get_text()
                total_score = get_score_from_text(text_content)
                
                # ここから詳細データを取得するロジックに変更 
                # 詳細ページへのリンクURLを取得する
                # ホテル名（h2）の中に <a> タグ（リンク）が含まれているため、その href 属性を取り出す
                link_tag = name_tag.find("a")
                
                # 初期値（リンクが見つからない場合用）
                breakfast_score = 0.0
                room_score = 0.0
                
                if link_tag:
                    detail_url = link_tag.get("href")
                    
                    # 進捗を表示する（詳細取得は時間がかかるため、ユーザーに状況を伝える）
                    print(f"[{i+1}/{len(hotel_sections)}] 詳細データ取得中: {name[:10]}... ", end="", flush=True)
                    
                    # 追加した関数を呼び出し、詳細ページの中身を見に行く
                    room_score, breakfast_score = get_detail_scores(detail_url)
                    
                    print(f"-> 部屋:{room_score}, 食事:{breakfast_score}")
                
                # 価格
                # 価格は dl の外側にあるケースが多いが、内側にある場合もある。
                # "円" を含む数字を探してみる
                price = 0
                price_match = re.search(r'([\d,]+)円', text_content)
                if price_match:
                    price_str = price_match.group(1).replace(",", "")
                    price = int(price_str)
                
                # 価格が取れなかった場合、親要素（外側の箱）まで見に行く
                if price == 0:
                    parent = section.parent
                    if parent:
                        parent_text = parent.get_text()
                        price_match_parent = re.search(r'([\d,]+)円', parent_text)
                        if price_match_parent:
                            price_str = price_match_parent.group(1).replace(",", "")
                            price = int(price_str)

                #  データの保存 
                now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                cursor.execute("""
                    INSERT INTO hotels (name, total_score, breakfast_score, room_score, price, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (name, total_score, breakfast_score, room_score, price, now))

            except Exception as e:
                print(f"エラー（{name}）: {e}")
                continue

        conn.commit()
        print("保存完了！")

    except Exception as e:
        print(f"全体エラー: {e}")

    finally:
        conn.close()
        time.sleep(2)

if __name__ == "__main__":
    scrape_and_save()