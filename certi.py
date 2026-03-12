import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
from streamlit_image_coordinates import streamlit_image_coordinates

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
    
    # Initialize session state for position and color if not set
    if "x_pos" not in st.session_state: st.session_state.x_pos = 500
    if "y_pos" not in st.session_state: st.session_state.y_pos = 400
    if "font_color" not in st.session_state: st.session_state.font_color = "#000000"

    # Color picker linked to session state
    font_color = st.color_picker("Font Color", value=st.session_state.font_color)
    st.session_state.font_color = font_color
    
    st.header("3. Position (X, Y)")
    col1, col2 = st.columns(2)
    x_input = col1.number_input("X", value=st.session_state.x_pos)
    y_input = col2.number_input("Y", value=st.session_state.y_pos)
    
    # Update state if manual input changes
    st.session_state.x_pos = x_input
    st.session_state.y_pos = y_input

    st.info("💡 Click the image to set position. Use the 'Pick Color from Click' button after clicking to sync color.")

# --- Logic & Preview ---
if excel_file and img_file:
    df = pd.read_excel(excel_file)
    names = df.iloc[:, 0].dropna().tolist()
    template = Image.open(img_file).convert("RGB")
    
    # Load Font
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    # Preview Logic
    preview_img = template.copy()
    draw = ImageDraw.Draw(preview_img)
    draw.text((st.session_state.x_pos, st.session_state.y_pos), "Sample Name", 
              fill=st.session_state.font_color, font=font, anchor="mm")
    
    # Clickable Preview (Eye-dropper and Position tool)
    coords = streamlit_image_coordinates(preview_img, key="pill")

    if coords:
        # Update Position
        st.session_state.x_pos = coords["x"]
        st.session_state.y_pos = coords["y"]
        
        # Eye-dropper Logic: Get RGB of clicked pixel
        pixel_rgb = template.getpixel((coords["x"], coords["y"]))
        hex_color = '#%02x%02x%02x' % pixel_rgb
        
        if st.button(f"Use Picked Color ({hex_color})"):
            st.session_state.font_color = hex_color
            st.rerun()

    # Generate
    if st.button("GENERATE & DOWNLOAD ALL"):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for name in names:
                cert = template.copy()
                d = ImageDraw.Draw(cert)
                d.text((st.session_state.x_pos, st.session_state.y_pos), str(name), 
                       fill=st.session_state.font_color, font=font, anchor="mm")
                
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
