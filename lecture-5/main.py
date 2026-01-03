# Fletとrequestsライブラリをインポートする。
import flet as ft
import requests

# --- 定数の定義 ---
# 気象庁の地域一覧APIのURLを定数として定義する。
# URLが変更された場合に、ここだけを修正すれば良くなる。
AREA_LIST_URL = 'http://www.jma.go.jp/bosai/common/const/area.json'

def get_structured_area_data():
    """
    気象庁の地域JSONを取得し、UIで扱いやすい階層構造の辞書に整形して返す。
    構造: {"地方名": {"都道府県名": [("観測所名", "観測所コード"), ...]}}
    """
    try:
        # requestsライブラリを使い、地域リストのURLからデータをGETリクエストで取得する。
        response = requests.get(AREA_LIST_URL)
        # HTTPステータスコードが200番台(成功)でない場合、エラーを発生させる。
        response.raise_for_status()
        # 取得したレスポンスボディをJSON形式からPythonの辞書・リストに変換する。
        area_data = response.json()

        # 整形後のデータを格納するための空の辞書を準備する。
        structured_data = {}
        
        # 地方ごとの情報を処理する (例: "北海道地方", "東北地方")
        for center_code, center_info in area_data.get("centers", {}).items():
            center_name = center_info.get("name")
            structured_data[center_name] = {}
            
            # 各地方が含む都道府県コードのリストを処理する
            prefs_in_center = center_info.get("children", [])
            for pref_code in prefs_in_center:
                pref_info = area_data.get("class10s", {}).get(pref_code, {})
                pref_name = pref_info.get("name")
                if not pref_name:
                    continue
                
                structured_data[center_name][pref_name] = []
                
                # 各都道府県が含む観測所コードのリストを処理する
                offices_in_pref = pref_info.get("children", [])
                for office_code in offices_in_pref:
                    office_info = area_data.get("offices", {}).get(office_code, {})
                    office_name = office_info.get("name")
                    if office_name:
                        structured_data[center_name][pref_name].append((office_name, office_code))
        
        return structured_data

    except requests.exceptions.RequestException as e:
        # ネットワークエラーなどが発生した場合、コンソールにエラーメッセージを出力し、空の辞書を返す。
        print(f"地域データの取得に失敗しました: {e}")
        return {}

def main(page: ft.Page):
    # --- アプリケーションウィンドウの基本設定 ---
    page.title = "天気予報アプリ"
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # --- データ取得の確認 ---
    # 作成した関数を呼び出して、データが正しく取得・整形できるかを確認する。
    area_data = get_structured_area_data()
    # ターミナルに結果を出力する。
    print("--- 取得した地域データ ---")
    if area_data:
        print("地域データの取得に成功しました。")
    else:
        print("地域データの取得に失敗しました。")
    print("--------------------------")

    # この時点では、UIはまだ単純なまま。
    page.add(
        ft.Text("ようこそ！コンソールでデータ取得結果を確認してください。")
    )
    page.update()

# --- アプリケーションの起動 ---
if __name__ == "__main__":
    ft.app(target=main)