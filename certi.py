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
    div.stButton > button:first-child { background-color: #2ecc71; color: white; border-radius: 5px; }
    div.stDownloadButton > button:first-child { background-color: #3498db; color: white; border-radius: 5px; }
    .reset-btn > div > button { background-color: #e74c3c !important; color: white !important; border-radius: 5px; }
    .creator-text { font-size: 14px; color: #888; margin-bottom: -10px; font-style: italic; }
    </style>
    """, unsafe_allow_html=True)

# --- Initialize Session State with your new defaults ---
if "x_pos" not in st.session_state: st.session_state.x_pos = 430
if "y_pos" not in st.session_state: st.session_state.y_pos = 370
if "zip_data" not in st.session_state: st.session_state.zip_data = None
if "show_success" not in st.session_state: st.session_state.show_success = False
if "cert_count" not in st.session_state: st.session_state.cert_count = 0

# --- Dialogs ---
@st.dialog("Confirm Reset")
def reset_confirmation():
    st.warning("⚠️ Are you sure you want to reset the page? All uploaded data and settings will be lost.")
    col_left, col_right = st.columns(2)
    if col_left.button("Yes, Reset Everything", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    if col_right.button("No, Keep Data", use_container_width=True):
        st.rerun()

@st.dialog("Generation Complete!")
def success_dialog():
    st.balloons()
    st.success(f"🎉 {st.session_state.cert_count} certificates generated successfully!")
    st.write("Your ZIP file is ready for download below:")
    st.download_button(
        label="⬇️ DOWNLOAD NOW",
        data=st.session_state.zip_data,
        file_name="certificates.zip",
        mime="application/zip",
        use_container_width=True,
        key="modal_download"
    )
    if st.button("Close", use_container_width=True):
        st.session_state.show_success = False
        st.rerun()

st.title("Bulk Certificate Generator")

# --- Sidebar Controls ---
with st.sidebar:
    st.error("**⚠️ PRIVACY NOTE: All data uploaded is temporarily kept on the cloud and is deleted the moment we refresh the webpage or close the window.**")
    st.divider()

    st.header("1. Upload Data")
    excel_file = st.file_uploader("Excel Sheet", type=['xlsx', 'xls'], key="excel_uploader")
    img_file = st.file_uploader("Certificate Template", type=['png', 'jpg', 'jpeg'], key="img_uploader")
    
    st.header("2. Font Settings")
    font_folder = "fonts"
    available_fonts = [f for f in os.listdir(font_folder) if f.endswith(('.ttf', '.otf'))] if os.path.exists(font_folder) else []
    
    if available_fonts:
        selected_font_name = st.selectbox("Select Font", available_fonts)
        font_path = os.path.join(font_folder, selected_font_name)
    else:
        st.warning("No fonts found in /fonts folder.")
        font_path = None

    # Requirement 1: Standard font size set to 40
    font_size = st.number_input("Font Size", min_value=10, max_value=1000, value=40)
    font_color = st.color_picker("Font Color", "#000000")
    
    st.header("3. Position (X, Y)")
    col_x, col_y = st.columns(2)
    # Requirement 2 & 3: Standard X=430, Y=370
    st.session_state.x_pos = col_x.number_input("X", value=int(st.session_state.x_pos))
    st.session_state.y_pos = col_y.number_input("Y", value=int(st.session_state.y_pos))

    st.divider()
    
    # Requirement 5: Creator Text
    st.markdown('<p class="creator-text">Created by "Shoeb Iqbal Khan"</p>', unsafe_allow_html=True)
    
    st.header("4. Actions")
    
    # Requirement 4: Buttons moved to sidebar
    if excel_file and img_file:
        if st.button("PREPARE ALL CERTIFICATES", use_container_width=True, key="prep_btn"):
            # Re-running the logic here so it has access to files
            df_temp = pd.read_excel(excel_file)
            names_temp = df_temp.iloc[:, 0].dropna().tolist()
            template_temp = Image.open(img_file).convert("RGB")
            
            try:
                font_temp = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()
            except:
                font_temp = ImageFont.load_default()

            with st.spinner(f"Generating {len(names_temp)} certificates..."):
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for name in names_temp:
                        cert = template_temp.copy()
                        d = ImageDraw.Draw(cert)
                        d.text((st.session_state.x_pos, st.session_state.y_pos), str(name), 
                               fill=font_color, font=font_temp, anchor="mm")
                        
                        img_byte_arr = io.BytesIO()
                        cert.save(img_byte_arr, format='PNG')
                        zip_file.writestr(f"{name}.png", img_byte_arr.getvalue())
                
                st.session_state.zip_data = zip_buffer.getvalue()
                st.session_state.cert_count = len(names_temp)
                st.session_state.show_success = True
                st.rerun()

        st.markdown('<div class="reset-btn">', unsafe_allow_html=True)
        if st.button("RESET PAGE", use_container_width=True, key="reset_trigger"):
            reset_confirmation()
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    if st.session_state.zip_data:
        st.download_button(
            label="⬇️ DOWNLOAD ZIP FILE",
            data=st.session_state.zip_data,
            file_name="certificates.zip",
            mime="application/zip",
            use_container_width=True,
            key="sidebar_download"
        )
    else:
        st.info("Prepare certificates to enable download.")

# --- Preview Logic (Main Page) ---
if excel_file and img_file:
    df = pd.read_excel(excel_file)
    names = df.iloc[:, 0].dropna().tolist()
    template = Image.open(img_file).convert("RGB")
    
    try:
        font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()
    except:
        font = ImageFont.load_default()

    preview_img = template.copy()
    draw = ImageDraw.Draw(preview_img)
    draw.text((st.session_state.x_pos, st.session_state.y_pos), "Sample Name", 
              fill=font_color, font=font, anchor="mm")
    
    st.subheader("Click on the template to set position:")
    coords = streamlit_image_coordinates(preview_img, key="cert_preview_component")

    if coords:
        if coords["x"] != st.session_state.x_pos or coords["y"] != st.session_state.y_pos:
            st.session_state.x_pos = coords["x"]
            st.session_state.y_pos = coords["y"]
            st.rerun()

    if st.session_state.show_success:
        success_dialog()

else:
    st.info("Please upload both an Excel file and a Template image to begin.")
