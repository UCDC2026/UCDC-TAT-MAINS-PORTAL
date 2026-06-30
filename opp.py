import streamlit as st
import re
from PIL import Image
import pandas as pd
from google import genai
from google.genai import types

# -----------------------------------------------------
# ૧. પેજ સેટિંગ
# -----------------------------------------------------
st.set_page_config(page_title="UCDC Visnagar - TAT Mains Checking", page_icon="🎓", layout="centered")

# -----------------------------------------------------
# ૨. API Key અને મોડેલ
# -----------------------------------------------------
API_KEY = st.secrets["GEMINI_API_KEY"] 
client = genai.Client(api_key=API_KEY)
BEST_MODEL = "gemini-1.5-flash-latest" 

# -----------------------------------------------------
# ૩. પ્રશ્નો લોડ કરવા (Google Sheet)
# -----------------------------------------------------
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSdEfCcM_cugFgMBsSlnsV_Lx1azdZgtNNivsApg1KWbFaE_24iMLFYvbkC8HMBg0xuKdsfbj6VxDZa/pub?output=csv" 

@st.cache_data(ttl=60)
def load_questions(url):
    fallback_questions = {
        "સંપૂર્ણ પેપર (૧૦૦ ગુણ)": ["૧. આખું TAT મેઈન્સ પેપર (તમામ પ્રશ્નો)", "મારો પોતાનો પ્રશ્ન (Custom)"],
        "નિબંધ લેખન": ["૧. આર્ટિફિશિયલ ઇન્ટેલિજન્સ: વરદાન કે અભિશાપ?", "મારો પોતાનો પ્રશ્ન (Custom)"],
        "ચર્ચાપત્ર": ["૧. ટ્રાફિક સમસ્યા અંગે તંત્રીને પત્ર", "મારો પોતાનો પ્રશ્ન (Custom)"],
        "પત્ર લેખન": ["૧. અનિયમિત વીજ પુરવઠા અંગે ફરિયાદ પત્ર", "મારો પોતાનો પ્રશ્ન (Custom)"],
        "સંક્ષેપીકરણ": ["૧. સંક્ષેપીકરણ ફકરો - ૧", "મારો પોતાનો પ્રશ્ન (Custom)"],
        "વ્યાકરણ (૨૦ ગુણ)": ["૧. વ્યાકરણ સેટ - ૧", "મારો પોતાનો પ્રશ્ન (Custom)"]
    }
    try:
        df = pd.read_csv(url)
        q_dict = {"સંપૂર્ણ પેપર (૧૦૦ ગુણ)": ["૧. આખું TAT મેઈન્સ પેપર (તમામ પ્રશ્નો)", "મારો પોતાનો પ્રશ્ન (Custom)"]}
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
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'mobile_no' not in st.session_state: st.session_state['mobile_no'] = ""
if 'user_name' not in st.session_state: st.session_state['user_name'] = ""
if 'user_village' not in st.session_state: st.session_state['user_village'] = ""

if st.query_params.get('logged_in') == 'true':
    st.session_state['logged_in'] = True
    if st.query_params.get('mobile'): st.session_state['mobile_no'] = st.query_params.get('mobile')
    if st.query_params.get('name'): st.session_state['user_name'] = st.query_params.get('name')
    if st.query_params.get('village'): st.session_state['user_village'] = st.query_params.get('village')

st.markdown("""<style>@import url('https://fonts.googleapis.com/css2?family=Mukta+Vaani:wght@400;600;700;800&display=swap'); * { font-family: 'Mukta Vaani', sans-serif !important; } .tat-title { color: #000080; text-align: center; font-size: 30px; font-weight: 800; } .question-box { background-color: #f0f2f6; border-left: 5px solid #000080; padding: 15px; border-radius: 5px; font-size: 18px; margin-bottom: 20px; }</style>""", unsafe_allow_html=True)

# -----------------------------------------------------
# ૫. HTML રિપોર્ટ બનાવવાનું ફંક્શન
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
            st.query_params['mobile'] = mobile_id
            st.rerun()
        else:
            st.error("કૃપા કરીને ૧૦ આંકડાનો સાચો મોબાઈલ નંબર દાખલ કરો.")
else:
    try: st.image("Seminar Uma Academy.jpg", use_container_width=True)
    except: pass
    st.markdown("<div class='tat-title'>UCDC વિસનગર - TAT પેપર ચેકિંગ</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1: 
        st.session_state['user_name'] = st.text_input("પૂરું નામ (English):", value=st.session_state['user_name'])
        st.query_params['name'] = st.session_state['user_name']
    with col2: 
        st.session_state['user_village'] = st.text_input("ગામ/શહેર:", value=st.session_state['user_village'])
        st.query_params['village'] = st.session_state['user_village']
    with col3: 
        st.text_input("મોબાઈલ નંબર:", value=st.session_state['mobile_no'], disabled=True)

    category = st.selectbox("વિભાગ:", list(questions_dict.keys()))
    selected_display = st.selectbox("વિષય/પ્રશ્ન પસંદ કરો:", questions_dict[category])
    actual_q = re.sub(r'^\d+\. ', '', selected_display) if selected_display != "મારો પોતાનો પ્રશ્ન (Custom)" else ""
    if actual_q: st.markdown(f"<div class='question-box'>{actual_q}</div>", unsafe_allow_html=True)
    final_question_to_check = actual_q if actual_q else st.text_area("તમારો પ્રશ્ન:")

    uploaded_files = st.file_uploader("PDF અથવા ફોટા પસંદ કરો (આખું પેપર હોય તો બધી ફાઈલો સિલેક્ટ કરો)", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)

    if st.button("પેપર ચેક કરો 🚀"):
        has_patel = "PATEL" in st.session_state['user_name'].upper()
        if not st.session_state['user_name'] or not has_patel:
            st.error("❌ આ પોર્ટલ માત્ર 'પાટીદાર' વિદ્યાર્થીઓ માટે છે.")
        elif not uploaded_files:
            st.warning("⚠️ ફાઈલ અપલોડ કરો.")
        else:
            with st.spinner("⏳ પેપરનું ડીપ ચેકિંગ ચાલુ છે... (આખા પેપરનું લાઈન-બાય-લાઈન ચેકિંગ)"):
                try:
                    if category == "સંપૂર્ણ પેપર (૧૦૦ ગુણ)":
                        prompt = f"""
                        તમે માઁ ઉમા એકેડમી & UCDC વિસનગરના અત્યંત હોશિયાર, કડક અને સચોટ TAT 2026 મેઈન્સ ના પેપર ચેકર છો. 
                        વિદ્યાર્થીએ આખું 100 ગુણનું મોક ટેસ્ટ પેપર અપલોડ કર્યું છે.
                        
                        તમારો જવાબ હંમેશા: "જય માઁ ઉમાખોડલ અને જય સરદાર જય પાટીદાર" થી જ શરૂ કરો. 
                        
                        ⚠️ સૌથી મોટી સૂચના: તમારે આખા પેપરને સળંગ ૧ પ્રશ્ન ગણીને ટૂંકમાં ચેક નથી કરવાનું! તમારે દરેક પ્રશ્ન (૧ થી ૫) ને અલગ વ્યક્તિગત પેપર તરીકે ગણીને અત્યંત ડીપમાં ચેકિંગ કરવાનું છે.

                        📏 માર્કિંગના કડક નિયમો (આંતરિક - વિદ્યાર્થીને લિમિટ બતાવવી નહીં):
                        ૧. નિબંધ (૨૦ ગુણ): મહત્તમ ૧૪ ગુણ આપી શકાય.
                        ૨. સંક્ષેપીકરણ (૨૦ ગુણ): ૨ પ્રશ્નો, દરેકના મહત્તમ ૫ ગુણ.
                        ૩. પત્ર લેખન (૨૦ ગુણ): ૨ પ્રશ્નો, દરેકના મહત્તમ ૬ ગુણ.
                        ૪. ચર્ચાપત્ર (૨૦ ગુણ): ૨ પ્રશ્નો, દરેકના મહત્તમ ૬ ગુણ.
                        ૫. વ્યાકરણ (૨૦ ગુણ): ૨૦ પ્રશ્નો (સાચાનો ૧ ગુણ, સહેજ પણ ભૂલ હોય તો ૦ ગુણ).
                        - અંગ્રેજી શબ્દો (A-Z) વાપરવા પર મનાઈ છે, જો વાપરે તો માર્ક કાપવા.
                        - ઓળખ છતી (સાચું નામ/ગામ) થાય તો -૨ ગુણ કાપવા.
                        - ૩ જોડણી/વાક્યરચનાની ભૂલ પર -૦.૫ ગુણ કાપવા.

                        તમારે ફરજિયાત નીચે મુજબના ફોર્મેટમાં જ રિઝલ્ટ આપવાનું છે:

                        ---
                        ### પ્રશ્ન ૧: નિબંધ લેખન (૨૦ ગુણ)
                        - 📝 શબ્દ સંખ્યા અને એનાલિસિસ: (શબ્દમર્યાદા અને વિષયવસ્તુ તપાસો)
                        - ❌ ભૂલો અને ક્યાં માર્કસ કપાયા: (જોડણી, મૌલિકતાનો અભાવ વગેરે)
                        - 💡 વિસ્તૃત સલાહ: (શું ઉમેર્યું હોત તો વધુ માર્ક આવત)
                        - 🏆 મેળવેલ ગુણ: (૨૦ માંથી)

                        ### પ્રશ્ન ૨: સંક્ષેપીકરણ (કુલ ૨૦ ગુણ)
                        - 📝 એનાલિસિસ અને મૂળ વિચાર: 
                        - ❌ ભૂલો અને માર્કસ કાપવાનું કારણ: (શીર્ષક આપ્યું છે કે નહીં વગેરે)
                        - 💡 વિસ્તૃત સલાહ: 
                        - 🏆 મેળવેલ ગુણ: (કુલ ૨૦ માંથી)

                        ### પ્રશ્ન ૩: પત્ર લેખન (કુલ ૨૦ ગુણ)
                        - 📝 ફોર્મેટ અને ઔપચારિક ભાષાનું એનાલિસિસ: 
                        - ❌ ભૂલો (ફોર્મેટ/ભાષા): 
                        - 💡 વિસ્તૃત સલાહ: 
                        - 🏆 મેળવેલ ગુણ: (કુલ ૨૦ માંથી)

                        ### પ્રશ્ન ૪: ચર્ચાપત્ર (કુલ ૨૦ ગુણ)
                        - 📝 તટસ્થ રજૂઆત એનાલિસિસ: 
                        - ❌ ભૂલો: 
                        - 💡 વિસ્તૃત સલાહ: 
                        - 🏆 મેળવેલ ગુણ: (કુલ ૨૦ માંથી)

                        ### પ્રશ્ન ૫: વ્યાકરણ (૨૦ ગુણ)
                        - 📝 દરેક પ્રશ્નનું વિશ્લેષણ: (કયો સાચો પડ્યો, કયો ખોટો પડ્યો તેનું લિસ્ટ)
                        - 🏆 મેળવેલ ગુણ: (૨૦ માંથી)

                        ---
                        ### 📊 ફાઇનલ માર્કશીટ (૧૦૦ ગુણ)
                        (અહીં એક સુંદર ટેબલ બનાવો, જેમાં પ્રશ્ન ૧ થી ૫ ના મેળવેલ ગુણ હોય અને છેલ્લે કુલ ૧૦૦ માંથી ફાઇનલ ગુણ હોય.)
                        
                        ### 🎯 આખા પેપરનું એક્સપર્ટ માર્ગદર્શન (Overall Feedback):
                        (વિદ્યાર્થીને આખા પેપરમાં જે સામાન્ય ભૂલો કરી છે તેનું ડીપ માર્ગદર્શન આપો અને કઈ રીતે સ્કોર વધારી શકાય તે જણાવો. સંદર્ભ માટે GCERT, ગુજરાત પાક્ષિક સૂચવો.)
                        """
                    else:
                        # સિંગલ પ્રશ્ન માટે જૂનો કડક પ્રોમ્પ્ટ
                        if category == "નિબંધ લેખન":
                            total_marks, max_marks_allowed, expected_words = 20, 14, "આશરે ૨૫૦ થી ૩૦૦ શબ્દો"
                            category_rules = "✅ હકારાત્મક ગુણ: પ્રસ્તાવના/ઉપસંહાર (૪ ગુણ), વિષયવસ્તુ (૮ ગુણ), મૌલિકતા (૪ ગુણ), ભાષાકીય શુદ્ધિ (૪ ગુણ).\n❌ નકારાત્મક ગુણ: વિષયાંતર (-૩ થી -૫ ગુણ), મૌલિકતાનો અભાવ (-૨ ગુણ), શબ્દમર્યાદા ભંગ (-૧ થી -૨ ગુણ)."
                        elif category == "ચર્ચાપત્ર":
                            total_marks, max_marks_allowed, expected_words = 10, 6, "આશરે ૨૦૦ શબ્દો"
                            category_rules = "✅ હકારાત્મક ગુણ: ફોર્મેટ (૨ ગુણ), તટસ્થ રજૂઆત (૩ ગુણ), રચનાત્મક સૂચનો (૩ ગુણ), ઔપચારિક ભાષા (૨ ગુણ).\n❌ નકારાત્મક ગુણ: ફોર્મેટ ભૂલ (-૧ ગુણ પ્રતિ ભૂલ)."
                        elif category == "પત્ર લેખન":
                            total_marks, max_marks_allowed, expected_words = 10, 6, "આશરે ૧૦૦ શબ્દો"
                            category_rules = "✅ હકારાત્મક ગુણ: સત્તાવાર ફોર્મેટ (૩ ગુણ), સચોટ વિષયવસ્તુ (૪ ગુણ), સત્તાવાર શબ્દાવલિ (૩ ગુણ).\n❌ નકારાત્મક ગુણ: માળખાકીય ભૂલો (-૧ થી -૨ ગુણ)."
                        elif category == "સંક્ષેપીકરણ":
                            total_marks, max_marks_allowed, expected_words = 10, 5, "આશરે ૧/૩ (ત્રીજો) ભાગ"
                            category_rules = "✅ હકારાત્મક ગુણ: યોગ્ય શીર્ષક (૨ ગુણ), મૂળ વિચારની જાળવણી (૩ ગુણ), મૌલિકતા (૩ ગુણ), લંબાઈ અને શુદ્ધિ (૨ ગુણ).\n❌ નકારાત્મક ગુણ: શીર્ષકનો અભાવ (-૨ ગુણ), કોપી-પેસ્ટ (-૨ થી -૩ ગુણ)."
                        else:
                            total_marks, max_marks_allowed, expected_words = 20, 20, "લાગુ પડતું નથી"
                            category_rules = "✅ નિયમ: વ્યાકરણના દરેક પ્રશ્નનો ૧ ગુણ છે. જવાબ સંપૂર્ણ સાચો હોય તો જ ૧ ગુણ આપવો. સહેજ પણ ભૂલ હોય તો સીધો ૦ ગુણ આપવો. અડધો ગુણ આપવો જ નહીં."

                        prompt = f"""
                        તમે માઁ ઉમા એકેડમી & UCDC વિસનગરના અત્યંત હોશિયાર, કડક અને સચોટ TAT 2026 મેઈન્સ ના પેપર ચેકર છો. 
                        વિદ્યાર્થીએ '{category}' વિભાગમાં '{final_question_to_check}' વિષય પર જવાબ લખ્યો છે.
                        
                        તમારો જવાબ હંમેશા: "જય માઁ ઉમાખોડલ અને જય સરદાર જય પાટીદાર" થી જ શરૂ કરો. 

                        📏 વિભાગ અને માર્કિંગના કડક નિયમો:
                        - આ પ્રશ્ન કુલ {total_marks} ગુણનો છે. મહત્તમ લિમિટ ({max_marks_allowed}) થી વધુ ગુણ આપવા જ નહીં. 
                        - 'મહત્તમ આટલા જ મળી શકે' એવું રિઝલ્ટમાં ક્યાંય દર્શાવવું નહીં. માત્ર '{total_marks} માંથી મેળવેલ ગુણ' જ દર્શાવવા.
                        {category_rules}
                        - અંગ્રેજી શબ્દો (A-Z) નો પ્રયોગ સદંતર ટાળવો. જો વાપરે તો માર્ક કાપવા.
                        - દર ૩ જોડણી કે વાક્યરચનાની ભૂલ પર -૦.૫ ગુણ કાપવા.
                        - ઓળખ છતી (સાચું નામ/ગામ) થાય તો -૨ ગુણ કાપવા.

                        મૂલ્યાંકન નીચેના ૫ વિભાગમાં જ સુંદર રીતે આપવું:
                        ### ૧. અંદાજિત શબ્દ સંખ્યા અને એનાલિસિસ: 
                        ### ૨. ક્યાં માર્કસ કપાયા અને શા માટે? (Errors Analysis): 
                        ### ૩. વિભાગવાર માર્કિંગ અને મેળવેલ ગુણ (Out of {total_marks}): (સુંદર ટેબલ)
                        ### ૪. ભૂલોનું લિસ્ટ (સચોટ ચેકિંગ): 
                        ### ૫. વિસ્તૃત સલાહ અને માર્ગદર્શન (Expert Advice): 
                        (ફરજિયાત આ વાક્યનો પ્રયોગ કરો: "જો તમે આવું લખ્યું હોત અને આ [X, Y, Z ચોક્કસ મુદ્દાઓ] ઉમેર્યા હોત, તો તમારા માર્ક ચોક્કસ વધારે આવત.")
                        """
                    
                    contents = [prompt]
                    for file in uploaded_files:
                        if file.type == "application/pdf": contents.append(types.Part.from_bytes(data=file.read(), mime_type="application/pdf"))
                        else: contents.append(Image.open(file))
                    
                    response = client.models.generate_content(model=BEST_MODEL, contents=contents, config=types.GenerateContentConfig(temperature=0.0))
                    
                    # રિઝલ્ટ ને Session State માં સેવ કરીએ છીએ જેથી ડાઉનલોડ કરતી વખતે ગાયબ ન થાય.
                    st.session_state['checking_result'] = response.text
                    st.rerun()
                except Exception as e: st.error(f"❌ ભૂલ: {e}")

    # -----------------------------------------------------
    # ૭. રિઝલ્ટ અને ડાઉનલોડ બટન
    # -----------------------------------------------------
    # આ બ્લોક બહાર છે, એટલે ડાઉનલોડ કર્યા પછી પણ રિઝલ્ટ સ્ક્રીન પર રહેશે જ.
    if st.session_state['checking_result']:
        st.success("✅ ચેકિંગ પૂર્ણ!")
        st.markdown("---")
        st.markdown(st.session_state['checking_result'])
        
        # HTML રિપોર્ટ ડાઉનલોડ બટન
        report_data = create_html_report(st.session_state['checking_result'], st.session_state['user_name'])
        st.download_button(
            label="📥 રિઝલ્ટ ડાઉનલોડ કરો",
            data=report_data,
            file_name=f"Result_{st.session_state['user_name']}.html",
            mime="text/html"
        )
