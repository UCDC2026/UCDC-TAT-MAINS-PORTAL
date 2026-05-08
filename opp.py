import streamlit as st
import re
from PIL import Image
import pandas as pd

# -----------------------------------------------------
# ૧. પેજ સેટિંગ
# -----------------------------------------------------
st.set_page_config(page_title="UCDC Visnagar - TAT Mains Checking", page_icon="🎓", layout="centered")

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
# ૫. HTML રિપોર્ટ બનાવવાનું ફંક્શન (PDF ના બદલે બેસ્ટ ઓપ્શન)
# -----------------------------------------------------
def create_html_report(text, student_name):
    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>UCDC Result - {student_name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; line-height: 1.6; color: #000; background-color: #fff; }}
            h2 {{ color: #000080; text-align: center; border-bottom: 2px solid #000080; padding-bottom: 10px; margin-bottom: 20px; }}
            .content {{ white-space: pre-wrap; font-size: 16px; }}
        </style>
    </head>
    <body>
        <h2>UCDC Visnagar - TAT Mains Result<br><small style="color: #555; font-size: 18px;">Student: {student_name}</small></h2>
        <div class="content">{text}</div>
    </body>
    </html>
    """
    return html_content.encode('utf-8')

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
        has_patel = "PATEL" in student_name.upper()
        if not student_name or not has_patel:
            st.error("❌ આ પોર્ટલ માત્ર 'પાટીદાર' વિદ્યાર્થીઓ માટે છે.")
        elif not uploaded_files:
            st.warning("⚠️ ફાઈલ અપલોડ કરો.")
        else:
            with st.spinner("⏳ પેપરનું ડીપ ચેકિંગ ચાલુ છે..."):
                try:
                    total_marks = 20 if category in ["નિબંધ લેખન", "વ્યાકરણ (૨૦ ગુણ)"] else 10
                    # નવી અત્યંત સચોટ અને કડક સૂચનાઓ
                    prompt = f"""
                    તમે માઁ ઉમા એકેડમી & UCDC વિસનગરના અત્યંત હોશિયાર અને સચોટ પેપર ચેકર છો. 
                    વિદ્યાર્થીએ '{category}' વિભાગમાં '{final_question_to_check}' વિષય પર જવાબ લખ્યો છે.
                    
                    તમારો જવાબ હંમેશા: "જય માઁ ઉમાખોડલ અને જય સરદાર જય પાટીદાર" થી જ શરૂ કરો. ત્યારબાદ માત્ર આ લીટી લખો: "તમારા જવાબનું મૂલ્યાંકન નીચે મુજબ છે:"

                    ⚠️ આંતરિક માર્કિંગ નિયમો (વિદ્યાર્થીને જણાવવા નહીં):
                    - નિબંધમાં ૨૦ માંથી મહત્તમ ૧૨-૧૩ ગુણ જ આપવા.
                    - પત્ર/ચર્ચાપત્રમાં ૧૦ માંથી મહત્તમ ૬ ગુણ જ આપવા.
                    - સંક્ષેપીકરણમાં ૧૦ માંથી મહત્તમ ૫ ગુણ જ આપવા.
                    - ચેકિંગ લાઈન-બાય-લાઈન, અત્યંત સચોટ અને ડીપમાં કરવું. એક પણ ભૂલ છૂટવી ના જોઈએ. 

                    📏 સરનામું અને ઓળખનો નિયમ (ખાસ ધ્યાન આપવું):
                    - પત્ર લેખન કે ચર્ચાપત્રમાં જો વિદ્યાર્થીએ 'સરનામું-૧', 'સરનામું-૨', 'અ.બ.ક.', 'ક્ષ.ય.જ.', કે 'ક.ખ.ગ.' જેવી કાલ્પનિક વિગતો લખી હોય તો તે GPSC/TAT ના નિયમ મુજબ એકદમ સાચું છે! આના માટે કોઈ માર્ક કાપવા નહીં.
                    - માર્ક ત્યારે જ કાપવા જો વિદ્યાર્થીએ પોતાનું સાચું નામ, સાચો મોબાઈલ નંબર કે સાચા ગામ/શહેરનું નામ ભૂલથી લખી દીધું હોય.

                    મૂલ્યાંકન નીચેના ૫ વિભાગમાં જ આપવું:
                    ### ૧. અંદાજિત શબ્દ સંખ્યા (Word Count): 
                    (અહીં ચોક્કસ શબ્દો ગણીને આંકડો આપો. અને જણાવો કે આ વિષય અને પ્રશ્નની માંગ મુજબ શબ્દમર્યાદા બરાબર જળવાયેલી છે કે નહીં. જો લખાણ બહુ ટૂંકું કે બહુ લાંબુ હોય તો જ માર્ક કાપવા.)

                    ### ૨. ક્યાં માર્કસ કપાયા તેનું વિશ્લેષણ: 
                    (અહીં ડીપમાં સમજાવો કે વિદ્યાર્થીની રજૂઆત, માળખું કે ભાષામાં ક્યાં કચાશ રહી ગઈ છે જેના કારણે માર્ક કપાયા છે.)

                    ### ૩. વિભાગવાર માર્કિંગ (કુલ {total_marks} માંથી): 
                    (અહીં એક સુંદર ટેબલ બનાવો: ક્રમ | મૂલ્યાંકન પાસું | મેળવેલ ગુણ).

                    ### ૪. ભૂલોનું લિસ્ટ (સચોટ ચેકિંગ): 
                    (લખાણમાં રહેલી તમામ જોડણીની ભૂલો, વાક્યરચનાની ભૂલો અને વિરામચિહ્નોની ભૂલો અહીં લિસ્ટ સ્વરૂપે દર્શાવો. એક પણ ભૂલ છૂટવી ના જોઈએ).

                    ### ૫. વિસ્તૃત સલાહ અને માર્ગદર્શન: 
                    (આ વિભાગ સૌથી મહત્વનો છે. અહીં વિદ્યાર્થીને અત્યંત વિસ્તૃત અને મુદ્દાસર માર્ગદર્શન આપો. તેને સમજાવો કે આ જવાબને વધુ શ્રેષ્ઠ બનાવવા માટે કયા નવા મુદ્દાઓ ઉમેરી શકાય, કયા ઉદાહરણો મૂકી શકાય અને હવે પછી તેને કયા પુસ્તકો કે સોર્સ વાંચવા જોઈએ).
                    """
                    contents = [prompt]
                    for file in uploaded_files:
                        if file.type == "application/pdf": contents.append(types.Part.from_bytes(data=file.read(), mime_type="application/pdf"))
                        else: contents.append(Image.open(file))
                    
                    response = client.models.generate_content(model=BEST_MODEL, contents=contents, config=types.GenerateContentConfig(temperature=0.0))
                    st.session_state['checking_result'] = response.text
                    st.rerun()
                except Exception as e: st.error(f"❌ ભૂલ: {e}")

    # રિઝલ્ટ અને ડાઉનલોડ બટન
    if st.session_state['checking_result']:
        st.success("✅ ચેકિંગ પૂર્ણ!")
        st.markdown("---")
        st.markdown(st.session_state['checking_result'])
        
        # HTML રિપોર્ટ ડાઉનલોડ બટન
        report_data = create_html_report(st.session_state['checking_result'], student_name)
        st.download_button(
            label="📥 રિઝલ્ટ ડાઉનલોડ કરો",
            data=report_data,
            file_name=f"Result_{student_name}.html",
            mime="text/html"
        )
