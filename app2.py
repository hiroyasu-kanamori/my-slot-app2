import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from PIL import Image, ImageDraw, ImageFont
import io
import os
import urllib.request

# --- 1. フォント設定 (Streamlit Cloud対応) ---
def setup_fonts():
    font_path = "NotoSansJP-Bold.ttf"
    # Boldを使用することで看板の文字をより強調します
    font_url = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansCJKjp-Bold.otf"
    
    if not os.path.exists(font_path):
        try:
            urllib.request.urlretrieve(font_url, font_path)
        except:
            return None, None
    
    # Matplotlib用
    fm.fontManager.addfont(font_path)
    prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = prop.get_name()
    
    return prop, font_path

# --- 2. Pillowで看板を作成する関数 ---
def create_pillow_banner(text, width, font_path):
    height = 150  # 看板の高さ(px) 縦幅0.07相当のゆとり
    banner = Image.new('RGB', (width, height), color='#FF0000') # 赤背景
    draw = ImageDraw.Draw(banner)
    
    # 文字サイズ 36pt (Pillowではpxに近い値になるため適宜調整。ここでは大きな100px相当)
    try:
        font = ImageFont.truetype(font_path, 80)
    except:
        font = ImageFont.load_default()
        
    # 文字をど真ん中に配置
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    # 白文字で描画
    draw.text(((width - w) // 2, (height - h) // 2 - 10), text, fill="white", font=font)
    return banner

# --- 3. データ抽出ロジック ---
def get_machine_rows(df, csv_name, display_name, threshold):
    target_col = '機種名（データサイト表記）'
    if target_col not in df.columns:
        return None
    m_df = df[df[target_col] == csv_name].copy()
    e_df = m_df[m_df['差枚'] >= threshold].copy().sort_values('台番')
    
    if e_df.empty: return None
    
    rows = []
    rows.append([""] * 7) # 見出し行用
    rows.append(['台番', '機種名', 'ゲーム数', 'BIG', 'REG', 'AT', '差枚数'])
    for _, row in e_df.iterrows():
        rows.append([
            str(row['台番']), display_name, f"{int(row['G数']):,}G",
            str(int(row['BB'])), str(int(row['RB'])), str(int(row['ART'])),
            f"+{int(row['差枚']):,}枚"
        ])
    return rows

# --- 4. アプリUI ---
st.set_page_config(page_title="優秀台表作成ツール Hybrid", layout="centered")
st.title("🎰 優秀台表作成アプリ (Hybrid版)")

prop, font_file_path = setup_fonts()

uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type=['csv'])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, encoding='cp932')
    except:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, encoding='utf-8')

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

        # 最初の看板用セパレーター (0.01相当)
        master_rows.append([""] * 7) 
        first_sep_idx = 0

        for i, (csv_n, disp_n, thresh) in enumerate(targets):
            res = get_machine_rows(df, csv_n, disp_n, thresh)
            if res:
                h_idx = len(master_rows)
                headline_indices.append(h_idx)
                header_indices.append(h_idx + 1)
                machine_info.append(disp_n)
                master_rows.extend(res)
                if i < 2: 
                    separator_indices.append(len(master_rows))
                    master_rows.append([""] * 7)

        if len(master_rows) > 1:
            # --- Matplotlibで表を描画 ---
            fig, ax = plt.subplots(figsize=(16, len(master_rows) * 0.8))
            ax.axis('off')
            table = ax.table(cellText=master_rows, colWidths=[0.1, 0.25, 0.15, 0.1, 0.1, 0.1, 0.2], loc='center', cellLoc='center')
            table.auto_set_font_size(False)
            table.scale(1.0, 3.5)

            cells = table.get_celld()
            for (r, c), cell in cells.items():
                if r == first_sep_idx:
                    cell.set_facecolor('white')
                    cell.set_height(0.01) # 看板直下の極細セパレート
                    cell.visible_edges = ''
                elif r in headline_indices:
                    cell.set_facecolor('#FF4B4B')
                    if c == 3:
                        idx = headline_indices.index(r)
                        cell.get_text().set_text(f"{machine_info[idx]} 優秀台")
                        cell.get_text().set_fontsize(28)
                        cell.get_text().set_weight('bold')
                        cell.get_text().set_color('white')
                    else: cell.get_text().set_text("")
                    if c == 0: cell.visible_edges = 'TLB'
                    elif c == 6: cell.visible_edges = 'TRB'
                    else: cell.visible_edges = 'TB'
                elif r in header_indices:
                    cell.set_facecolor('#444444')
                    cell.get_text().set_color('white')
                    cell.get_text().set_fontsize(20)
                elif r in separator_indices:
                    cell.set_facecolor('white')
                    cell.set_height(0.03) # 機種間のセパレート
                    cell.visible_edges = ''
                else:
                    cell.set_facecolor('#F2F2F2' if r % 2 == 0 else 'white')
                    cell.get_text().set_fontsize(18)

            # 表を一度画像化
            table_buf = io.BytesIO()
            plt.savefig(table_buf, format='png', bbox_inches='tight', dpi=150)
            table_buf.seek(0)
            table_img = Image.open(table_buf)

            # --- Pillowで看板を作成して結合 ---
            banner_img = create_pillow_banner("週間おススメ機種", table_img.width, font_file_path)
            
            # 結合
            final_img = Image.new('RGB', (table_img.width, banner_img.height + table_img.height), color='white')
            final_img.paste(banner_img, (0, 0))
            final_img.paste(table_img, (0, banner_img.height))

            # 表示とダウンロード
            final_buf = io.BytesIO()
            final_img.save(final_buf, format='png')
            st.image(final_buf.getvalue())
            st.download_button("画像をダウンロード", final_buf.getvalue(), "report.png", "image/png")
