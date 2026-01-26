import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import japanize_matplotlib  # 日本語豆腐化防止（インストールされていない場合は pip install japanize-matplotlib）

def analyze_hypothesis():
    #  データベースからデータを読み込む
    db_path = 'travel_analysis.db'
    conn = sqlite3.connect(db_path)
    
    # 0.0のデータ（取得失敗やデータなし）を除外して取得
    query = """
    SELECT name, total_score, breakfast_score, room_score, price 
    FROM hotels 
    WHERE breakfast_score > 0 AND room_score > 0
    """
    df = pd.read_sql(query, conn)
    conn.close()

    if df.empty:
        print("有効なデータがありませんでした。")
        return

    print(f"分析対象データ数: {len(df)} 件")

    #  相関係数の計算（統計的な証明）
    correlation = df[['total_score', 'breakfast_score', 'room_score', 'price']].corr()
    print("\n--- 【相関係数】（1.0に近いほど総合評価への影響が強い） ---")
    print(correlation['total_score'].sort_values(ascending=False))

    # 散布図の作成（視覚的な証明）
    plt.figure(figsize=(10, 6))
    
    # 散布図を描画
    # X軸: 部屋, Y軸: 朝食, 色: 総合評価
    scatter = sns.scatterplot(
        data=df, 
        x='room_score', 
        y='breakfast_score', 
        hue='total_score', 
        palette='viridis', 
        s=100, 
        edgecolor='black', 
        alpha=0.8
    )

    # グラフの装飾
    plt.title('検証: 朝食スコアと部屋スコアが総合評価に与える影響', fontsize=15)
    plt.xlabel('部屋の評価', fontsize=12)
    plt.ylabel('朝食の評価', fontsize=12)
    plt.axvline(x=df['room_score'].mean(), color='gray', linestyle='--', alpha=0.5, label='部屋平均')
    plt.axhline(y=df['breakfast_score'].mean(), color='gray', linestyle='--', alpha=0.5, label='朝食平均')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title='総合評価')
    plt.grid(True, alpha=0.3)

    # 仮説エリア（部屋は平均以下だが、朝食は平均以上）の注目ホテルに名前を表示
    avg_room = df['room_score'].mean()
    avg_break = df['breakfast_score'].mean()
    
    target_hotels = df[
        (df['room_score'] < avg_room) & 
        (df['breakfast_score'] > avg_break)
    ]
    
    for i, row in target_hotels.iterrows():
        plt.text(
            row['room_score'], 
            row['breakfast_score'] + 0.02, 
            row['name'][:5], # 長すぎるので5文字まで
            fontsize=9, 
            color='red'
        )

    plt.tight_layout()
    plt.show()

    # 「朝食一点突破型ホテル」ランキング
    # ギャップ（朝食スコア - 部屋スコア）を計算
    df['gap'] = df['breakfast_score'] - df['room_score']
    
    # 朝食の方が部屋より圧倒的に評価が高い順に並べる
    # かつ、総合評価が4.0以上のもの（満足度は高いもの）
    top_gap_hotels = df[df['total_score'] >= 4.0].sort_values(by='gap', ascending=False).head(10)

    print("\n--- 【仮説立証】部屋より朝食の評価が圧倒的に高い高評価ホテル ---")
    print(top_gap_hotels[['name', 'total_score', 'breakfast_score', 'room_score', 'gap']].to_string(index=False))

if __name__ == "__main__":
    analyze_hypothesis()