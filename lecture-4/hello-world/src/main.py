import flet as ft
import random # 雪の位置をランダムにするために追加

def main(page: ft.Page):
    counter = ft.Text("0", size=50, data=0)

    # ボタンがクリックされたときの関数を改造
    def increment_click(e):
        # 元のカウンターを増やす処理
        counter.data += 1
        counter.value = str(counter.data)
        counter.update()

        # ここから雪を降らせる処理を追加

        # 1. 雪の結晶アイコンを作成します
        snow_flake = ft.Icon(
            name=ft.icons.AC_UNIT,
            color=ft.colors.WHITE,
            size=random.randint(20, 50), # 大きさをランダムに
            # アニメーションの設定（3秒かけて移動する）
            animate_position=3000,
            # 初期の位置（画面の上部外側、横の位置はランダム）
            top=-50,
            left=random.randint(0, page.width - 50 if page.width else 500),
        )

        # 2. 画面の一番手前に、作った雪を追加します
        page.overlay.append(snow_flake)
        page.update()

        # 3. 雪の最終的な位置を画面の下に設定します
        #    この行を実行すると、アニメーションが自動で開始されます
        snow_flake.top = page.height
        page.update()


    page.floating_action_button = ft.FloatingActionButton(
        icon=ft.Icons.ADD, on_click=increment_click
    )
    page.add(
        ft.SafeArea(
            ft.Container(
                counter,
                alignment=ft.alignment.center,
            ),
            expand=True,
        )
    )

    # 見た目を調整するために、背景色だけ変更します
    page.title = "シンプルな雪アプリ"
    page.bgcolor = "#1E2952" # 夜空のような色
    page.update()


ft.app(main)