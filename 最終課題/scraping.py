import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import random
import datetime
import re # 正規表現を使うためのライブラリ（数字の抽出に便利）


TARGET_URL = "https://search.travel.rakuten.co.jp/ds/station/ensen?f_eki=0&f_page=1&f_hyoji=30&f_disp_type=hotel&f_ido=0.0&f_kdo=0.0&f_teikei=ensen&f_key=200%252C15503839%252C50887650&f_nen1=2026&f_tuki1=1&f_hi1=25&f_nen2=2026&f_tuki2=1&f_hi2=26&f_heya_su=1&f_otona_su=1&f_s1=0&f_s2=0&f_y1=0&f_y2=0&f_y3=0&f_y4=0&f_km=1.0&f_sort=hotel&f_tab=hotel&f_kin2=0&f_kin="

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36"
}

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

        for section in hotel_sections:
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
                
                # 詳細ページに行かずに「総合評価」だけで進めるか、
                # もしテキスト内に「食事」や「部屋」の点数があればそれを拾う。
                breakfast_score = 0.0
                room_score = 0.0
                
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
                print(f"取得: {name[:15]}... | 評価: {total_score} | 価格: {price}")

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