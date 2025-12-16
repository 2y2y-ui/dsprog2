#元々の四則演算機能に加え、より高度な計算を行えるようにするため、UIを拡張し、新たに5つの科学計算機能（平方根、2乗、sin、cos、tan）を追加しました。さらに、log（常用対数）、階乗、逆数の計算機能も実装しました。
#実装にあたっては、まず既存のUIレイアウトに新しい行を追加し、科学計算専用のボタンを配置しました。これらのボタンは、他のボタンと視覚的に区別がつくように専用のクラス（ScientificButton）を定義し、独自のスタイルを適用しています。
#計算ロジックについては、Pythonの標準mathモジュールを活用し、各ボタンに対応する数学関数を呼び出す形で実装しました。特に、三角関数（sin, cos, tan）については、一般的な電卓の挙動に合わせ、ユーザーが入力した数値を度数（Degree）として扱えるよう、内部でラジアンに変換する処理を加えています。
#参考文献はこちらです。
#Flet 公式サイトhttps://flet.dev/docs/
#Flet 公式サンプルhttps://github.com/flet-dev/examples/tree/main/python/apps/calculator
#Python ライブラリドキュメント (math モジュール) https://docs.python.org/3/library/math.html
import flet as ft
# 科学計算のためにmathモジュールをインポートする
import math


class CalcButton(ft.ElevatedButton):
    # 電卓のボタンの基底
    def __init__(self, text, button_clicked, expand=1):
        super().__init__()
        self.text = text
        self.expand = expand
        self.on_click = button_clicked
        self.data = text


class DigitButton(CalcButton):
    # 数字ボタン用
    def __init__(self, text, button_clicked, expand=1):
        CalcButton.__init__(self, text, button_clicked, expand)
        self.bgcolor = ft.Colors.WHITE24
        self.color = ft.Colors.WHITE


class ActionButton(CalcButton):
    # 四則演算などのアクションボタン用のクラス
    def __init__(self, text, button_clicked):
        CalcButton.__init__(self, text, button_clicked)
        self.bgcolor = ft.Colors.ORANGE
        self.color = ft.Colors.WHITE


class ExtraActionButton(CalcButton):
    # AC, +/-, % といった追加機能ボタン用のクラス
    def __init__(self, text, button_clicked):
        CalcButton.__init__(self, text, button_clicked)
        self.bgcolor = ft.Colors.BLUE_GREY_100
        self.color = ft.Colors.BLACK

class ScientificButton(CalcButton):
    # 科学計算ボタン用の新しいクラスを定義する。
    def __init__(self, text, button_clicked):
        CalcButton.__init__(self, text, button_clicked)
        # ボタンの背景色と文字色を定義する。
        self.bgcolor = ft.Colors.INDIGO_400
        self.color = ft.Colors.WHITE


class CalculatorApp(ft.Container):
    def __init__(self):
        super().__init__()
        self.reset()

        self.result = ft.Text(value="0", color=ft.Colors.WHITE, size=20)
        self.width = 350
        self.bgcolor = ft.Colors.BLACK
        self.border_radius = ft.border_radius.all(20)
        self.padding = 20
        self.content = ft.Column(
            controls=[
                ft.Row(controls=[self.result], alignment="end"),
                # 科学計算ボタンを配置する新しい行を追加する。
                ft.Row(
                    controls=[
                        ScientificButton(text="√", button_clicked=self.button_clicked),
                        ScientificButton(text="x²", button_clicked=self.button_clicked),
                        ScientificButton(text="sin", button_clicked=self.button_clicked),
                        ScientificButton(text="cos", button_clicked=self.button_clicked),
                        ScientificButton(text="tan", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        ScientificButton(text="tan", button_clicked=self.button_clicked),
                        ScientificButton(text="log", button_clicked=self.button_clicked),
                        ScientificButton(text="!", button_clicked=self.button_clicked),
                        ScientificButton(text="1/x", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        ExtraActionButton(text="AC", button_clicked=self.button_clicked),
                        ExtraActionButton(text="+/-", button_clicked=self.button_clicked),
                        ExtraActionButton(text="%", button_clicked=self.button_clicked),
                        ActionButton(text="/", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="7", button_clicked=self.button_clicked),
                        DigitButton(text="8", button_clicked=self.button_clicked),
                        DigitButton(text="9", button_clicked=self.button_clicked),
                        ActionButton(text="*", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="4", button_clicked=self.button_clicked),
                        DigitButton(text="5", button_clicked=self.button_clicked),
                        DigitButton(text="6", button_clicked=self.button_clicked),
                        ActionButton(text="-", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="1", button_clicked=self.button_clicked),
                        DigitButton(text="2", button_clicked=self.button_clicked),
                        DigitButton(text="3", button_clicked=self.button_clicked),
                        ActionButton(text="+", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="0", expand=2, button_clicked=self.button_clicked),
                        DigitButton(text=".", button_clicked=self.button_clicked),
                        ActionButton(text="=", button_clicked=self.button_clicked),
                    ]
                ),
            ]
        )

    def button_clicked(self, e):
        # ボタンクリック時に実行される関数
        data = e.control.data
        print(f"Button clicked with data = {data}")
        if self.result.value == "Error" or data == "AC":
            self.result.value = "0"
            self.reset()

        elif data in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "."):
            if self.result.value == "0" or self.new_operand == True:
                self.result.value = data
                self.new_operand = False
            else:
                self.result.value = self.result.value + data

        elif data in ("+", "-", "*", "/"):
            self.result.value = self.calculate(self.operand1, float(self.result.value), self.operator)
            self.operator = data
            if self.result.value == "Error":
                self.operand1 = "0"
            else:
                self.operand1 = float(self.result.value)
            self.new_operand = True

        elif data in ("="):
            self.result.value = self.calculate(self.operand1, float(self.result.value), self.operator)
            self.reset()
        
        # 科学計算ボタンが押された場合の処理を記述する。
        elif data in ("√", "x²", "sin", "cos", "tan", "log", "!", "1/x"):
            try:
                # 現在の表示値を取得し、浮動小数点数に変換する。
                current_value = float(self.result.value)
                res = 0 # 結果を格納する変数を初期化する。

                if data == "√":
                    # 負の数の平方根はエラーとする。
                    if current_value < 0:
                        res = "Error"
                    else:
                        res = math.sqrt(current_value)
                elif data == "x²":
                    res = current_value ** 2
                elif data == "sin":
                    # 入力値を度数とみなし、ラジアンに変換してsinを計算する。
                    res = math.sin(math.radians(current_value))
                elif data == "cos":
                    # 入力値を度数とみなし、ラジアンに変換してcosを計算する。
                    res = math.cos(math.radians(current_value))
                elif data == "tan":
                    # 入力値を度数とみなし、ラジアンに変換してtanを計算する。
                    res = math.tan(math.radians(current_value))
                
                # --- ここから追加したもの ---
                elif data == "log":
                    # 常用対数(log10)を計算する。入力値が0以下の場合はエラーとする。
                    if current_value <= 0:
                        res = "Error"
                    else:
                        res = math.log10(current_value)
                elif data == "!":
                    # 階乗を計算する。入力値が整数でない、または負の場合はエラーとする。
                    if current_value < 0 or current_value != int(current_value):
                        res = "Error"
                    else:
                        res = math.factorial(int(current_value))
                elif data == "1/x":
                    # 逆数を計算する。入力値が0の場合はエラーとする。
                    if current_value == 0:
                        res = "Error"
                    else:
                        res = 1 / current_value
                # --- ここまで追加したもの ---

                # 計算結果がエラーでなければ、表示を更新する。
                if res != "Error":
                    self.result.value = str(self.format_number(res))
                else:
                    self.result.value = "Error"
            
            except ValueError:
                # floatへの変換失敗など、予期せぬエラーが発生した場合は"Error"を表示する。
                self.result.value = "Error"
            
            # 科学計算後は、次の入力を新しいオペランドとして扱う。
            self.new_operand = True
        # --- ここまで追加したコード ---

        elif data in ("%"):
            self.result.value = str(float(self.result.value) / 100)
            self.reset()

        elif data in ("+/-"):
            if float(self.result.value) > 0:
                self.result.value = "-" + str(self.result.value)

            elif float(self.result.value) < 0:
                self.result.value = str(self.format_number(abs(float(self.result.value))))

        self.update()

    def format_number(self, num):
        # 計算結果が整数の場合、小数点以下を非表示にするためのフォーマット関数
        if num % 1 == 0:
            return int(num)
        else:
            # 非常に長い小数になる場合を考慮し、小数点以下10桁に丸める
            return round(num, 10)

    def calculate(self, operand1, operand2, operator):
        # 二項演算（四則演算）を実行する関数
        if operator == "+":
            return self.format_number(operand1 + operand2)

        elif operator == "-":
            return self.format_number(operand1 - operand2)

        elif operator == "*":
            return self.format_number(operand1 * operand2)

        elif operator == "/":
            if operand2 == 0:
                # ゼロ除算はエラーとする。
                return "Error"
            else:
                return self.format_number(operand1 / operand2)

    def reset(self):
        # 電卓の状態を初期化
        self.operator = "+"
        self.operand1 = 0
        self.new_operand = True


def main(page: ft.Page):
    page.title = "Scientific Calculator"
    # アプリケーションのインスタンスを作成
    calc = CalculatorApp()
    # ページにアプリケーションを追加
    page.add(calc)


# Fletアプリケーションとして実行する。
ft.app(main)