import flet as ft
import requests

# 天気の文字からアイコンを判定する補助関数（これはデザイン用の追加機能です）
def get_weather_icon(weather_text):
    if "晴" in weather_text:
        return ft.Icons.WB_SUNNY, ft.Colors.ORANGE
    elif "雨" in weather_text:
        return ft.Icons.UMBRELLA, ft.Colors.BLUE
    elif "曇" in weather_text:
        return ft.Icons.CLOUD, ft.Colors.GREY
    elif "雪" in weather_text:
        return ft.Icons.AC_UNIT, ft.Colors.LIGHT_BLUE
    else:
        return ft.Icons.WB_CLOUDY_OUTLINED, ft.Colors.BLUE_GREY

def main(page: ft.Page):
    # アプリ全体のタイトルを設定する
    page.title = "天気予報アプリ"
    # テーマをライトモード（明るい）にする
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # デザイン調整: 全体のフォントやパディング設定
    page.fonts = {"Roboto": "Roboto-Regular.ttf"}  # デフォルトフォント
    page.padding = 0
    page.bgcolor = ft.Colors.GREY_100 # 背景を薄いグレーに

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
    # デザイン変更: グリッド風に見せるためのコンテナ調整
    weather_column = ft.Column(scroll=ft.ScrollMode.HIDDEN)
    
    weather_display = ft.Container(
        content=weather_column,
        expand=True,
        padding=30,
        bgcolor=ft.Colors.GREY_100 # メインエリアの背景色
    )
    
    # 初期メッセージの表示
    weather_column.controls.append(
        ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.MAP, size=64, color=ft.Colors.BLUE_GREY_300),
                ft.Text("左のメニューから地域を選択してください", size=20, color=ft.Colors.BLUE_GREY_500)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            padding=50
        )
    )

    # 天気情報を取得・表示する関数（ListTileをクリックしたときに動く）
    def show_forecast(e):
        # クリックされたListTileに埋め込んだ地域コード(data属性)を取り出す
        region_code = e.control.data
        region_name = e.control.title.value
        
        # 画面の表示を一度クリアする
        weather_column.controls.clear()
        # 読み込み中であることを表示する
        weather_column.controls.append(ft.ProgressBar(width=None, color=ft.Colors.BLUE))
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
            weather_column.controls.clear()
            
            # デザイン変更: ヘッダー部分をリッチにする
            header = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.LOCATION_ON, color=ft.Colors.RED_400, size=30),
                    ft.Text(f"{region_name}の天気予報", size=28, weight="bold", color=ft.Colors.BLUE_GREY_900)
                ]),
                padding=ft.padding.only(bottom=20)
            )
            weather_column.controls.append(header)

            # 天気予報の数だけループして表示を作る
            # デザイン変更: Rowを使ってカードを横並び（レスポンシブ）っぽく配置するコンテナを用意
            cards_row = ft.Row(wrap=True, spacing=20, run_spacing=20)

            for i, weather in enumerate(weather_list):
                # 日付の文字列を見やすく整形する (例: 2024-01-01T17:00:00+09:00 -> 2024-01-01)
                date_str = time_defines[i][:10]
                
                # デザイン変更: アイコンを取得
                icon_data, icon_color = get_weather_icon(weather)

                # 天気情報をカードに入れて表示リストに追加する
                # デザイン変更: カードに影と角丸をつけてリッチにする
                card_content = ft.Container(
                    width=250, # カードの幅を固定
                    height=180,
                    padding=20,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=15,
                    shadow=ft.BoxShadow(
                        blur_radius=10,
                        spread_radius=1,
                        color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                        offset=ft.Offset(0, 4)
                    ),
                    content=ft.Column([
                        ft.Text(f"日付: {date_str}", size=14, color=ft.Colors.GREY_600),
                        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                        ft.Row([
                            ft.Icon(icon_data, size=40, color=icon_color),
                            ft.Text("天気", size=14, weight="bold", color=ft.Colors.GREY_800)
                        ]),
                        ft.Text(weather, size=16, weight="w500", max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)
                    ], spacing=5)
                )
                
                cards_row.controls.append(card_content)
            
            weather_column.controls.append(cards_row)

        except Exception as err:
            # エラーが起きた場合は画面に表示する
            weather_column.controls.append(
                ft.Container(
                    content=ft.Text(f"エラーが発生しました: {err}", color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.RED_400,
                    padding=10,
                    border_radius=5
                )
            )
        
        # 画面を更新して変更を反映する
        page.update()

    # --- 左側のサイドバー（地域リスト）の作成 ---
    
    sidebar_controls = []
    
    # デザイン変更: サイドバーのタイトルを追加
    sidebar_controls.append(
        ft.Container(
            content=ft.Text("地域一覧", size=18, weight="bold", color=ft.Colors.WHITE),
            padding=20,
            bgcolor=ft.Colors.BLUE_800
        )
    )

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
                # デザイン変更: アイコンを追加し、クリック時の色設定を追加
                tile = ft.ListTile(
                    leading=ft.Icon(ft.Icons.LOCATION_CITY, size=16, color=ft.Colors.BLUE_GREY_200),
                    title=ft.Text(office_name, color=ft.Colors.BLUE_GREY_100, size=14),
                    data=child_code,
                    on_click=show_forecast,
                    hover_color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE)
                )
                prefecture_tiles.append(tile)
        
        # ExpansionTile（開閉可能なリスト）を作成し、その中に都道府県リストを入れる
        # 地方名（関東甲信地方など）をタイトルにする
        # デザイン変更: 色とアイコンを調整して視認性を向上
        expansion_tile = ft.ExpansionTile(
            leading=ft.Icon(ft.Icons.MAP_OUTLINED, color=ft.Colors.WHITE),
            title=ft.Text(center_info["name"], weight="bold"),
            controls=prefecture_tiles,
            collapsed_text_color=ft.Colors.WHITE,
            text_color=ft.Colors.LIGHT_BLUE_200,
            icon_color=ft.Colors.WHITE,
            collapsed_icon_color=ft.Colors.WHITE,
        )
        sidebar_controls.append(expansion_tile)

    # サイドバー部分のスクロール可能なカラムを作成する
    # デザイン変更: 背景色を濃い色にして、メインコンテンツとの境界をはっきりさせる
    sidebar = ft.Container(
        content=ft.Column(
            controls=sidebar_controls,
            scroll=ft.ScrollMode.AUTO,
            spacing=0
        ),
        width=300, # サイドバーの幅を指定する
        bgcolor=ft.Colors.BLUE_GREY_900,
        height=page.height # 高さを画面いっぱいに
    )

    # --- メインレイアウトの組み立て ---
    
    # 行（Row）を使って、左にサイドバー、右に天気表示エリアを配置する
    # デザイン変更: VerticalDividerを削除し、色分けで境界を表現
    layout = ft.Row(
        controls=[
            sidebar,
            weather_display
        ],
        expand=True, # 画面いっぱいに広げる
        spacing=0 # 隙間をなくす
    )

    # ページにレイアウトを追加する
    page.add(layout)

# アプリを実行する
ft.app(target=main)