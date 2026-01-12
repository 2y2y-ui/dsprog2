import flet as ft
import requests
# 追加機能: データベース操作と日付管理のためのライブラリを読み込む
import sqlite3
import datetime

# 天気の文字からアイコンを判定する補助関数（これはデザイン用の追加機能です）
# 修正: 判定ロジックを強化し、誤判定を防ぐ
def get_weather_icon(weather_text):
    # 判定用に不要な文字（スペースなど）を削除してシンプルにする
    text = weather_text.replace(" ", "").replace("　", "")
    
    # 特殊な天気の判定を先に行う
    if "雷" in text:
        return ft.Icons.FLASH_ON, ft.Colors.YELLOW_800
    elif "雪" in text or "吹雪" in text: 
        return ft.Icons.AC_UNIT, ft.Colors.LIGHT_BLUE
    
    # 基本的な天気の判定
    # ここでは分割された単語（例：「くもり」だけ）が渡されることを想定して判定する
    if "晴" in text:
        return ft.Icons.WB_SUNNY, ft.Colors.ORANGE
    elif "雨" in text:
        return ft.Icons.UMBRELLA, ft.Colors.BLUE
    elif "曇" in text or "くもり" in text:
        return ft.Icons.CLOUD, ft.Colors.GREY
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

    # --- 追加機能: ユーザーへの通知用メッセージバー ---
    # 画面の下にポップアップメッセージを出すための部品（SnackBar）を用意する
    # 中身のテキストは空にしておき、使うときに書き換える
    snack_bar = ft.SnackBar(content=ft.Text(""))
    # ページ全体の上乗せレイヤー（overlay）に追加して、どこからでも使えるようにする
    page.overlay.append(snack_bar)

    # メッセージを表示する処理を関数にしておく
    # これを作ることで、好きなタイミングで「show_message("文字")」と呼べばメッセージが出るようになる
    def show_message(text):
        # 表示したい文章をセットする
        snack_bar.content.value = text
        # 表示スイッチをオンにする
        snack_bar.open = True
        # 画面を更新して表示を反映させる
        page.update()

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

    # --- 追加機能: 取得した地域情報をデータベースに保存する ---
    # データベースに接続する
    conn = sqlite3.connect('weather.db')
    cursor = conn.cursor()

    # 取得したoffices（都道府県ごとの情報）をループしてデータベースに登録する
    for code, info in offices.items():
        name = info["name"]
        # 重複してもエラーにならないよう INSERT OR IGNORE を使う
        # areasテーブルに地域コードと地域名を保存する
        cursor.execute("INSERT OR IGNORE INTO areas (area_code, area_name) VALUES (?, ?)", (code, name))
    
    # 変更を確定して接続を閉じる
    conn.commit()
    conn.close()

    # --- お気に入り機能用の変数 ---
    # お気に入りに登録された地域コードを保存するセット（重複しないリストのようなもの）
    favorite_codes = set()

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

    # --- サイドバー更新用の関数定義 ---
    # お気に入りが変更されるたびにサイドバーを作り直す必要があるため、関数化します
    sidebar_column = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=0)

    # 天気情報を取得・表示する関数（ListTileをクリックしたときに動く）
    # ※関数内で関数を使うため、先に定義します
    def show_forecast(e):
        # クリックされたListTileまたはボタンから地域コードと地域名を取り出す
        # data属性に格納しておいた値を使います
        region_code = e.control.data
        
        # 地域名を取得する（お気に入りボタンからの場合とリストからの場合で取り方が違うため工夫）
        if isinstance(e.control, ft.ListTile):
            region_name = e.control.title.value
        else:
            # ボタンなどの場合、辞書から名前を逆引きする（簡易的な実装）
            region_name = offices[region_code]["name"]
        
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

            # --- 追加機能: データベースへの保存と読み出し ---
            
            # 取得したAPIデータをデータベースに保存する
            conn = sqlite3.connect('weather.db')
            cursor = conn.cursor()
            
            # データをいつ取得したか記録するために現在時刻を取得する
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 天気リスト（3日分など）をループして1件ずつ保存する
            for i in range(len(weather_list)):
                w_text = weather_list[i]
                w_date = time_defines[i]
                
                # forecastsテーブルに、地域コード、日付、天気、取得日時を保存する
                # weather_codeは今回は仮で空文字にしている
                cursor.execute("""
                    INSERT INTO forecasts (area_code, target_date, weather_text, weather_code, fetched_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (region_code, w_date, w_text, "", current_time))
            
            # 保存を確定する
            conn.commit()

            # 画面表示用にデータベースからデータを読み込む
            # 今回保存したばかりのデータ（fetched_atがcurrent_timeと同じもの）を取得する
            # ※これが「データベースに保存したものを表示する」という要件になる
            cursor.execute("""
                SELECT target_date, weather_text 
                FROM forecasts 
                WHERE area_code = ? AND fetched_at = ?
            """, (region_code, current_time))
            
            # 検索結果をすべて取得する
            db_results = cursor.fetchall()
            
            # 接続を閉じる
            conn.close()

            # タイトルを更新する
            weather_column.controls.clear()
            
            # --- お気に入りボタンの処理 ---
            # 現在の地域がお気に入りに含まれているか確認する
            is_favorite = region_code in favorite_codes
            # アイコンの状態を決める（お気に入りなら塗りつぶし星、そうでなければ枠線のみ）
            fav_icon = ft.Icons.STAR if is_favorite else ft.Icons.STAR_BORDER
            fav_color = ft.Colors.AMBER if is_favorite else ft.Colors.GREY

            # お気に入りボタンが押されたときの関数
            def toggle_favorite(e):
                # 状態を反転させる
                if region_code in favorite_codes:
                    favorite_codes.remove(region_code)
                    # 追加機能: 解除したことを画面下のメッセージでユーザーに伝える
                    show_message("お気に入りから解除しました")
                else:
                    favorite_codes.add(region_code)
                    # 追加機能: 追加したことを画面下のメッセージでユーザーに伝える
                    show_message("お気に入りに追加しました")
                
                # サイドバーを更新して、お気に入りリストに反映させる
                render_sidebar()
                
                # 現在表示中の天気画面も再描画して、星の色を変える
                # （show_forecastをもう一度呼ぶことで画面全体を更新する）
                show_forecast(e)

            # デザイン変更: ヘッダー部分をリッチにする
            header = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.LOCATION_ON, color=ft.Colors.RED_400, size=30),
                    ft.Text(f"{region_name}の天気予報", size=28, weight="bold", color=ft.Colors.BLUE_GREY_900, expand=True),
                    # ここにお気に入りボタンを追加
                    ft.IconButton(
                        icon=fav_icon,
                        icon_color=fav_color,
                        icon_size=30,
                        tooltip="お気に入りに追加/解除",
                        on_click=toggle_favorite,
                        data=region_code # ボタンにも地域コードを持たせる
                    )
                ]),
                padding=ft.padding.only(bottom=20)
            )
            weather_column.controls.append(header)

            # 天気予報の数だけループして表示を作る
            # デザイン変更: Rowを使ってカードを横並び（レスポンシブ）っぽく配置するコンテナを用意
            cards_row = ft.Row(wrap=True, spacing=20, run_spacing=20)

            # --- 修正箇所: 以前は weather_list を直接ループしていたが、データベースからのデータを使うように変更 ---
            
            # データベースから取得した結果（db_results）を使ってループする
            # db_resultsの中身は [(日付, 天気), (日付, 天気), ...] という形になっている
            for row in db_results:
                # データベースから値を取り出す
                full_date_str = row[0] # target_date
                weather = row[1]       # weather_text

                # 元のコードのロジックに合わせて変数を準備する
                # 日付の文字列を見やすく整形する (例: 2024-01-01T17:00:00+09:00 -> 2024-01-01)
                date_str = full_date_str[:10]
                
                # デザイン変更: 天気の変化（のち、から）を判定してビジュアルを変える
                # 全角スペースなどを除去して、判定用の文字列を作成する
                # これにより「晴れ　のち　くもり」のようなスペース入りテキストも正しく処理できる
                search_text = weather.replace("　", "").replace(" ", "")
                
                visual_content = None # ここに表示するアイコン等のパーツを入れる
                
                # --- ロジック分岐の準備 ---
                
                #  時間による変化（「のち」「から」）
                time_split_keyword = None
                if "のち" in search_text:
                    time_split_keyword = "のち"
                elif "から" in search_text:
                    time_split_keyword = "から"
                
                #  一時的な変化（「時々」「一時」）
                occasional_split_keyword = None
                if "時々" in search_text:
                    occasional_split_keyword = "時々"
                elif "一時" in search_text:
                    occasional_split_keyword = "一時"

                # --- アイコン作成ロジック ---

                if time_split_keyword:
                    #  時間変化がある場合 (矢印スタイル)
                    # search_textを使って分割することで、正確に前後の天気を取得する
                    parts = search_text.split(time_split_keyword, 1)
                    before_txt = parts[0]
                    after_txt = parts[1]
                    
                    icon1, col1 = get_weather_icon(before_txt)
                    icon2, col2 = get_weather_icon(after_txt)
                    
                    visual_content = ft.Row(
                        [
                            ft.Icon(icon1, size=35, color=col1),
                            ft.Icon(ft.Icons.ARROW_FORWARD, size=24, color=ft.Colors.GREY_400),
                            ft.Icon(icon2, size=35, color=col2),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    )
                
                elif occasional_split_keyword:
                    # 「時々」や「一時」の場合 (スタックスタイル)
                    # テキストを分割してからアイコンを判定する
                    # これにより「くもり」がメインの場合に「晴れ」アイコンが出るのを防ぐ
                    parts = search_text.split(occasional_split_keyword, 1)
                    main_txt = parts[0] # メインの天気
                    sub_txt = parts[1]  # サブの天気
                    
                    main_icon_data, main_col = get_weather_icon(main_txt)
                    sub_icon_data, sub_col = get_weather_icon(sub_txt)
                    
                    # ft.Stackを使ってアイコンを重ねます
                    visual_content = ft.Stack(
                        controls=[
                            # 下のレイヤー: メインの天気（大きく表示）
                            ft.Container(
                                content=ft.Icon(main_icon_data, size=50, color=main_col),
                                padding=ft.padding.only(right=15, bottom=15) # 重なり調整
                            ),
                            # 上のレイヤー: サブの天気（右下に小さく表示）
                            ft.Container(
                                content=ft.Icon(sub_icon_data, size=28, color=sub_col),
                                bgcolor=ft.Colors.WHITE, # 重なった時に見やすいよう背景を白く抜く
                                border_radius=50, # 丸くする
                                padding=2,
                                alignment=ft.alignment.bottom_right, # 右下に配置
                                right=0,
                                bottom=0
                            ),
                        ],
                        width=75, # Stack全体のサイズ確保
                        height=65,
                    )

                else:
                    #  通常の（変化がない、または単純な）天気の場合
                    # 分割不要な場合も、search_textを使って判定する
                    icon_data, icon_color = get_weather_icon(search_text)
                    
                    visual_content = ft.Row([
                        ft.Icon(icon_data, size=40, color=icon_color),
                        ft.Text("天気", size=14, weight="bold", color=ft.Colors.GREY_800)
                    ])

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
                        # ここに作成したアイコン等を配置
                        # Stackなど高さが可変なものが入るため、Containerで包む
                        ft.Container(content=visual_content, height=65, alignment=ft.alignment.center_left),
                        
                        # テキストは補足として残す
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

    # --- サイドバーを構築する関数 ---
    def render_sidebar():
        # 一度中身を空にする
        sidebar_column.controls.clear()
        
        sidebar_controls = []
        
        # デザイン変更: サイドバーのタイトルを追加
        sidebar_controls.append(
            ft.Container(
                content=ft.Text("地域一覧", size=18, weight="bold", color=ft.Colors.WHITE),
                padding=20,
                bgcolor=ft.Colors.BLUE_800
            )
        )

        # --- お気に入りセクションの表示 ---
        if favorite_codes: # お気に入りが1つでもある場合のみ表示
            fav_tiles = []
            for code in favorite_codes:
                # 地域コードから名前を取得する（offices辞書を使う）
                if code in offices:
                    name = offices[code]["name"]
                    # お気に入り用のListTile作成
                    tile = ft.ListTile(
                        leading=ft.Icon(ft.Icons.STAR, size=16, color=ft.Colors.AMBER), # 星アイコン
                        title=ft.Text(name, color=ft.Colors.WHITE, size=14, weight="bold"),
                        data=code,
                        on_click=show_forecast,
                        hover_color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.AMBER) # 少し背景色をつける
                    )
                    fav_tiles.append(tile)
            
            # お気に入りリストをまとめる
            sidebar_controls.append(
                ft.ExpansionTile(
                    leading=ft.Icon(ft.Icons.BOOKMARK, color=ft.Colors.AMBER),
                    title=ft.Text("お気に入り", weight="bold"),
                    controls=fav_tiles,
                    collapsed_text_color=ft.Colors.AMBER,
                    text_color=ft.Colors.AMBER,
                    icon_color=ft.Colors.AMBER,
                    collapsed_icon_color=ft.Colors.AMBER,
                    initially_expanded=True # 最初から開いておく
                )
            )
            # 区切り線を入れる
            sidebar_controls.append(ft.Divider(color=ft.Colors.BLUE_GREY_700))


        # --- 通常の地域リスト ---
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

        # 作成したリストをサイドバーカラムに追加
        sidebar_column.controls.extend(sidebar_controls)
        # サイドバー部分を更新
        sidebar_column.update()

    # --- 初回起動時の処理 ---
    
    # サイドバー部分のコンテナを作成
    # デザイン変更: 背景色を濃い色にして、メインコンテンツとの境界をはっきりさせる
    sidebar = ft.Container(
        content=sidebar_column,
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
    
    # ページに追加した後にサイドバーの中身を描画する（これでupdateが機能する）
    render_sidebar()

# アプリを実行する
ft.app(target=main)