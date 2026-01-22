import streamlit as st

import pandas as pd

import matplotlib.pyplot as plt

import matplotlib.font_manager as fm

import io

import os

import urllib.request



# --- 1. フォント設定 (Streamlit Cloudでの日本語化) ---

def setup_plt_font():

    font_path = "NotoSansJP-Regular.ttf"

    font_url = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansCJKjp-Regular.otf"

    

    if not os.path.exists(font_path):

        try:

            urllib.request.urlretrieve(font_url, font_path)

        except:

            return None



    fm.fontManager.addfont(font_path)

    prop = fm.FontProperties(fname=font_path)

    plt.rcParams['font.family'] = prop.get_name()

    return prop



# --- 2. データ抽出ロジック ---

def get_machine_rows(df, csv_name, display_name, threshold):

    target_col = '機種名（データサイト表記）'

    if target_col not in df.columns:

        return None

        

    m_df = df[df[target_col] == csv_name].copy()

    e_df = m_df[m_df['差枚'] >= threshold].copy().sort_values('台番')

    

    if e_df.empty:

        return None

    

    rows = []

    rows.append([""] * 7) # 見出し行用

    rows.append(['台番', '機種名', 'ゲーム数', 'BIG', 'REG', 'AT', '差枚数'])

    

    for _, row in e_df.iterrows():

        rows.append([

            str(row['台番']),

            display_name,

            f"{int(row['G数']):,}G",

            str(row['BB']),

            str(row['RB']),

            str(row['ART']),

            f"+{int(row['差枚']):,}枚"

        ])

    return rows



# --- 3. アプリUI ---

st.set_page_config(page_title="優秀台表作成ツール v2", layout="centered")

st.title("🎰 優秀台表作成アプリ")



setup_plt_font()



uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type=['csv'])



if uploaded_file:

    try:

        df = pd.read_csv(uploaded_file, encoding='cp932')

    except:

        try:

            uploaded_file.seek(0)

            df = pd.read_csv(uploaded_file, encoding='utf-8')

        except Exception as e:

            st.error("CSV読み込み失敗")

            st.stop()



    all_machines = df['機種名（データサイト表記）'].unique().tolist()

    

    st.divider()

    targets = []

    for i in range(1, 4):

        st.subheader(f"{i}機種目")

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:

            csv_n = st.selectbox(f"CSV機種名", all_machines, key=f"csv_{i}")

        with col2:

            disp_n = st.text_input(f"表示略称", value=csv_n, key=f"disp_{i}")

        with col3:

            thresh = st.number_input(f"枚数条件", value=500, step=100, key=f"thresh_{i}")

        targets.append((csv_n, disp_n, thresh))



    st.divider()

    if st.button("OK（表を作成）"):

        master_rows = []

        headline_indices = []

        header_indices = []

        separator_indices = []

        machine_info = []



        for i, (csv_n, disp_n, thresh) in enumerate(targets):

            res = get_machine_rows(df, csv_n, disp_n, thresh)

            if res:

                headline_indices.append(len(master_rows))

                header_indices.append(len(master_rows) + 1)

                machine_info.append(disp_n)

                master_rows.extend(res)

                if i < 2: 

                    separator_indices.append(len(master_rows))

                    master_rows.append([""] * 7)



        if master_rows:

            fig, ax = plt.subplots(figsize=(16, len(master_rows) * 0.9))

            ax.axis('off')

            table = ax.table(cellText=master_rows, colWidths=[0.1, 0.25, 0.15, 0.1, 0.1, 0.1, 0.2], loc='center', cellLoc='center')

            table.auto_set_font_size(False)

            table.scale(1.0, 3.8)



            cells = table.get_celld()

            for (r, c), cell in cells.items():

                # --- 【修正ポイント】見出しの設定 ---

                if r in headline_indices:

                    cell.set_facecolor('#FF4B4B') # 指定の赤

                    if c == 3: # 中央列にテキスト

                        cell.get_text().set_text(f"{machine_info[headline_indices.index(r)]} 優秀台")

                        cell.get_text().set_fontsize(28)

                        cell.get_text().set_weight('bold') # 太字

                        cell.get_text().set_color('white') # 白文字

                    else:

                        cell.get_text().set_text("")

                    # 枠線

                    if c == 0: cell.visible_edges = 'TLB'

                    elif c == 6: cell.visible_edges = 'TRB'

                    else: cell.visible_edges = 'TB'

                

                # ヘッダー（黒）

                elif r in header_indices:

                    cell.set_facecolor('#444444')

                    cell.get_text().set_color('white')

                    cell.get_text().set_weight('bold')

                    cell.get_text().set_fontsize(20)

                # 余白

                elif r in separator_indices:

                    cell.set_facecolor('white')

                    cell.set_height(0.03)

                    cell.visible_edges = ''

                # データ行

                else:

                    cell.set_facecolor('#F2F2F2' if r % 2 == 0 else 'white')

                    cell.get_text().set_fontsize(18)



            buf = io.BytesIO()

            plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)

            st.image(buf)

            st.download_button("画像をダウンロード", buf.getvalue(), "result.png", "image/png")
