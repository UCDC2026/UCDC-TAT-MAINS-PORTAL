import streamlit as st
import re
from PIL import Image
import pandas as pd
import os
import urllib.request
from fpdf import FPDF

# -----------------------------------------------------
# ૧. પેજનું સેટિંગ
# -----------------------------------------------------
st.set_page_config(page_title="UCDC Visnagar - TAT Mains Checking", page_icon="🎓", layout="centered")

# -----------------------------------------------------
# ૨. ઓટોમેટિક ગુજરાતી ફોન્ટ ડાઉનલોડ (PDF માટે)
# -----------------------------------------------------
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
# ૩. તમારી API Key અને મોડેલ
# -----------------------------------------------------
from google import genai
from google.genai import types

API_KEY = st.secrets["GEMINI_API_KEY"] 
client = genai.Client(api_key=API_KEY)
BEST_MODEL = "gemini-flash-latest" 

# -----------------------------------------------------
# ૪. ગૂગલ શીટમાંથી પ્રશ્નો
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
            questions = [q for q in questions if q and q.lower() != 'nan']
            numbered_questions = []
            for i, q in enumerate(questions):
                if q != "મારો પોતાનો પ્રશ્ન (Custom)":
                    numbered_questions.append(f"{i+1}. {q}")
                else:
                    numbered_questions.append(q)
            q_dict[cat] = numbered_questions
        for cat in q_dict:
            if "મારો પોતાનો પ્રશ્ન (Custom)" not in q_dict[cat]:
                q_dict[cat].append("મારો પોતાનો પ્રશ્ન (Custom)")
        return q_dict
    except:
        return fallback_questions

questions_dict = load_questions(GOOGLE_SHEET_CSV_URL)

# -----------------------------------------------------
# ૫. સ્ટેટ મેનેજમેન્ટ (રિઝલ્ટ સાચવવા)
# -----------------------------------------------------
if 'checking_result' not in st.session_state: st.session_state['checking_result'] = None
if 'logged_in' not in st.session_state:
    if st.query_params.get('logged_in') == 'true':
        st.session_state['logged_in'] = True
        st.session_state['mobile_no'] = st.query_params.get('mobile', '')
        st.session_state['user_name'] = st.query_params.get('name', '')
        st.session_state['user_village'] = st.query_params.get('village', '')
    else:
        st.session_state['logged_in'] = False
        st.session_state['user_name'] = ""
        st.session_state['user_village'] = ""
        st.session_state['mobile_no'] = ""

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Mukta+Vaani:wght@400;600;700;800&display=swap');
    * { font-family: 'Mukta Vaani', sans-serif !important; }
    .tat-title { color: #000080; text-align: center; font-size: 30px; font-weight: 800; margin-bottom: 20px; margin-top: 15px; }
    .question-box { background-color: #f0f2f6; border-left: 5px solid #000080; padding: 15px; border-radius: 5px; font-size: 18px; color: #333; margin-bottom: 20px; white-space: pre-wrap; }
    div.stButton > button:first-child { background-color: #000080; color: white; font-size: 22px; width: 100%; font-weight: 700; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------
# ૬. PDF બનાવવાનું ફંક્શન
# -----------------------------------------------------
def create_pdf(text, student_name):
    # ઇમોજી અને અમુક નિશાનો કાઢવા જેથી PDF માં એરર ના આવે
    clean_text = text.replace('✅', '[+]').replace('❌', '[-]').replace('🎓', '').replace('⚠️', '!')
    
    pdf = FPDF()
    pdf.add_page()
    try:
        # જો ડાઉનલોડ થયેલો ફોન્ટ મળે તો તેનો ઉપયોગ કરવો
        pdf.add_font("Gujarati", style="", fname=FONT_PATH, uni=True)
        pdf.set_font("Gujarati", size=12)
    except:
        pdf.set_font("Arial", size=12)
    
    # PDF માં ટાઇટલ ઉમેરવું
    pdf.cell(200, 10, txt="UCDC Visnagar - TAT Mains Result", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Student Name: {student_name}", ln=True, align='C')
    pdf.cell(200, 10, txt="-"*50, ln=True, align='C')
    pdf.ln(5)
    
    # રિઝલ્ટ પ્રિન્ટ કરવું
    pdf.multi_cell(0, 8, txt=clean_text)
    return bytes(pdf.output())

# -----------------------------------------------------
# ૭. લૉગિન અને પોર્ટલ લેઆઉટ
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
            st.query_params['mobile'] = mobile_id
            st.rerun()
else:
    try: st.image("Seminar Uma Academy.jpg", use_container_width=True)
    except: pass

    st.markdown("<div class='tat-title'>UCDC વિસનગર - TAT પેપર ચેકિંગ</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1: 
        student_name = st.text_input("પૂરું નામ (English):", value=st.session_state['user_name'])
        if student_name != st.session_state['user_name']:
            st.session_state['user_name'] = student_name
            st.query_params['name'] = student_name 
            
    with col2: 
        student_village = st.text_input("ગામ/શહેર:", value=st.session_state['user_village'])
        if student_village != st.session_state['user_village']:
            st.session_state['user_village'] = student_village
            st.query_params['village'] = student_village 
            
    with col3: 
        student_mobile = st.text_input("મોબાઈલ નંબર:", value=st.session_state['mobile_no'], disabled=True)

    st.markdown("### 📝 પ્રશ્ન પસંદ કરો")
    category = st.selectbox("વિભાગ:", list(questions_dict.keys()))
    selected_display = st.selectbox("વિષય/પ્રશ્ન પસંદ કરો:", questions_dict[category])
    
    if selected_display != "મારો પોતાનો પ્રશ્ન (Custom)":
        actual_q = re.sub(r'^\d+\. ', '', selected_display)
        st.markdown(f"<div class='question-box'>{actual_q}</div>", unsafe_allow_html=True)
        final_question_to_check = actual_q
    else:
        custom_q = st.text_area("તમારો પોતાનો પ્રશ્ન અહીં ટાઈપ કરો:")
        final_question_to_check = custom_q

    st.markdown("### 📁 જવાબવહી અપલોડ કરો")
    uploaded_files = st.file_uploader("PDF અથવા ફોટા પસંદ કરો", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)

    if st.button("પેપર ચેક કરો 🚀"):
        has_patel = "PATEL" in student_name.upper()
        if not student_name or not has_patel:
            st.error("❌ આ પોર્ટલ માત્ર 'પાટીદાર' વિદ્યાર્થીઓ માટે છે.")
        elif not uploaded_files:
            st.warning("⚠️ ફાઈલ અપલોડ કરો.")
        else:
            with st.spinner("⏳ ચેકિંગ ચાલુ છે..."):
                try:
                    total_marks = 20 if category in ["નિબંધ લેખન", "વ્યાકરણ (૨૦ ગુણ)"] else 10
                    prompt = f"""
                    તમે માઁ ઉમા એકેડમી & UCDC વિસનગરના અત્યંત કડક અને અનુભવી નિષ્ણાત છો. 
                    વિદ્યાર્થીએ '{category}' વિભાગમાં '{final_question_to_check}' વિષય પર જવાબ લખ્યો છે.
                    
                    તમારો જવાબ હંમેશા: "જય માઁ ઉમાખોડલ અને જય સરદાર જય પાટીદાર" થી જ શરૂ કરો.

                    ૧. જો પ્રશ્ન અંગ્રેજી લિપિમાં હોય તો તેનો ગુજરાતી અર્થ કાઢી ચેક કરવું.
                    ૨. જો અપલોડ કરેલ લખાણ અલગ હોય તો સીધા ૦ ગુણ આપવા.

                    🎓 TAT 2026: ગુજરાતી વર્ણનાત્મક પેપર - મૂલ્યાંકન માળખું (કડક પાલન કરવું):
                    આ પ્રશ્ન કુલ {total_marks} ગુણનો છે.
                    
                    ⚠️ અત્યંત કડક સૂચના (STRICT MARKING POLICY) ⚠️
                    વિદ્યાર્થી ગમે તેટલું ઉત્કૃષ્ટ કે સર્વશ્રેષ્ઠ લખે, છતાં પણ તેને ક્યારેય પૂરા ગુણ આપવા નહીં. નીચે મુજબની મહત્તમ ગુણ મર્યાદાનું ચુસ્તપણે પાલન કરવું:
                    - જો '{category}' 'નિબંધ લેખન' હોય: તો ગમે તેટલો સારો નિબંધ હોય, ૨૦ માંથી મહત્તમ ૧૨ થી ૧૩ ગુણ જ આપવા.
                    - જો '{category}' 'ચર્ચાપત્ર' અથવા 'પત્ર લેખન' હોય: તો ૧૦ માંથી મહત્તમ ૬ ગુણ જ આપવા.
                    - જો '{category}' 'સંક્ષેપીકરણ' હોય: તો ૧૦ માંથી મહત્તમ ૫ ગુણ જ આપવા.
                    - (માત્ર વ્યાકરણમાં જ નિયમ મુજબ પૂરા માર્ક્સ આપી શકાય).

                    ૧. નિબંધ લેખન (કુલ ગુણ: ૨૦)
                    ✅ હકારાત્મક ગુણ: પ્રસ્તાવના/ઉપસંહાર (૦૪), વિષયવસ્તુ/ઊંડાણ (૦૮), મૌલિકતા/તાર્કિક પ્રવાહ (૦૪), ભાષાકીય શુદ્ધિ (૦૪).
                    ❌ નકારાત્મક ગુણ: વિષયાંતર (-૩ થી -૫), મૌલિકતાનો અભાવ (-૨), શબ્દમર્યાદા ભંગ (-૧ થી -૨), જોડણી/વ્યાકરણ (દર ૩ ભૂલે -૦.૫).

                    ૨. ચર્ચાપત્ર (કુલ ગુણ: ૧૦) 
                    ✅ હકારાત્મક ગુણ: માળખું/ફોર્મેટ (૦૨), તટસ્થ રજૂઆત (૦૩), મૌલિક/રચનાત્મક સૂચનો (૦૩), ભાષાશૈલી (૦૨).
                    ❌ નકારાત્મક ગુણ: ફોર્મેટની ભૂલ (-૧ પ્રત્યેક), અંગત/ઉગ્ર ભાષા (-૧.૫), જોડણી/વ્યાકરણ (દર ૩ ભૂલે -૦.૫).

                    ૩. પત્ર લેખન (કુલ ગુણ: ૧૦) 
                    ✅ હકારાત્મક ગુણ: માળખું/ઔપચારિકતા (૦૩), વિષયવસ્તુની સચોટતા (૦૪), સત્તાવાર શબ્દાવલિ (૦૩).
                    ❌ નકારાત્મક ગુણ: માળખાકીય ભૂલો (-૧ પ્રત્યેક), અસ્પષ્ટતા (-૨), બિનઔપચારિક ભાષા (-૧).

                    ૪. સંક્ષેપીકરણ (કુલ ગુણ: ૧૦) 
                    ✅ હકારાત્મક ગુણ: યોગ્ય શીર્ષક (૦૨), મૂળ વિચારની જાળવણી (૦૩), મૌલિકતા (૦૩), લંબાઈ/શુદ્ધિ (૦૨).
                    ❌ નકારાત્મક ગુણ: શીર્ષકનો અભાવ (-૨), કોપી-પેસ્ટ (-૨ થી -૩), અર્થનો અનર્થ (-૧.૫), બિનજરૂરી લંબાણ (-૧).

                    ૫. વ્યાકરણ (૨૦ ગુણ) - ૨૦ પ્રશ્નો. (સાચાનો ૧ ગુણ, ખોટાનો ૦).

                    તમારો જવાબ નીચેના ૫ (પાંચ) વિભાગમાં જ આપવો:
                    ### **૧. અંદાજિત શબ્દ સંખ્યા (Word Count)**
                    ### **૨. ક્યાં માર્કસ કપાયા તેનું વિશ્લેષણ**
                    ### **૩. વિભાગવાર માર્કિંગ (કુલ {total_marks} માંથી)** (માત્ર ટેબલ બનાવવું)
                    ### **૪. ભૂલોનું લિસ્ટ** (જોડણી/વ્યાકરણની ભૂલોનું લિસ્ટ આપવું. દર ૩ ભૂલે ૦.૫ ગુણ કાપવા)
                    ### **૫. નિષ્ણાતની સલાહ** (કયા મુદ્દા છૂટી ગયા અને કયા સોર્સ વાંચવા)
                    """
                    
                    contents = [prompt]
                    for file in uploaded_files:
                        if file.type == "application/pdf":
                            contents.append(types.Part.from_bytes(data=file.read(), mime_type="application/pdf"))
                        else:
                            contents.append(Image.open(file))
                    
                    response = client.models.generate_content(model=BEST_MODEL, contents=contents, config=types.GenerateContentConfig(temperature=0.0))
                    
                    st.session_state['checking_result'] = response.text
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ ભૂલ: {e}")

    # રિઝલ્ટ અને ડાઉનલોડ બટન
    if st.session_state['checking_result']:
        st.success("✅ ચેકિંગ પૂર્ણ!")
        st.balloons()
        st.markdown("---")
        st.markdown(st.session_state['checking_result'])
        
        # PDF ડાઉનલોડ બટન
        try:
            pdf_bytes = create_pdf(st.session_state['checking_result'], student_name)
            st.download_button(
                label="📥 રિઝલ્ટ PDF માં ડાઉનલોડ કરો",
                data=pdf_bytes,
                file_name=f"Result_{student_name}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error("PDF બનાવવામાં નાની ટેકનિકલ ભૂલ આવી છે, પણ તમારું રિઝલ્ટ ઉપર તૈયાર છે.")
