import streamlit as st
import re
from PIL import Image
import pandas as pd
import os
import urllib.request
from fpdf import FPDF

# -----------------------------------------------------
# ૧. પેજ અને ફોન્ટ સેટિંગ
# -----------------------------------------------------
st.set_page_config(page_title="UCDC Visnagar - TAT Mains Checking", page_icon="🎓", layout="centered")

FONT_URL = "https://github.com/google/fonts/raw/main/ofl/notosansgujarati/NotoSansGujarati-Regular.ttf"
FONT_PATH = "NotoSansGujarati-Regular.ttf"

@st.cache_resource
def download_font():
    if not os.path.exists(FONT_PATH):
        try:
            urllib.request.urlretrieve(FONT_URL, FONT_PATH)
        except:
            pass
download_font()

# -----------------------------------------------------
# ૨. API Key અને મોડેલ
# -----------------------------------------------------
from google import genai
from google.genai import types

API_KEY = st.secrets["GEMINI_API_KEY"] 
client = genai.Client(api_key=API_KEY)
BEST_MODEL = "gemini-flash-latest" 

# -----------------------------------------------------
# ૩. પ્રશ્નો લોડ કરવા
# -----------------------------------------------------
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSdEfCcM_cugFgMBsSlnsV_Lx1azdZgtNNivsApg1KWbFaE_24iMLFYvbkC8HMBg0xuKdsfbj6VxDZa/pub?output=csv" 

@st.cache_data(ttl=60)
def load_questions(url):
    fallback_questions = {
        "નિબંધ લેખન": ["૧. આર્ટિફિશિયલ ઇન્ટેલિજન્સ: વરદાન કે અભિશાપ?", "મારો પોતાનો પ્રશ્ન (Custom)"],
        "ચર્ચાપત્ર": ["૧. ટ્રાફિક સમસ્યા અંગે તંત્રીને પત્ર", "મારો પોતાનો પ્રશ્ન (Custom)"],
        "પત્ર લેખન": ["૧. અનિયમિત વીજ પુરવઠા અંગે ફરિયાદ પત્ર", "મારો પોતાનો પ્રશ્ન (Custom)"],
        "સંક્ષેપીકરણ": ["૧. સંક્ષેપીકરણ ફકરો - ૧", "મારો પોતાનો પ્રશ્ન (Custom)"],
        "વ્યાકરણ (૨૦ ગુણ)": ["૧. વ્યાકરણ સેટ - ૧", "મારો પોતાનો પ્રશ્ન (Custom)"]
    }
    try:
        df = pd.read_csv(url)
        q_dict = {}
        for col in df.columns:
            cat = str(col).strip()
            questions = df[col].dropna().astype(str).str.strip().tolist()
            numbered_questions = [f"{i+1}. {q}" if q != "મારો પોતાનો પ્રશ્ન (Custom)" else q for i, q in enumerate(questions)]
            q_dict[cat] = numbered_questions
        for cat in q_dict:
            if "મારો પોતાનો પ્રશ્ન (Custom)" not in q_dict[cat]: q_dict[cat].append("મારો પોતાનો પ્રશ્ન (Custom)")
        return q_dict
    except: return fallback_questions

questions_dict = load_questions(GOOGLE_SHEET_CSV_URL)

# -----------------------------------------------------
# ૪. સ્ટેટ મેનેજમેન્ટ
# -----------------------------------------------------
if 'checking_result' not in st.session_state: st.session_state['checking_result'] = None
if 'logged_in' not in st.session_state:
    if st.query_params.get('logged_in') == 'true':
        st.session_state['logged_in'] = True
        st.session_state['mobile_no'] = st.query_params.get('mobile', '')
        st.session_state['user_name'] = st.query_params.get('name', '')
        st.session_state['user_village'] = st.query_params.get('village', '')
    else: st.session_state['logged_in'] = False

st.markdown("""<style>@import url('https://fonts.googleapis.com/css2?family=Mukta+Vaani:wght@400;600;700;800&display=swap'); * { font-family: 'Mukta Vaani', sans-serif !important; } .tat-title { color: #000080; text-align: center; font-size: 30px; font-weight: 800; } .question-box { background-color: #f0f2f6; border-left: 5px solid #000080; padding: 15px; border-radius: 5px; font-size: 18px; margin-bottom: 20px; }</style>""", unsafe_allow_html=True)

# -----------------------------------------------------
# ૫. PDF બનાવવાનું ફંક્શન
# -----------------------------------------------------
def create_pdf(text, student_name):
    # ચિન્હો સાફ કરવા
    clean_text = text.replace('✅', '[+]').replace('❌', '[-]').replace('🎓', '').replace('⚠️', '!')
    pdf = FPDF()
    pdf.add_page()
    if os.path.exists(FONT_PATH):
        pdf.add_font("Gujarati", style="", fname=FONT_PATH, uni=True)
        pdf.set_font("Gujarati", size=11)
    else: pdf.set_font("Arial", size=11)
    
    pdf.multi_cell(0, 10, txt=f"UCDC Visnagar - TAT Mains Result\nStudent: {student_name}\n{'-'*40}\n\n{clean_text}")
    return pdf.output()

# -----------------------------------------------------
# ૬. પોર્ટલ લોજિક
# -----------------------------------------------------
if not st.session_state['logged_in']:
    try: st.image("Seminar Uma Academy.jpg", use_container_width=True)
    except: pass
    st.markdown("<div class='tat-title'>🔐 વિદ્યાર્થી લૉગિન</div>", unsafe_allow_html=True)
    mobile_id = st.text_input("લૉગિન ID (૧૦ અંક):", max_chars=10)
    password = st.text_input("પાસવર્ડ:", type="password")
    if st.button("લૉગિન કરો"):
        if len(mobile_id) == 10:
            st.session_state['logged_in'] = True
            st.session_state['mobile_no'] = mobile_id
            st.query_params['logged_in'] = 'true'
            st.rerun()
else:
    try: st.image("Seminar Uma Academy.jpg", use_container_width=True)
    except: pass
    st.markdown("<div class='tat-title'>UCDC વિસનગર - TAT પેપર ચેકિંગ</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1: student_name = st.text_input("પૂરું નામ (English):", value=st.session_state['user_name'])
    with col2: student_village = st.text_input("ગામ/શહેર:", value=st.session_state['user_village'])
    with col3: student_mobile = st.text_input("મોબાઈલ નંબર:", value=st.session_state['mobile_no'], disabled=True)

    category = st.selectbox("વિભાગ:", list(questions_dict.keys()))
    selected_display = st.selectbox("વિષય/પ્રશ્ન પસંદ કરો:", questions_dict[category])
    actual_q = re.sub(r'^\d+\. ', '', selected_display) if selected_display != "મારો પોતાનો પ્રશ્ન (Custom)" else ""
    if actual_q: st.markdown(f"<div class='question-box'>{actual_q}</div>", unsafe_allow_html=True)
    final_question_to_check = actual_q if actual_q else st.text_area("તમારો પ્રશ્ન:")

    uploaded_files = st.file_uploader("PDF અથવા ફોટા પસંદ કરો", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)

    if st.button("પેપર ચેક કરો 🚀"):
        if not student_name or "PATEL" not in student_name.upper():
            st.error("❌ આ પોર્ટલ માત્ર 'પાટીદાર' વિદ્યાર્થીઓ માટે છે.")
        elif not uploaded_files:
            st.warning("⚠️ ફાઈલ અપલોડ કરો.")
        else:
            with st.spinner("⏳ ચેકિંગ ચાલુ છે..."):
                try:
                    total_marks = 20 if category in ["નિબંધ લેખન", "વ્યાકરણ (૨૦ ગુણ)"] else 10
                    # નવી શરતો સાથેનો પ્રોમ્પ્ટ
                    prompt = f"""
                    તમે માઁ ઉમા એકેડમી & UCDC વિસનગરના અનુભવી નિષ્ણાત છો. 
                    વિદ્યાર્થીએ '{category}' વિભાગમાં '{final_question_to_check}' વિષય પર જવાબ લખ્યો છે.
                    
                    તમારો જવાબ હંમેશા: "જય માઁ ઉમાખોડલ અને જય સરદાર જય પાટીદાર" થી જ શરૂ કરો. ત્યારબાદ આ લીટી લખો: "માઁ ઉમા એકેડમી & UCDC વિસનગરના નિષ્ણાત તરીકે તમારા પત્રનું મૂલ્યાંકન નીચે મુજબ છે:"

                    ⚠️ અત્યંત કડક માર્કિંગ સૂચના (આંતરિક ઉપયોગ માટે):
                    - વિદ્યાર્થી ગમે તેટલું સારું લખે, નિબંધમાં ૨૦ માંથી મહત્તમ ૧૨-૧૩, પત્ર/ચર્ચાપત્રમાં ૧૦ માંથી મહત્તમ ૬, અને સંક્ષેપીકરણમાં મહત્તમ ૫ ગુણ જ આપવા. આ મર્યાદા વિશે વિદ્યાર્થીને લખાણમાં ક્યાંય જણાવવું નહીં.

                    📏 શબ્દ મર્યાદા અને ઓળખ (STRICT):
                    ૧. પત્ર લેખન: જો વિદ્યાર્થીએ પત્રમાં પોતાનું સાચું નામ, મોબાઈલ નંબર કે સાચું સરનામું (જેમ કે 'સરનામું-૧', 'સરનામું-૨') લખ્યું હોય, તો ઓળખ જાહેર કરવા બદલ સીધા ૨ માર્ક કાપવા. તેની જગ્યાએ 'અ.બ.ક.' કે 'ક્ષ.ય.જ.' હોવું જોઈએ.
                    ૨. શબ્દ સંખ્યા: તમારે ચોકસાઈથી શબ્દો ગણવા. જો શબ્દ મર્યાદા (નિબંધ ૩૦૦, પત્ર ૨૦૦, ચર્ચાપત્ર ૨૦૦) કરતા ૧૦% થી વધુ વધ-ઘટ હોય તો માર્ક કાપવા.

                    મૂલ્યાંકન વિભાગો:
                    ### ૧. અંદાજિત શબ્દ સંખ્યા (Word Count): (અહીં ચોક્કસ આંકડો આપો અને જણાવો કે તે વિષયને અનુરૂપ છે કે નહીં).
                    ### ૨. ક્યાં માર્કસ કપાયા તેનું વિશ્લેષણ: (જોડણી, શબ્દમર્યાદા ભંગ કે ઓળખ જાહેર કરવા બદલ કપાયેલ માર્ક અહીં સમજાવો).
                    ### ૩. વિભાગવાર માર્કિંગ (કુલ {total_marks} માંથી): (ટેબલ બનાવો).
                    ### ૪. ભૂલોનું લિસ્ટ: (જોડણીની ભૂલો આપો).
                    ### ૫. નિષ્ણાતની સલાહ: (સુધારા માટે માર્ગદર્શન).
                    """
                    contents = [prompt]
                    for file in uploaded_files:
                        if file.type == "application/pdf": contents.append(types.Part.from_bytes(data=file.read(), mime_type="application/pdf"))
                        else: contents.append(Image.open(file))
                    
                    response = client.models.generate_content(model=BEST_MODEL, contents=contents, config=types.GenerateContentConfig(temperature=0.0))
                    st.session_state['checking_result'] = response.text
                    st.rerun()
                except Exception as e: st.error(f"❌ ભૂલ: {e}")

    if st.session_state['checking_result']:
        st.success("✅ ચેકિંગ પૂર્ણ!")
        st.markdown("---")
        st.markdown(st.session_state['checking_result'])
        try:
            pdf_data = create_pdf(st.session_state['checking_result'], student_name)
            st.download_button(label="📥 રિઝલ્ટ PDF ડાઉનલોડ કરો", data=pdf_data, file_name=f"Result_{student_name}.pdf", mime="application/pdf")
        except: st.warning("PDF જનરેટ કરવામાં મુશ્કેલી છે, પણ તમે ઉપરથી રિઝલ્ટ કોપી કરી શકો છો.")
