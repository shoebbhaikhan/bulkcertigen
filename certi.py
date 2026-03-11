import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile

st.set_page_config(page_title="Certificate Designer Pro", layout="wide")

# --- UI Styling ---
st.markdown("""
    <style>
    .main { background-color: #1e1e2e; color: white; }
    stButton>button { background-color: #2ecc71; color: white; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

st.title("Bulk Certificate Generator")

# --- Sidebar Controls ---
with st.sidebar:
    st.header("1. Upload Data")
    excel_file = st.file_uploader("Excel Sheet", type=['xlsx', 'xls'])
    img_file = st.file_uploader("Certificate Template", type=['png', 'jpg', 'jpeg'])
    
    st.header("2. Text Settings")
    font_size = st.number_input("Font Size", value=120)
    font_color = st.color_picker("Font Color", "#000000")
    
    st.header("3. Position (X, Y)")
    col1, col2 = st.columns(2)
    x_pos = col1.number_input("X", value=500)
    y_pos = col2.number_input("Y", value=400)

# --- Logic & Preview ---
if excel_file and img_file:
    df = pd.read_excel(excel_file)
    names = df.iloc[:, 0].dropna().tolist()
    template = Image.open(img_file).convert("RGB")
    
    # Preview
    preview_img = template.copy()
    draw = ImageDraw.Draw(preview_img)
    # Note: Streamlit uses default font if .ttf isn't provided
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
        
    draw.text((x_pos, y_pos), "Sample Name", fill=font_color, font=font, anchor="mm")
    st.image(preview_img, caption="Preview", use_container_width=True)
    
    # Generate
    if st.button("GENERATE & DOWNLOAD ALL"):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for name in names:
                cert = template.copy()
                d = ImageDraw.Draw(cert)
                d.text((x_pos, y_pos), str(name), fill=font_color, font=font, anchor="mm")
                
                img_byte_arr = io.BytesIO()
                cert.save(img_byte_arr, format='PNG')
                zip_file.writestr(f"{name}.png", img_byte_arr.getvalue())
        
        st.download_button(
            label="Download Certificates (.zip)",
            data=zip_buffer.getvalue(),
            file_name="certificates.zip",
            mime="application/zip"
        )
else:
    st.info("Please upload both an Excel file and a Template image to begin.")
