import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
import os
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

# --- Initialize Session State ---
if "x_pos" not in st.session_state: st.session_state.x_pos = 500
if "y_pos" not in st.session_state: st.session_state.y_pos = 400
if "font_color" not in st.session_state: st.session_state.font_color = "#000000"

# --- Sidebar Controls ---
with st.sidebar:
    st.header("1. Upload Data")
    excel_file = st.file_uploader("Excel Sheet", type=['xlsx', 'xls'])
    img_file = st.file_uploader("Certificate Template", type=['png', 'jpg', 'jpeg'])
    
    st.header("2. Font Settings")
    # Feature 2 Fix: Font Selection Menu
    font_folder = "fonts"
    available_fonts = [f for f in os.listdir(font_folder) if f.endswith(('.ttf', '.otf'))] if os.path.exists(font_folder) else []
    
    if available_fonts:
        selected_font_name = st.selectbox("Select Font", available_fonts)
        font_path = os.path.join(font_folder, selected_font_name)
    else:
        st.warning("No fonts found in /fonts folder. Using default.")
        font_path = None

    # Feature 1 Fix: Font Size (Removing 'value' link to state to allow manual override)
    font_size = st.number_input("Font Size", min_value=10, max_value=1000, value=120)
    
    font_color = st.color_picker("Font Color", value=st.session_state.font_color)
    st.session_state.font_color = font_color
    
    st.header("3. Position (X, Y)")
    col1, col2 = st.columns(2)
    # Allow manual entry to update the session state
    x_input = col1.number_input("X", value=st.session_state.x_pos)
    y_input = col2.number_input("Y", value=st.session_state.y_pos)
    st.session_state.x_pos = x_input
    st.session_state.y_pos = y_input

# --- Logic & Preview ---
if excel_file and img_file:
    df = pd.read_excel(excel_file)
    names = df.iloc[:, 0].dropna().tolist()
    template = Image.open(img_file).convert("RGB")
    
    # Load Selected Font
    try:
        if font_path:
            font = ImageFont.truetype(font_path, font_size)
        else:
            font = ImageFont.load_default()
    except Exception as e:
        st.error(f"Font Error: {e}")
        font = ImageFont.load_default()

    # Preview Image
    preview_img = template.copy()
    draw = ImageDraw.Draw(preview_img)
    draw.text((st.session_state.x_pos, st.session_state.y_pos), "Sample Name", 
              fill=st.session_state.font_color, font=font, anchor="mm")
    
    # Clickable Area (Updates Position and allows Eye-Dropper)
    st.subheader("Click on the image to place text or pick color")
    coords = streamlit_image_coordinates(preview_img, key="cert_preview")

    if coords:
        # Update session state with click coordinates
        st.session_state.x_pos = coords["x"]
        st.session_state.y_pos = coords["y"]
        
        # Eye-dropper logic
        pixel_rgb = template.getpixel((coords["x"], coords["y"]))
        hex_color = '#%02x%02x%02x' % pixel_rgb
        
        # Button to confirm color pick so it doesn't change accidentally
        if st.button(f"Apply Clicked Color ({hex_color})"):
            st.session_state.font_color = hex_color
            st.rerun()
        else:
            # Rerun to update the red dot/text position immediately on click
            st.rerun()

    # Bulk Generation
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
