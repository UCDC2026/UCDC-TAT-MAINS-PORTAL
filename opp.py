import streamlit as st
import re
from PIL import Image
from google import genai
from google.genai import types

# -----------------------------------------------------
# ૧. પેજ સેટિંગ અને API
# -----------------------------------------------------
st.set_page_config(page_title="UCDC Visnagar - TAT Mains Checker", page_icon="📝", layout="centered")

# તમારી API કી જે તમે સિક્રેટ્સમાં મૂકેલી છે તે જ લેશે
API_KEY = st.secrets["GEMINI_API_KEY"] 
client = genai.Client(api_key=API_KEY)

# મોડેલનું સૌથી સ્ટેબલ નામ (જે 404 એરર નહીં આપે)
BEST_MODEL = "gemini-flash-latest" 

# -----------------------------------------------------
# ૨. CSS અને ડિઝાઇન
# -----------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Mukta+Vaani:wght@400;600;700;800&display=swap'); 
    * { font-family: 'Mukta Vaani', sans-serif !important; } 
    .tat-title { color: #000080; text-align: center; font-size: 30px; font-weight: 800; margin-bottom: 20px;} 
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------
# ૩. HTML રિપોર્ટ ફંક્શન
# -----------------------------------------------------
def create_html_report(text):
    return f"""<html><body><pre style="white-space: pre-wrap;">{text}</pre></body></html>""".encode('utf-8')

# -----------------------------------------------------
# ૪. મેઈન પોર્ટલ
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
        with st.spinner("⏳ પેપરનું ડીપ ચેકિંગ ચાલુ છે..."):
            try:
                # દરેક કેટેગરી માટેના કડક રૂલ્સ
                if category == "સંપૂર્ણ પેપર-૧ (૧૦૦ ગુણ)":
                    category_rules = """
                    - નિબંધ (૨૦ ગુણ): મહત્તમ ૧૬ ગુણ. 
                    - સંક્ષેપીકરણ (૨ પ્રશ્નો): દરેકના મહત્તમ ૭ ગુણ.
                    - પત્ર લેખન (૨ પ્રશ્નો): દરેકના મહત્તમ ૭ ગુણ.
                    - ચર્ચાપત્ર (૨ પ્રશ્નો): દરેકના મહત્તમ ૭ ગુણ.
                    - વ્યાકરણ (૨૦ પ્રશ્નો): સાચાનો ૧ ગુણ, ખોટાનો ૦.
                    """
                else:
                    category_rules = "તમારા વિષય મુજબ કડક મૂલ્યાંકન કરવું."

                prompt = f"""
                તમે માઁ ઉમા એકેડમી & UCDC વિસનગરના અત્યંત કડક TAT મેઈન્સ પેપર ચેકર છો. 
                વિદ્યાર્થીએ '{category}' નું પેપર અપલોડ કર્યું છે.
                
                તમારો જવાબ હંમેશા: "જય માઁ ઉમાખોડલ અને જય સરદાર જય પાટીદાર" થી શરૂ કરો.

                📏 માર્કિંગના કડક નિયમો:
                {category_rules}
                - 'મહત્તમ લિમિટ' નો નિયમ આંતરિક છે, રિઝલ્ટમાં ક્યાંય લખવું નહીં કે 'તમને આટલા જ મળી શકે'.
                - અંગ્રેજી શબ્દોનો નિષેધ છે, ગુજરાતી ઉચ્ચાર વાપરવા.
                - જોડણી/વ્યાકરણની ૩ ભૂલ પર -૦.૫ ગુણ કાપવા.
                - ઓળખ છતી થાય (નામ/ગામ) તો -૨ ગુણ કાપવા.

                મૂલ્યાંકન નીચેના ૫ વિભાગમાં સુંદર રીતે આપો:
                ૧. અંદાજિત શબ્દ સંખ્યા અને એનાલિસિસ.
                ૨. ક્યાં માર્કસ કપાયા અને શા માટે? (Errors Analysis - ડીપમાં).
                ૩. વિભાગવાર માર્કિંગ અને મેળવેલ ગુણ (ટેબલ ફોર્મેટ - છેલ્લે કુલ ગુણ આપવા).
                ૪. ભૂલોનું લિસ્ટ (પોઈન્ટ્સમાં).
                ૫. 💡 એક્સપર્ટ સલાહ (સચોટ ટોપિક્સ અને સરકારી સ્ત્રોત મુજબ માર્ગદર્શન).
                """

                contents = [prompt]
                if question_paper_files:
                    contents.append("--- અસલ પ્રશ્નપત્ર ---")
                    for file in question_paper_files:
                        if file.type == "application/pdf": contents.append(types.Part.from_bytes(data=file.read(), mime_type="application/pdf"))
                        else: contents.append(Image.open(file))
                
                contents.append("--- વિદ્યાર્થીના જવાબો ---")
                for file in uploaded_files:
                    if file.type == "application/pdf": contents.append(types.Part.from_bytes(data=file.read(), mime_type="application/pdf"))
                    else: contents.append(Image.open(file))
                
                response = client.models.generate_content(model=BEST_MODEL, contents=contents, config=types.GenerateContentConfig(temperature=0.0))
                
                st.success("✅ ચેકિંગ પૂર્ણ!")
                st.markdown("---")
                st.markdown(response.text)
                
                st.download_button("📥 રિઝલ્ટ ડાઉનલોડ કરો", data=create_html_report(response.text), file_name="TAT_Result.html", mime="text/html")

            except Exception as e: st.error(f"❌ ભૂલ: {e}")
