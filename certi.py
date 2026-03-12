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
    .stDownloadButton>button { background-color: #3498db; color: white; width: 100%; border-radius: 5px; }
    .stButton>button { background-color: #2ecc71; color: white; width: 100%; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.title("Bulk Certificate Generator")

# --- Initialize Session State ---
if "x_pos" not in st.session_state: st.session_state.x_pos = 432
if "y_pos" not in st.session_state: st.session_state.y_pos = 365
if "font_color" not in st.session_state: st.session_state.font_color = "#000000"
if "zip_data" not in st.session_state: st.session_state.zip_data = None

# --- Sidebar Controls ---
with st.sidebar:
# Privacy Note
    st.markdown("""
        **⚠️ PRIVACY NOTE:** **We DO NOT Save your data. All data uploaded (Excel sheets and images) is temporarily processed on the cloud and is permanently deleted the moment you refresh the webpage or close this window.**
    """)
    st.divider() # Adds a clean line to separate the note from the tools
    
    st.header("1. Upload Data")
    excel_file = st.file_uploader("Excel Sheet", type=['xlsx', 'xls'])
    img_file = st.file_uploader("Certificate Template", type=['png', 'jpg', 'jpeg'])
    
    st.header("2. Font Settings")
    font_folder = "fonts"
    available_fonts = [f for f in os.listdir(font_folder) if f.endswith(('.ttf', '.otf'))] if os.path.exists(font_folder) else []
    
    if available_fonts:
        selected_font_name = st.selectbox("Select Font", available_fonts)
        font_path = os.path.join(font_folder, selected_font_name)
    else:
        st.warning("No fonts found in /fonts folder. Using default.")
        font_path = None

    font_size = st.number_input("Font Size", min_value=10, max_value=1000, value=40)
    font_color = st.color_picker("Font Color", value=st.session_state.font_color)
    st.session_state.font_color = font_color
    
    st.header("3. Position (X, Y)")
    col1, col2 = st.columns(2)
    st.session_state.x_pos = col1.number_input("X", value=st.session_state.x_pos)
    st.session_state.y_pos = col2.number_input("Y", value=st.session_state.y_pos)

# --- Logic & Preview ---
if excel_file and img_file:
    df = pd.read_excel(excel_file)
    names = df.iloc[:, 0].dropna().tolist()
    template = Image.open(img_file).convert("RGB")
    
    try:
        if font_path:
            font = ImageFont.truetype(font_path, font_size)
        else:
            font = ImageFont.load_default()
    except Exception as e:
        font = ImageFont.load_default()

    # Preview
    preview_img = template.copy()
    draw = ImageDraw.Draw(preview_img)
    draw.text((st.session_state.x_pos, st.session_state.y_pos), "Sample Name", 
              fill=st.session_state.font_color, font=font, anchor="mm")
    
    st.subheader("Click to Position / Pick Color")
    coords = streamlit_image_coordinates(preview_img, key="cert_preview")

    if coords:
        # Check if coordinates actually changed to avoid infinite loop
        if coords["x"] != st.session_state.x_pos or coords["y"] != st.session_state.y_pos:
            st.session_state.x_pos = coords["x"]
            st.session_state.y_pos = coords["y"]
            
            # Auto-update color if you want, or just update position
            pixel_rgb = template.getpixel((coords["x"], coords["y"]))
            st.session_state.last_picked_color = '#%02x%02x%02x' % pixel_rgb
            st.rerun()

    # --- Generation Logic ---
    if st.button("PREPARE ALL CERTIFICATES"):
        with st.spinner("Generating..."):
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for name in names:
                    cert = template.copy()
                    d = ImageDraw.Draw(cert)
                    d.text((st.session_state.x_pos, st.session_state.y_pos), str(name), 
                           fill=st.session_state.font_color, font=font, anchor="mm")
                    
                    img_byte_arr = io.BytesIO()
                    cert.save(img_byte_arr, format='PNG')
                    zip_file.writestr(f"{name}.png", img_byte_arr.getvalue())
            
            st.session_state.zip_data = zip_buffer.getvalue()
            st.success(f"Successfully generated {len(names)} certificates!")

    # Show download button only if data exists in session state
    if st.session_state.zip_data:
        st.download_button(
            label="⬇️ DOWNLOAD ZIP FILE",
            data=st.session_state.zip_data,
            file_name="certificates.zip",
            mime="application/zip"
        )
else:
    st.info("Please upload both an Excel file and a Template image to begin.")

