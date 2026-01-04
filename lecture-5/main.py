import flet as ft
import requests

def main(page: ft.Page):
    # アプリ全体のタイトルを設定する
    page.title = "天気予報アプリ"
    # テーマをライトモード（明るい）にする
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # --- データ取得処理 ---

    # 気象庁の地域リスト（エリア定義）を取得するURL
    area_url = "http://www.jma.go.jp/bosai/common/const/area.json"
    
    # APIから地域データを取得する
    # requestsを使ってWeb上のデータをJSON形式として読み込む
    response = requests.get(area_url)
    area_data = response.json()

    # 「centers」が地方（関東、近畿など）、「offices」が都道府県ごとの気象台を表している
    centers = area_data["centers"]
    offices = area_data["offices"]

    # --- UIパーツの定義 ---

    # 天気予報を表示するエリア（右側のメイン画面）
    # 初期状態では「地域を選択してください」と表示しておく
    weather_display = ft.Column(
        controls=[ft.Text("左のメニューから地域を選択してください", size=20)],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    # 天気情報を取得・表示する関数（ListTileをクリックしたときに動く）
    def show_forecast(e):
        # クリックされたListTileに埋め込んだ地域コード(data属性)を取り出す
        region_code = e.control.data
        region_name = e.control.title.value
        
        # 画面の表示を一度クリアする
        weather_display.controls.clear()
        # 読み込み中であることを表示する
        weather_display.controls.append(ft.Text(f"{region_name}の天気を取得中...", size=20))
        page.update()

        try:
            # 選択された地域の天気予報JSONを取得するURLを作成する
            forecast_url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{region_code}.json"
            forecast_res = requests.get(forecast_url)
            forecast_data = forecast_res.json()

            # 取得したデータから必要な情報を取り出す
            # データ構造: [0] -> timeSeries[0] -> areas[0] -> weathers (天気の配列)
            # ※気象庁のJSONは複雑なため、ここでは一番手前の「詳細な天気」を取得する
            time_series = forecast_data[0]["timeSeries"][0]
            weather_list = time_series["areas"][0]["weathers"]
            time_defines = time_series["timeDefines"]

            # タイトルを更新する
            weather_display.controls.clear()
            weather_display.controls.append(ft.Text(f"{region_name}の天気予報", size=30, weight="bold"))
            weather_display.controls.append(ft.Divider())

            # 天気予報の数だけループして表示を作る
            for i, weather in enumerate(weather_list):
                # 日付の文字列を見やすく整形する (例: 2024-01-01T17:00:00+09:00 -> 2024-01-01)
                date_str = time_defines[i][:10]
                
                # 天気情報をカードに入れて表示リストに追加する
                weather_display.controls.append(
                    ft.Card(
                        content=ft.Container(
                            padding=15,
                            content=ft.Column([
                                ft.Text(f"日付: {date_str}", weight="bold"),
                                ft.Text(f"天気: {weather}", size=18),
                            ])
                        )
                    )
                )

        except Exception as err:
            # エラーが起きた場合は画面に表示する
            weather_display.controls.append(ft.Text(f"エラーが発生しました: {err}", color="red"))
        
        # 画面を更新して変更を反映する
        page.update()

    # --- 左側のサイドバー（地域リスト）の作成 ---
    
    sidebar_controls = []

    # 地方（centers）ごとにループ処理を行う
    for center_code, center_info in centers.items():
        # その地方に含まれる都道府県（子供の要素）のコードリストを取得する
        child_codes = center_info["children"]
        
        # 都道府県ごとのListTileを入れるリストを作る
        prefecture_tiles = []
        
        for child_code in child_codes:
            # officesの中に詳細情報があればリストに追加する
            if child_code in offices:
                office_name = offices[child_code]["name"]
                
                # ListTileを作成する
                # data属性にコードを持たせておき、クリック時に使えるようにする
                tile = ft.ListTile(
                    title=ft.Text(office_name),
                    data=child_code,
                    on_click=show_forecast
                )
                prefecture_tiles.append(tile)
        
        # ExpansionTile（開閉可能なリスト）を作成し、その中に都道府県リストを入れる
        # 地方名（関東甲信地方など）をタイトルにする
        expansion_tile = ft.ExpansionTile(
            title=ft.Text(center_info["name"]),
            controls=prefecture_tiles,
            collapsed_text_color=ft.Colors.BLACK,
            text_color=ft.Colors.BLUE
        )
        sidebar_controls.append(expansion_tile)

    # サイドバー部分のスクロール可能なカラムを作成する
    sidebar = ft.Column(
        controls=sidebar_controls,
        scroll=ft.ScrollMode.AUTO,
        width=300, # サイドバーの幅を指定する
    )

    # --- メインレイアウトの組み立て ---
    
    # 行（Row）を使って、左にサイドバー、右に天気表示エリアを配置する
    layout = ft.Row(
        controls=[
            sidebar,
            ft.VerticalDivider(width=1), # 区切り線
            weather_display
        ],
        expand=True, # 画面いっぱいに広げる
    )

    # ページにレイアウトを追加する
    page.add(layout)

# アプリを実行する
ft.app(target=main)