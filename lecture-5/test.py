import requests
import json 

# main.pyから、テストしたい関数だけをそのままコピーしてくる
def get_structured_area_data():
    """
    気象庁の地域JSONを取得し、UIで扱いやすい階層構造の辞書に整形して返す。
    """
    # Fletとは無関係に、この関数が単体で正しく動作するかをテストする
    AREA_LIST_URL = 'http://www.jma.go.jp/bosai/common/const/area.json'
    
    try:
        response = requests.get(AREA_LIST_URL)
        response.raise_for_status()
        area_data = response.json()

        structured_data = {}
        for center_code, center_info in area_data.get("centers", {}).items():
            center_name = center_info.get("name")
            structured_data[center_name] = {}
            
            prefs_in_center = center_info.get("children", [])
            for pref_code in prefs_in_center:
                pref_info = area_data.get("class10s", {}).get(pref_code, {})
                pref_name = pref_info.get("name")
                if not pref_name:
                    continue
                
                structured_data[center_name][pref_name] = []
                
                offices_in_pref = pref_info.get("children", [])
                for office_code in offices_in_pref:
                    office_info = area_data.get("offices", {}).get(office_code, {})
                    office_name = office_info.get("name")
                    if office_name:
                        structured_data[center_name][pref_name].append((office_name, office_code))
        
        return structured_data

    except requests.exceptions.RequestException as e:
        print(f"地域データの取得に失敗しました: {e}")
        return {}

# --- ここからがテストの実行部分 ---
if __name__ == "__main__":
    print("データ取得・整形処理を開始します...")
    
    # 関数を呼び出して、結果を変数に格納する
    final_data = get_structured_area_data()
    
    if final_data:
        print("データ取得・整形に成功しました。")
        print("--- 整形後のデータ構造 ---")
        # 辞書を人間が読みやすいように整形して、ターミナルに全て表示する
        # json.dumpsを使うと、日本語も文字化けせず綺麗に出力できる
        print(json.dumps(final_data, indent=2, ensure_ascii=False))
    else:
        print("データ取得・整形に失敗しました。")