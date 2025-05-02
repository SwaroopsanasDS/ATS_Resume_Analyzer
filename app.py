import io
import base64
import os
import re
from io import BytesIO
import pdf2image
import streamlit as st
import plotly.graph_objects as go
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv

# Load API key
load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# ----------------- Futuristic Glassmorphic UI Styling -----------------
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0d1117;
        color: #e6edf3;
    }

    .main {
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 0 40px rgba(0, 255, 255, 0.05);
    }

    h1 {
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
        color: #ffffff;
        background: linear-gradient(90deg, #00feca, #2c67f2, #00feca);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradientGlow 4s ease-in-out infinite;
        text-shadow: 0 0 20px rgba(0, 254, 202, 0.25);
        margin-bottom: 0.5rem;
    }

    h2 {
        font-size: 1.3rem;
        font-weight: 500;
        text-align: center;
        color: #9beefb;
        text-shadow: 0 0 10px rgba(0, 254, 202, 0.2);
        animation: fadeInUp 2s ease-in-out;
    }

    @keyframes gradientGlow {
        0% { background-position: 0% center; }
        50% { background-position: 100% center; }
        100% { background-position: 0% center; }
    }

    @keyframes fadeInUp {
        0% { opacity: 0; transform: translateY(10px); }
        100% { opacity: 1; transform: translateY(0); }
    }

    .stTextArea > div, .stFileUploader > div {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(0, 254, 202, 0.2);
        border-radius: 12px;
        padding: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 0 0 transparent;
    }

    .stTextArea > div:hover, .stFileUploader > div:hover {
        box-shadow: 0 0 10px rgba(0, 254, 202, 0.3);
        border-color: #00feca;
        background-color: rgba(0, 254, 202, 0.05);
    }

    .stTextArea textarea {
        color: #e6edf3 !important;
        background-color: transparent !important;
    }

    .stFileUploader label {
        font-weight: 500;
        color: #9beefb;
    }

    .stButton button {
        background: linear-gradient(135deg, #00feca, #2c67f2);
        border: none;
        color: #0d1117;
        font-weight: bold;
        padding: 0.75rem 2rem;
        border-radius: 10px;
        transition: all 0.3s ease-in-out;
        box-shadow: 0 0 12px rgba(0, 254, 202, 0.3);
    }

    .stButton button:hover {
        background: linear-gradient(135deg, #2c67f2, #00feca);
        transform: scale(1.03);
        box-shadow: 0 0 20px rgba(0, 254, 202, 0.4);
        color: white;
    }

    .stProgress > div > div {
        background-image: linear-gradient(to right, #00feca, #2c67f2);
    }

    .css-1v0mbdj.ef3psqc4 {
        background: transparent;
    }

    .stPlotlyChart {
        background: transparent;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------- App Title -----------------
st.markdown("<h1>📄 Resume Analyzer</h1>", unsafe_allow_html=True)
st.markdown("<h2>AI-Powered Resume Screening & ATS Match Evaluation</h2>", unsafe_allow_html=True)


# ----------------- Upload & Inputs -----------------
input_text = st.text_area("📌 Paste Job Description", key="input")
uploaded_file = st.file_uploader("📤 Upload Resume (PDF)", type=["pdf"])

if uploaded_file:
    st.success("✅ Resume Uploaded")

# ----------------- PDF Conversion -----------------
def input_pdf_setup(uploaded_file):
    if uploaded_file is not None:
        # Specify the path to the Poppler binaries you included in your app
        poppler_path = './poppler-utils/bin'  # Adjust this based on where you stored the Poppler binary

        # Convert PDF to image
        images = pdf2image.convert_from_bytes(uploaded_file.read(), poppler_path=poppler_path)

        first_page = images[0]

        # Convert to bytes
        img_byte_arr = io.BytesIO()
        first_page.save(img_byte_arr, format="JPEG")
        img_byte_arr = img_byte_arr.getvalue()

        pdf_parts = [
            {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(img_byte_arr).decode()  # encode to base64
            }
        ]
        return pdf_parts
    else:
        raise FileNotFoundError

# ----------------- Gemini Call -----------------
def get_gemini_response(prompt_text, pdf_content, job_description):
    model = genai.GenerativeModel("gemini-1.5-pro")
    response = model.generate_content([
        {"text": prompt_text},
        {"inline_data": pdf_content[0]},
        {"text": job_description}
    ])
    return response.text

# ----------------- Visualization -----------------
def extract_percentage(text):
    match = re.search(r"(\d{1,3})\s*%", text)
    return int(match.group(1)) if match else None

def show_percentage_chart(percent):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=percent,
        title={'text': "ATS Match"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#00ffe1"},
            'bgcolor': "#1c1c1e",
            'borderwidth': 1,
            'bordercolor': "#333",
            'steps': [
                {'range': [0, 50], 'color': "#ff4d4d"},
                {'range': [50, 80], 'color': "#f9ca24"},
                {'range': [80, 100], 'color': "#00ffab"}
            ]
        }
    ))
    st.plotly_chart(fig, use_container_width=True)

# ----------------- Prompts -----------------
input_prompt1 = """You are an Experienced HR reviewing a resume for roles like Data Science, Web Development, or DevOps. Analyze how well this resume fits the job description. Highlight strengths and weaknesses."""
input_prompt2 = """As a Career Coach, analyze this resume and suggest how the candidate can improve their skills and experience for better alignment with the job description."""
input_prompt3 = """As an ATS scanner, compare this resume to the job description and give a percentage match. Include missing keywords and a final assessment."""

# ----------------- Buttons -----------------
col1, col2, col3 = st.columns(3)
with col1:
    submit1 = st.button("📋 Review Resume")
with col2:
    submit2 = st.button("🛠️ Improve Skills")
with col3:
    submit3 = st.button("📊 ATS Match")

# ----------------- Actions -----------------
if submit1 and uploaded_file:
    pdf_content = input_pdf_setup(uploaded_file)
    response = get_gemini_response(input_prompt1, pdf_content, input_text)
    st.subheader("🧾 Resume Review")
    st.write(response)

elif submit2 and uploaded_file:
    pdf_content = input_pdf_setup(uploaded_file)
    response = get_gemini_response(input_prompt2, pdf_content, input_text)
    st.subheader("🛠️ Skill Suggestions")
    st.write(response)

elif submit3 and uploaded_file:
    pdf_content = input_pdf_setup(uploaded_file)
    response = get_gemini_response(input_prompt3, pdf_content, input_text)
    st.subheader("📈 ATS Matching Result")

    percent = extract_percentage(response)
    if percent is not None:
        st.metric(label="Match Score", value=f"{percent}%")
        st.progress(percent)
        show_percentage_chart(percent)
    else:
        st.warning("⚠️ Could not extract percentage. Check if the AI response includes one.")

    st.markdown("### 🧠 Full Analysis")
    st.write(response)

elif (submit1 or submit2 or submit3) and not uploaded_file:
    st.warning("⚠️ Please upload your resume first.")
