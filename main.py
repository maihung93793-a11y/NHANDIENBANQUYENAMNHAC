import streamlit as st
import requests
import time
import base64
import hmac
import hashlib
import os
import tempfile
import pandas as pd
from supabase import create_client, Client

# ================= CẤU HÌNH SUPABASE (DATABASE) =================
SUPABASE_URL = "https://sgzkyiycjxzmxdwcfzea.supabase.co"
SUPABASE_KEY = "sb_publishable_6G_Zd6f-uBx1PPgwDkoWhg_9lfMC89U"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================= CẤU HÌNH ACRCLOUD =================
ACR_HOST = "identify-ap-southeast-1.acrcloud.com"
ACR_ACCESS_KEY = "5a3db137d09ce88dbba26021d0d19371"
ACR_ACCESS_SECRET = "AYMk9dZkcCTUZgel6ZCEwLGBy6916vM31RK0SCip"

# Cấu hình giao diện tổng thể
st.set_page_config(
    page_title="Hệ Thống Kiểm Tra Bản Quyền Nhạc",
    page_icon="🎵",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ================= CSS TÙY CHỈNH =================
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;600;700;800&display=swap');

        /* NGĂN CHẶN BÔI ĐEN VÀ ĐỔI CON TRỎ CHUỘT TOÀN BỘ TRANG */
        * {
            -webkit-user-select: none !important;
            -moz-user-select: none !important;
            -ms-user-select: none !important;
            user-select: none !important;
            cursor: default;
        }

        /* NGOẠI LỆ: Cho phép bôi đen và hiện con trỏ nhập chữ tại ô Input */
        input, textarea {
            -webkit-user-select: auto !important;
            -moz-user-select: auto !important;
            -ms-user-select: auto !important;
            user-select: auto !important;
            cursor: text !important;
        }

        /* NGOẠI LỆ: Giữ con trỏ hình bàn tay cho Nút bấm, Tabs và Khu vực tải tệp */
        button, a, [data-testid="stFileUploadDropzone"], .stTabs [data-baseweb="tab"] {
            cursor: pointer !important;
        }

        html, body, [class*="css"] { font-family: 'Quicksand', sans-serif !important; }

        .block-container { padding-top: 2rem !important; padding-bottom: 0.5rem !important; }

        /* Tiêu đề chính */
        .title-text {
            text-align: center; 
            background: -webkit-linear-gradient(45deg, #1f77b4, #ff4b4b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
            font-size: 2.2rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
            padding-top: 10px;
            line-height: 1.4;
        }

        /* Tùy chỉnh Nút bấm Chính (Đăng nhập, Đăng ký, Phân tích) */
        button[kind="primary"] {
            border-radius: 10px;
            font-weight: 700;
            font-size: 16px;
            background: linear-gradient(135deg, #ff4b4b 0%, #ff7676 100%);
            color: white;
            padding: 0.5rem 1rem;
            border: none;
            box-shadow: 0 4px 10px rgba(255, 75, 75, 0.3);
            transition: all 0.3s ease;
            margin-top: 5px;
        }
        button[kind="primary"]:hover {
            transform: translateY(-2px) scale(1.01);
            box-shadow: 0 6px 15px rgba(255, 75, 75, 0.5);
            color: white;
        }

        /* Tùy chỉnh Nút Đăng xuất: Đẩy lề trên xuống để không bị cắt viền */
        button[kind="secondary"] {
            border-radius: 8px;
            font-weight: 700;
            color: #ff4b4b !important;
            border: 2px solid #ff4b4b !important;
            background: transparent !important;
            padding: 0.3rem 1rem !important; /* Tạo khung vừa vặn ôm sát chữ */
            transition: all 0.3s ease;
            margin-top: 15px !important; /* Đẩy nút xuống để hiển thị full viền trên */
        }
        button[kind="secondary"]:hover {
            background: #ff4b4b !important;
            color: white !important;
        }

        /* Khu vực Tải Tệp */
        [data-testid="stFileUploadDropzone"] {
            border: 2px dashed #1f77b4 !important;
            border-radius: 15px !important;
            padding: 20px 10px !important;
            background-color: #ffffff !important;
            display: flex; justify-content: center; align-items: center;
        }

        [data-testid="stAudioInput"] {
            margin: 0px auto;
        }

        /* Thẻ thông tin bài hát */
        .custom-metric-container {
            background-color: #ffffff; border-radius: 12px; padding: 10px 15px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05);
            border-left: 4px solid #1f77b4; height: 100%;
        }
        .custom-metric-label { color: #6c757d; font-size: 0.85rem; font-weight: 600; margin-bottom: 2px; }
        .custom-metric-value { color: #31333F; font-size: 1.1rem; font-weight: 700; word-wrap: break-word; }

        div[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
        h3 { margin-top: 5px !important; padding-bottom: 2px !important; font-size: 1.2rem !important; text-align: center; }

        .stTabs [data-baseweb="tab-list"] { gap: 10px; justify-content: center; }
        .stTabs [data-baseweb="tab"] { padding: 5px 15px; font-size: 1rem; }

        .stAlert { padding: 0.5rem !important; }
    </style>
""", unsafe_allow_html=True)

# ================= QUẢN LÝ TRẠNG THÁI ĐĂNG NHẬP =================
if 'user_authenticated' not in st.session_state:
    st.session_state['user_authenticated'] = False

query_params = st.query_params
if "access_token" in query_params or "type" in query_params:
    st.session_state['user_authenticated'] = True


# ================= HÀM XỬ LÝ DỮ LIỆU VÀ API =================
def check_song_in_local_file(song_title, file_path):
    if not os.path.exists(file_path):
        return False, f"⚠️ Không tìm thấy tệp `{file_path}`."
    try:
        df = pd.read_excel(file_path)
        target_title = str(song_title).lower().strip()
        matched = False
        matched_column = ""
        for col in df.columns:
            col_values = df[col].astype(str).str.lower().str.strip()
            if (col_values == target_title).any():
                matched = True
                matched_column = str(col)
                break
        if matched:
            return True, f"✅ Hợp lệ: **'{song_title}'** nằm trong Cột: {matched_column}."
        else:
            return False, f"❌ Bản nhạc **không** thuộc hệ thống bản quyền."
    except Exception as e:
        return False, f"⚠️ Lỗi đọc tệp: {e}"


def recognize_acrcloud(file_path):
    http_method = "POST"
    http_uri = "/v1/identify"
    data_type = "audio"
    signature_version = "1"
    timestamp = str(int(time.time()))
    string_to_sign = '\n'.join([http_method, http_uri, ACR_ACCESS_KEY, data_type, signature_version, timestamp])
    sign = base64.b64encode(hmac.new(ACR_ACCESS_SECRET.encode('ascii'), string_to_sign.encode('ascii'),
                                     digestmod=hashlib.sha1).digest()).decode('ascii')
    file_size = os.path.getsize(file_path)
    with open(file_path, 'rb') as f:
        files = {'sample': f}
        data = {
            'access_key': ACR_ACCESS_KEY, 'sample_bytes': file_size, 'timestamp': timestamp,
            'signature': sign, 'data_type': data_type, 'signature_version': signature_version
        }
        res = requests.post(f"https://{ACR_HOST}{http_uri}", files=files, data=data)
    return res.json()


def display_result_and_check(result):
    status_code = result.get("status", {}).get("code")
    if status_code == 0:
        track = result["metadata"]["music"][0]
        song_title = track.get('title', 'Không rõ')
        artist_names = ", ".join([a.get("name") for a in track.get("artists", [])])

        st.markdown("### 🎧 KẾT QUẢ")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                f'<div class="custom-metric-container"><div class="custom-metric-label">📌 Tên bài hát</div><div class="custom-metric-value">{song_title}</div></div>',
                unsafe_allow_html=True)
        with col2:
            st.markdown(
                f'<div class="custom-metric-container"><div class="custom-metric-label">🎤 Nghệ sĩ</div><div class="custom-metric-value">{artist_names}</div></div>',
                unsafe_allow_html=True)

        found, msg = check_song_in_local_file(song_title, "Nhạc BẢN QUYỀN.xlsx")

        if found:
            st.success(msg)
            st.balloons()
        else:
            st.error(msg)
    elif status_code in [3014, 3003]:
        st.error("⏳ Hết lượt nhận diện miễn phí hôm nay!")
    else:
        st.warning("⚠️ Không nhận diện được. Giai điệu ồn hoặc chưa đủ dài!")


# ================= ĐIỀU HƯỚNG GIAO DIỆN =================

if not st.session_state['user_authenticated']:
    st.markdown("<div class='title-text'>ĐĂNG NHẬP HỆ THỐNG</div>", unsafe_allow_html=True)

    tab_login, tab_register = st.tabs(["🔐 Đăng Nhập", "📝 Đăng Ký"])

    with tab_login:
        email_login = st.text_input("Email", key="login_email")
        pass_login = st.text_input("Mật khẩu", type="password", key="login_pass")
        if st.button("🚀 ĐĂNG NHẬP", type="primary", use_container_width=True):
            if email_login and pass_login:
                try:
                    res = supabase.auth.sign_in_with_password({"email": email_login, "password": pass_login})
                    st.session_state['user_authenticated'] = True
                    st.rerun()
                except Exception:
                    st.error("❌ Thông tin không chính xác hoặc chưa xác thực email!")
            else:
                st.warning("Vui lòng nhập đầy đủ.")

    with tab_register:
        email_reg = st.text_input("Email", key="reg_email")
        pass_reg = st.text_input("Mật khẩu (Tối thiểu 6 ký tự)", type="password", key="reg_pass")
        if st.button("🚀 ĐĂNG KÝ", type="primary", use_container_width=True):
            if len(pass_reg) >= 6:
                try:
                    res = supabase.auth.sign_up({"email": email_reg, "password": pass_reg})
                    st.success("✅ Đăng ký thành công! Vui lòng kiểm tra hộp thư email.")
                except Exception as e:
                    st.error(f"❌ Lỗi: {e}")
            else:
                st.warning("Mật khẩu tối thiểu 6 ký tự.")

else:
    # Chia cột để dồn nút Đăng xuất sang góc phải
    col_empty, col_logout = st.columns([7, 2])
    with col_logout:
        # BỎ use_container_width=True để khung nút ôm vừa khít vào chữ
        if st.button("🚪 ĐĂNG XUẤT", type="secondary"):
            supabase.auth.sign_out()
            st.session_state['user_authenticated'] = False
            st.query_params.clear()
            st.rerun()

    st.markdown("<div class='title-text'>KIỂM TRA BẢN QUYỀN ÂM NHẠC</div>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🎙️ Ghi âm trực tiếp", "📁 Tải tệp âm thanh"])

    with tab1:
        audio_bytes = st.audio_input("Bấm biểu tượng Micro để ghi âm (5-10s)")
        if audio_bytes:
            if st.button("🚀 PHÂN TÍCH GIAI ĐIỆU", type="primary", use_container_width=True):
                with st.spinner("Đang truy vấn dữ liệu..."):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                        tmp_file.write(audio_bytes.read())
                        temp_path = tmp_file.name
                    try:
                        result = recognize_acrcloud(temp_path)
                        display_result_and_check(result)
                    finally:
                        if os.path.exists(temp_path):
                            try:
                                os.remove(temp_path)
                            except:
                                pass

    with tab2:
        uploaded_audio = st.file_uploader("Kéo thả hoặc chọn tệp (MP3, WAV...)", type=['mp3', 'wav', 'm4a', 'mp4'])
        if uploaded_audio is not None:
            if st.button("🚀 KIỂM TRA TỆP", type="primary", use_container_width=True):
                with st.spinner("Đang phân tích tệp..."):
                    file_ext = os.path.splitext(uploaded_audio.name)[1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
                        tmp_file.write(uploaded_audio.read())
                        temp_path = tmp_file.name
                    try:
                        result = recognize_acrcloud(temp_path)
                        display_result_and_check(result)
                    finally:
                        if os.path.exists(temp_path):
                            try:
                                os.remove(temp_path)
                            except:
                                pass