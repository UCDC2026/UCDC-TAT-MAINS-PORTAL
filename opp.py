import streamlit as st
import re
from PIL import Image
from google import genai
from google.genai import types

# -----------------------------------------------------
# ૧. પેજ સેટિંગ અને API
# -----------------------------------------------------
st.set_page_config(page_title="UCDC Visnagar - TAT Mains Checker", page_icon="📝", layout="centered")

API_KEY = st.secrets["GEMINI_API_KEY"] 
client = genai.Client(api_key=API_KEY)
BEST_MODEL = "gemini-1.5-flash-latest" 

# -----------------------------------------------------
# ૨. સ્ટેટ મેનેજમેન્ટ (રિઝલ્ટ ગાયબ ન થાય તે માટે)
# -----------------------------------------------------
if 'checking_result' not in st.session_state:
    st.session_state['checking_result'] = None

# -----------------------------------------------------
# ૩. CSS અને ડિઝાઇન
# -----------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Mukta+Vaani:wght@400;600;700;800&display=swap'); 
    * { font-family: 'Mukta Vaani', sans-serif !important; } 
    .tat-title { color: #000080; text-align: center; font-size: 30px; font-weight: 800; margin-bottom: 20px;} 
</style>
""", unsafe_allow_html=True)

def create_html_report(text):
    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>UCDC Result</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; line-height: 1.6; color: #000; background-color: #fff; }}
            h2 {{ color: #000080; text-align: center; border-bottom: 2px solid #000080; padding-bottom: 10px; margin-bottom: 20px; }}
            .content {{ white-space: pre-wrap; font-size: 16px; }}
        </style>
    </head>
    <body>
        <h2>UCDC Visnagar - TAT Mains Result</h2>
        <div class="content">{text}</div>
    </body>
    </html>
    """
    return html_content.encode('utf-8')

# -----------------------------------------------------
# ૪. મેઈન UI (તમારી સૂચના મુજબ એકદમ શોર્ટ)
# -----------------------------------------------------
try: st.image("Seminar Uma Academy.jpg", use_container_width=True)
except: pass

st.markdown("<div class='tat-title'>UCDC વિસનગર - એડવાન્સ પેપર ચેકિંગ</div>", unsafe_allow_html=True)

category = st.selectbox("કયો વિભાગ ચેક કરવો છે?", [
    "સંપૂર્ણ પેપર-૧ (૧૦૦ ગુણ)",
    "નિબંધ લેખન (૨૦ ગુણ)",
    "સંક્ષેપીકરણ (૧૦ ગુણ)",
    "પત્ર લેખન (૧૦ ગુણ)",
    "ચર્ચાપત્ર (૧૦ ગુણ)",
    "વ્યાકરણ (૨૦ ગુણ)",
    "પેપર-૨: વિષય વસ્તુ અને પદ્ધતિ શાસ્ત્ર (સંપૂર્ણ પેપર)"
])

custom_question = st.text_area("તમારો પ્રશ્ન / વિષય અહીં લખો:", placeholder="દા.ત. આર્ટિફિશિયલ ઇન્ટેલિજન્સ: વરદાન કે અભિશાપ?")

st.markdown("---")
st.markdown("#### 📄 પેપર અપલોડ સેક્શન")
question_paper_files = st.file_uploader("૧. અસલ પ્રશ્નપત્ર અપલોડ કરો (Optional)", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)
uploaded_files = st.file_uploader("૨. વિદ્યાર્થીના જવાબોની PDF/ફોટા અપલોડ કરો (ફરજિયાત)", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)

if st.button("પેપર ચેક કરો 🚀"):
    if not uploaded_files:
        st.warning("⚠️ કૃપા કરીને વિદ્યાર્થીના જવાબો અપલોડ કરો.")
    else:
        with st.spinner("⏳ પેપરનું ડીપ ચેકિંગ ચાલુ છે... (દરેક પ્રશ્નનું લાઈન-બાય-લાઈન એનાલિસિસ)"):
            try:
                # --- ડીપ ચેકિંગ પ્રોમ્પ્ટ્સ ---
                if category == "સંપૂર્ણ પેપર-૧ (૧૦૦ ગુણ)":
                    prompt = f"""
                    તમે માઁ ઉમા એકેડમી & UCDC વિસનગરના અત્યંત હોશિયાર, કડક અને સચોટ TAT 2026 મેઈન્સ ના પેપર ચેકર છો. 
                    વિદ્યાર્થીએ આખું મોક ટેસ્ટ પેપર અપલોડ કર્યું છે. શિક્ષકે આપેલો પ્રશ્નપત્ર/સૂચના: {custom_question}
                    
                    તમારો જવાબ હંમેશા: "જય માઁ ઉમાખોડલ અને જય સરદાર જય પાટીદાર" થી જ શરૂ કરો. 
                    
                    ⚠️ સૌથી મોટી સૂચના: તમારે આખા પેપરને સળંગ ૧ પ્રશ્ન ગણીને શોર્ટમાં નથી પતાવવાનું! તમારે ફરજિયાત પ્રશ્ન ૧ થી ૫ ને અલગ સેક્શન બનાવીને અત્યંત ડીપમાં ચેકિંગ કરવાનું છે.

                    📏 માર્કિંગના કડક નિયમો:
                    ૧. નિબંધ (૨૦ ગુણ): મહત્તમ ૧૬ ગુણ આપી શકાય.
                    ૨. સંક્ષેપીકરણ (૧૦ ગુણ): મહત્તમ ૭ ગુણ આપી શકાય.
                    ૩. પત્ર લેખન (૧૦ ગુણ): મહત્તમ ૭ ગુણ આપી શકાય.
                    ૪. ચર્ચાપત્ર (૧૦ ગુણ): મહત્તમ ૭ ગુણ આપી શકાય.
                    ૫. વ્યાકરણ (૨૦ ગુણ): દરેક સાચા જવાબનો ૧ ગુણ, સહેજ પણ ભૂલ હોય તો ૦ ગુણ.
                    - અંગ્રેજી શબ્દો (A-Z) વાપરવા પર મનાઈ છે, જો વાપરે તો માર્ક કાપવા.
                    - ઓળખ છતી (સાચું નામ/ગામ) થાય તો સીધા -૨ ગુણ કાપવા.
                    - ૩ જોડણી/વાક્યરચનાની ભૂલ પર -૦.૫ ગુણ કાપવા.

                    તમારે નીચે મુજબના ફોર્મેટમાં જ રિઝલ્ટ આપવાનું છે:

                    ---
                    ### પ્રશ્ન ૧: નિબંધ લેખન (૨૦ ગુણ)
                    - 📝 વિશ્લેષણ: (શબ્દમર્યાદા ૨૫૦-૩૦૦ અને વિષયવસ્તુ તપાસો)
                    - ❌ ભૂલો: (ક્યાં માર્કસ કપાયા અને કઈ જોડણી ખોટી છે)
                    - 💡 સલાહ: (શું ઉમેર્યું હોત તો વધુ માર્ક આવત)
                    - 🏆 મેળવેલ ગુણ: (૨૦ માંથી)

                    ### પ્રશ્ન ૨: સંક્ષેપીકરણ (૧૦ ગુણ)
                    - 📝 વિશ્લેષણ અને મૂળ વિચાર: 
                    - ❌ ભૂલો અને માર્કસ કાપવાનું કારણ: 
                    - 💡 સલાહ: 
                    - 🏆 મેળવેલ ગુણ: (૧૦ માંથી)

                    ### પ્રશ્ન ૩: પત્ર લેખન (૧૦ ગુણ)
                    - 📝 ફોર્મેટ અને ઔપચારિક ભાષાનું વિશ્લેષણ: 
                    - ❌ ભૂલો (ફોર્મેટ/ભાષા): 
                    - 💡 સલાહ: 
                    - 🏆 મેળવેલ ગુણ: (૧૦ માંથી)

                    ### પ્રશ્ન ૪: ચર્ચાપત્ર (૧૦ ગુણ)
                    - 📝 તટસ્થ રજૂઆત વિશ્લેષણ: 
                    - ❌ ભૂલો: 
                    - 💡 સલાહ: 
                    - 🏆 મેળવેલ ગુણ: (૧૦ માંથી)

                    ### પ્રશ્ન ૫: વ્યાકરણ (૨૦ ગુણ)
                    - 📝 દરેક પ્રશ્નનું વિશ્લેષણ: (કયો સાચો પડ્યો, કયો ખોટો)
                    - 🏆 મેળવેલ ગુણ: (૨૦ માંથી)

                    ---
                    ### 📊 ફાઇનલ માર્કશીટ (૧૦૦ ગુણ)
                    (અહીં સુંદર ટેબલ બનાવો, જેમાં પ્રશ્ન ૧ થી ૫ ના ગુણ અને છેલ્લે કુલ ગુણ હોય.)
                    
                    ### 🎯 ઓવરઓલ માર્ગદર્શન (Overall Feedback):
                    (વિદ્યાર્થીની સામાન્ય ભૂલો અને સ્કોર કઈ રીતે વધારવો તેની ડીપ માહિતી.)
                    """
                else:
                    prompt = f"""
                    તમે માઁ ઉમા એકેડમી & UCDC વિસનગરના અત્યંત કડક TAT મેઈન્સ પેપર ચેકર છો. 
                    વિદ્યાર્થીએ '{category}' નો જવાબ લખ્યો છે. પ્રશ્ન: {custom_question}
                    
                    તમારો જવાબ હંમેશા: "જય માઁ ઉમાખોડલ અને જય સરદાર જય પાટીદાર" થી શરૂ કરો. 

                    📏 નિયમો:
                    - નિબંધ હોય તો મેક્સિમમ ૧૬ ગુણ. સંક્ષેપ, પત્ર, ચર્ચાપત્ર હોય તો મેક્સિમમ ૭ ગુણ. વ્યાકરણ હોય તો સાચાનો ૧, ખોટાનો ૦.
                    - અંગ્રેજી શબ્દો (A-Z) નો પ્રયોગ ટાળવો.
                    - દર ૩ ભૂલ પર -૦.૫ ગુણ કાપવા. ઓળખ છતી થાય તો -૨ ગુણ કાપવા.

                    નીચેના ૫ વિભાગમાં સુંદર રીતે મૂલ્યાંકન આપવું:
                    ### ૧. એનાલિસિસ: 
                    ### ૨. ભૂલો (Errors): 
                    ### ૩. વિભાગવાર માર્કિંગ (ટેબલ): 
                    ### ૪. ભૂલોનું લિસ્ટ: 
                    ### ૫. 💡 એક્સપર્ટ સલાહ: 
                    """

                contents = [prompt]
                if question_paper_files:
                    contents.append("--- પ્રશ્નપત્ર ---")
                    for file in question_paper_files:
                        if file.type == "application/pdf": contents.append(types.Part.from_bytes(data=file.read(), mime_type="application/pdf"))
                        else: contents.append(Image.open(file))
                
                contents.append("--- જવાબો ---")
                for file in uploaded_files:
                    if file.type == "application/pdf": contents.append(types.Part.from_bytes(data=file.read(), mime_type="application/pdf"))
                    else: contents.append(Image.open(file))
                
                response = client.models.generate_content(model=BEST_MODEL, contents=contents, config=types.GenerateContentConfig(temperature=0.0))
                
                # રિઝલ્ટ સેવ કરીએ છીએ જેથી ડાઉનલોડ વખતે રિફ્રેશ ન થાય
                st.session_state['checking_result'] = response.text
                st.rerun()

            except Exception as e: 
                st.error(f"❌ ભૂલ: {e}")

# -----------------------------------------------------
# ૫. રિઝલ્ટ પ્રિન્ટ અને ડાઉનલોડ 
# -----------------------------------------------------
if st.session_state['checking_result']:
    st.success("✅ ચેકિંગ પૂર્ણ!")
    st.markdown("---")
    st.markdown(st.session_state['checking_result'])
    
    report_data = create_html_report(st.session_state['checking_result'])
    st.download_button(
        label="📥 રિઝલ્ટ ડાઉનલોડ કરો",
        data=report_data,
        file_name="TAT_Mains_Result.html",
        mime="text/html"
    )
