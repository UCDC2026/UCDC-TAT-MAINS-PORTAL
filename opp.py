import streamlit as st
import re
from PIL import Image
from google import genai
from google.genai import types

# -----------------------------------------------------
# ૧. પેજ સેટિંગ અને API
# -----------------------------------------------------
st.set_page_config(page_title="UCDC Visnagar - TAT Mains Checker", page_icon="📝", layout="centered")

# નોંધ: જો નવી કી ડાયરેક્ટ કોડમાં મૂકવી હોય તો નીચેની લાઈન બદલીને API_KEY = "તમારી-કી" કરી દેવી.
API_KEY = st.secrets["GEMINI_API_KEY"] 
client = genai.Client(api_key=API_KEY)

# મોડેલનું લેટેસ્ટ અને ફાસ્ટ નામ
BEST_MODEL = "gemini-1.5-flash-latest" 

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
# ૩. મેઈન પોર્ટલ
# -----------------------------------------------------
try: 
    st.image("Seminar Uma Academy.jpg", use_container_width=True)
except: 
    pass

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

custom_question = st.text_area("તમારો પ્રશ્ન / વિષય અહીં લખો (જો પ્રશ્નપત્ર અપલોડ ન કરવું હોય તો):", placeholder="દા.ત. આર્ટિફિશિયલ ઇન્ટેલિજન્સ: વરદાન કે અભિશાપ?")

# --- નવું ઓપ્શન: પ્રશ્નપત્ર અને જવાબ બંને અલગ અલગ અપલોડ કરવા ---
st.markdown("---")
st.markdown("#### 📄 પેપર અપલોડ સેક્શન")
question_paper_files = st.file_uploader("૧. અસલ પ્રશ્નપત્ર અપલોડ કરો (Optional / મરજિયાત)", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)
uploaded_files = st.file_uploader("૨. વિદ્યાર્થીના જવાબોની PDF અથવા ફોટા અપલોડ કરો (ફરજિયાત)", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)

if st.button("પેપર ચેક કરો 🚀"):
    if not uploaded_files:
        st.warning("⚠️ કૃપા કરીને વિદ્યાર્થીના જવાબો અપલોડ કરો.")
    elif not custom_question and not question_paper_files and category != "સંપૂર્ણ પેપર-૧ (૧૦૦ ગુણ)" and category != "પેપર-૨: વિષય વસ્તુ અને પદ્ધતિ શાસ્ત્ર (સંપૂર્ણ પેપર)":
        st.warning("⚠️ કૃપા કરીને પ્રશ્ન લખો અથવા પ્રશ્નપત્ર અપલોડ કરો.")
    else:
        with st.spinner("⏳ પેપરનું ડીપ ચેકિંગ ચાલુ છે..."):
            try:
                # માર્કિંગ રૂલ્સ 
                if category == "સંપૂર્ણ પેપર-૧ (૧૦૦ ગુણ)":
                    total_marks = 100
                    category_rules = "✅ નિયમ: આખા પેપરનું સળંગ મૂલ્યાંકન ન કરવું. પ્રશ્ન ૧ થી ૫ નું અલગ-અલગ ડીપ એનાલિસિસ કરવું. નિબંધ (મેક્સ ૧૬ ગુણ), સંક્ષેપીકરણ (મેક્સ ૭ ગુણ), પત્ર (મેક્સ ૭ ગુણ), ચર્ચાપત્ર (મેક્સ ૭ ગુણ), વ્યાકરણ (સાચાનો ૧ ગુણ, ખોટાનો ૦)."
                elif category == "નિબંધ લેખન (૨૦ ગુણ)":
                    total_marks = 20
                    category_rules = "✅ નિયમ: પ્રસ્તાવના, વિષયવસ્તુ, મૌલિકતા તપાસવા. મહત્તમ લિમિટ ૧૬ ગુણથી વધુ આપવા નહીં."
                elif category == "સંક્ષેપીકરણ (૧૦ ગુણ)":
                    total_marks = 10
                    category_rules = "✅ નિયમ: યોગ્ય શીર્ષક અને મૂળ વિચારની જાળવણી. મહત્તમ લિમિટ ૭ ગુણથી વધુ આપવા નહીં."
                elif category == "પત્ર લેખન (૧૦ ગુણ)":
                    total_marks = 10
                    category_rules = "✅ નિયમ: સત્તાવાર ફોર્મેટ અને શબ્દાવલિ તપાસવી. મહત્તમ લિમિટ ૭ ગુણથી વધુ આપવા નહીં."
                elif category == "ચર્ચાપત્ર (૧૦ ગુણ)":
                    total_marks = 10
                    category_rules = "✅ નિયમ: ફોર્મેટ અને તટસ્થ રજૂઆત. મહત્તમ લિમિટ ૭ ગુણથી વધુ આપવા નહીં."
                elif category == "વ્યાકરણ (૨૦ ગુણ)":
                    total_marks = 20
                    category_rules = "✅ નિયમ: દરેક પ્રશ્નનો ૧ ગુણ. સંપૂર્ણ સાચો હોય તો જ ૧ ગુણ આપવો. સહેજ પણ ભૂલ હોય તો સીધો ૦ ગુણ."
                else: 
                    total_marks = 100
                    category_rules = "✅ નિયમ: વિષય વસ્તુ અને પદ્ધતિ શાસ્ત્રના પ્રશ્નોનું ઊંડાણપૂર્વક વિશ્લેષણ કરવું. સાચા જવાબો અને સિલેબસ મુજબ ચોકસાઈ તપાસવી."

                prompt = f"""
                તમે માઁ ઉમા એકેડમી & UCDC વિસનગરના અત્યંત કડક TAT મેઈન્સ પેપર ચેકર છો. 
                વિદ્યાર્થીએ '{category}' વિભાગમાં જવાબ લખ્યો છે.
                શિક્ષકે આપેલો પ્રશ્ન/વિષય (જો લખ્યો હોય તો): {custom_question}
                
                તમારો જવાબ હંમેશા: "જય માઁ ઉમાખોડલ અને જય સરદાર જય પાટીદાર" થી જ શરૂ કરો.

                📏 માર્કિંગના કડક નિયમો:
                {category_rules}
                - 'મહત્તમ લિમિટ' નો નિયમ આંતરિક છે, રિઝલ્ટમાં ક્યાંય દર્શાવવું નહીં કે 'તમને આટલા જ મળી શકે'.
                - લખાણમાં અંગ્રેજી મૂળાક્ષરો (A-Z) નો પ્રયોગ સદંતર ટાળવો.
                - દર ૩ જોડણી કે વાક્યરચનાની ભૂલ પર -૦.૫ ગુણ કાપવા.
                - ઓળખ છતી: પત્ર/ચર્ચાપત્રમાં સાચું નામ લખ્યું હોય તો -૨ ગુણ કાપવા.

                મૂલ્યાંકન સુંદર ફોર્મેટમાં આપો:
                ૧. અંદાજિત શબ્દ સંખ્યા અને એનાલિસિસ.
                ૨. ક્યાં માર્કસ કપાયા (Errors Analysis).
                ૩. વિભાગવાર માર્કિંગ અને મેળવેલ ગુણ (ટેબલ ફોર્મેટ).
                ૪. ભૂલોનું લિસ્ટ.
                ૫. 💡 એક્સપર્ટ સલાહ.
                """

                contents = [prompt]
                
                # ૧. જો પ્રશ્નપત્ર અપલોડ કર્યું હોય તો તે ઉમેરવું
                if question_paper_files:
                    contents.append("--- અસલ પ્રશ્નપત્ર (Question Paper) નીચે મુજબ છે ---")
                    for file in question_paper_files:
                        if file.type == "application/pdf": 
                            contents.append(types.Part.from_bytes(data=file.read(), mime_type="application/pdf"))
                        else: 
                            contents.append(Image.open(file))
                
                # ૨. વિદ્યાર્થીના જવાબો ઉમેરવા
                contents.append("--- વિદ્યાર્થીના જવાબો (Answer Sheet) નીચે મુજબ છે ---")
                for file in uploaded_files:
                    if file.type == "application/pdf": 
                        contents.append(types.Part.from_bytes(data=file.read(), mime_type="application/pdf"))
                    else: 
                        contents.append(Image.open(file))
                
                # AI મોડેલને રિક્વેસ્ટ મોકલવી
                response = client.models.generate_content(
                    model=BEST_MODEL, 
                    contents=contents, 
                    config=types.GenerateContentConfig(temperature=0.0)
                )
                
                st.success("✅ ચેકિંગ પૂર્ણ!")
                st.markdown("---")
                st.markdown(response.text)

            except Exception as e: 
                st.error(f"❌ ભૂલ: {e}")
