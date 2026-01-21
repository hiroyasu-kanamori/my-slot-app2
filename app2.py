import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import io

# --- 1. フォント・基本設定 ---
def setup_plt_font():
    font_list = [f.name for f in fm.fontManager.ttflist]
    # システム内の日本語フォントを優先順位をつけて検索
    for f in ['IPAexGothic', 'Noto Sans CJK JP', 'Arial Unicode MS', 'Hiragino Sans', 'sans-serif']:
        if any(f in name for name in font_list):
            plt.rcParams['font.family'] = f
            break

# --- 2. データ抽出ロジック ---
def get_machine_rows(df, csv_name, display_name, threshold):
    # 機種名でフィルタリング
    m_df = df[df['機種名（データサイト表記）'] == csv_name].copy()
    # 差枚数でフィルタリングして台番順にソート
    e_df = m_df[m_df['差枚'] >= threshold].copy().sort_values('台番')
    
    if e_df.empty:
        return None
    
    rows = []
    rows.append([""] * 7) # 見出し用の空行
    rows.append(['台番', '機種名', 'ゲーム数', 'BIG', 'REG', 'AT', '差枚数']) # ヘッダー
    
    for _, row in e_df.iterrows():
        rows.append([
            row['台番'],
            display_name,
            f"{row['G数']:,}G",
            row['BB'],
            row['RB'],
            row['ART'],
            f"+{row['差枚']:,}枚"
        ])
    return rows

# --- 3. アプリUI構成 ---
st.set_page_config(page_title="優秀台表作成ツール v2", layout="centered")
st.title("🎰 優秀台表作成アプリ (app2.py)")

# STEP 1 & 2: CSVの挿入
st.header("STEP 1 & 2")
uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type=['csv'])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    all_machines_in_csv = df['機種名（データサイト表記）'].unique().tolist()
    st.success("CSVを読み込みました。")

    # STEP 3〜6: 3機種分の設定
    st.divider()
    st.header("機種設定")
    
    targets = []
    for i in range(1, 4):
        st.subheader(f"{i}機種目の設定")
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            # STEP 3: 機種名選択
            csv_n = st.selectbox(f"CSV上の名前を選択", all_machines_in_csv, key=f"csv_{i}", index=0)
        with col2:
            # STEP 4: 略称（表示名）
            disp_n = st.text_input(f"表示用の略称", value=csv_n, key=f"disp_{i}")
        with col3:
            # STEP 5: 枚数条件
            thresh = st.number_input(f"プラス枚数条件", value=500, step=100, key=f"thresh_{i}")
            
        targets.append((csv_n, disp_n, thresh))

    st.divider()
    # STEP 6: 作成確認
    st.subheader("表を作成しますか？")
    if st.button("OK（結合表を作成）"):
        setup_plt_font()
        
        master_rows = []
        headline_indices = []
        header_indices = []
        separator_indices = []
        machine_info = []

        # データの統合
        for csv_n, disp_n, thresh in targets:
            res = get_machine_rows(df, csv_n, disp_n, thresh)
            if res:
                headline_indices.append(len(master_rows))
                header_indices.append(len(master_rows) + 1)
                machine_info.append(disp_n)
                master_rows.extend(res)
                # 最後の機種でなければセパレーター（余白）を追加
                if disp_n != targets[-1][1]:
                    separator_indices.append(len(master_rows))
                    master_rows.append([""] * 7)

        if not master_rows:
            st.error("条件に合うデータがありませんでした。枚数条件を下げてみてください。")
        else:
            # 描画処理
            num_total_rows = len(master_rows)
            fig, ax = plt.subplots(figsize=(16, num_total_rows * 0.9))
            ax.axis('off')

            # 指定された列幅比率
            col_widths = [0.1, 0.25, 0.15, 0.1, 0.1, 0.1, 0.2]
            
            table = ax.table(
                cellText=master_rows,
                colWidths=col_widths,
                loc='center',
                cellLoc='center'
            )

            table.auto_set_font_size(False)
            table.scale(1.0, 3.8) # 行の高さ

            cells = table.get_celld()
            for (r, c), cell in cells.items():
                # 青見出し（ぶち抜き）
                if r in headline_indices:
                    cell.set_facecolor('#ADD8E6')
                    if c == 3:
                        idx = headline_indices.index(r)
                        cell.get_text().set_text(f"{machine_info[idx]} 優秀台")
                        cell.get_text().set_fontsize(28)
                        cell.get_text().set_weight('bold')
                        cell.get_text().set_clip_on(False)
                    else:
                        cell.get_text().set_text("")
                    
                    if c == 0: cell.visible_edges = 'TLB'
                    elif c == 6: cell.visible_edges = 'TRB'
                    else: cell.visible_edges = 'TB'

                # 黒ヘッダー
                elif r in header_indices:
                    cell.set_facecolor('#444444')
                    cell.get_text().set_color('white')
                    cell.get_text().set_weight('bold')
                    cell.get_text().set_fontsize(20)

                # 0.03の透明セパレーター
                elif r in separator_indices:
                    cell.set_facecolor('white')
                    cell.set_height(0.03)
                    cell.get_text().set_text("")
                    cell.visible_edges = ''

                # データ行（ゼブラ柄）
                else:
                    cell.set_facecolor('#F2F2F2' if r % 2 == 0 else 'white')
                    cell.get_text().set_fontsize(18)

            # 画像のバッファ出力と表示
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
            st.image(buf)
            
            # ダウンロードボタン
            st.download_button(
                label="画像をダウンロード",
                data=buf.getvalue(),
                file_name="excellent_table_combined.png",
                mime="image/png"
            )
