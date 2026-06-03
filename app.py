import streamlit as st
import urllib.request
import urllib.error
import json
import os
import datetime
import ssl

# --- הגדרות עיצוב בסיסיות ---
st.set_page_config(page_title="CaPow Smart Fridge", page_icon="⚡")

# הזרקת קוד CSS - שילוב של RTL ועיצוב מותאם אישית לחברת CaPow
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;700;900&display=swap');

    /* הופך את כל האפליקציה לימין-לשמאל ומשנה פונט למודרני */
    .stApp, .stApp > header, .stApp .main {
        direction: rtl;
        font-family: 'Heebo', sans-serif !important;
    }
    
    /* מכריח את כל הטקסטים והתוויות להתיישר לימין */
    * {
        text-align: right !important;
    }
    
    /* --- עיצוב בהשראת CaPow Energy --- */
    
    /* טקסט כותרת עם גרדיאנט "אנרגטי" */
    .capow-title {
        background: linear-gradient(90deg, #0052D4 0%, #4364F7 50%, #6FB1FC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
    }

    /* תיקון עבור תיבת הבחירה */
    div[data-baseweb="select"] {
        direction: rtl;
    }
    
    /* עיצוב משודרג לשדות טקסט ובחירה */
    div[data-baseweb="base-input"] > div, div[data-baseweb="select"] > div {
        border-radius: 10px !important;
        border: 1.5px solid #d1d5db !important;
        background-color: #f9fafb !important;
        transition: all 0.3s ease;
    }
    
    /* אפקט פוקוס (זוהר אנרגטי כחול) */
    div[data-baseweb="base-input"] > div:focus-within, div[data-baseweb="select"] > div:focus-within {
        border-color: #4364F7 !important;
        box-shadow: 0 0 10px rgba(67, 100, 247, 0.2) !important;
    }
    
    /* יישור טקסט בשדות הקלדה */
    div[data-baseweb="base-input"] input {
        direction: rtl;
        font-weight: bold;
    }

    /* עיצוב כפתורים בסגנון סטארטאפ */
    .stButton {
        display: flex;
        justify-content: flex-start;
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #4364F7, #6FB1FC) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        font-weight: 700 !important;
        transition: all 0.3s ease !important;
        border-bottom: 3px solid #0052D4 !important;
    }
    
    /* אפקט ריחוף לכפתור */
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 15px rgba(67, 100, 247, 0.3) !important;
        border-bottom-width: 3px !important;
        color: white !important;
    }
    
    .stButton > button:active {
        transform: translateY(1px) !important;
        border-bottom-width: 0px !important;
        box-shadow: none !important;
    }
    
    /* עיצוב התראות (ההודעות הירוקות/צהובות) */
    div[data-testid="stAlert"] {
        direction: rtl;
        border-radius: 10px !important;
        border-right: 5px solid #4364F7 !important;
        border-left: none !important;
    }
    
    /* סגנון לקו המפריד */
    hr {
        border-top: 2px dashed #e5e7eb !important;
    }
</style>
""", unsafe_allow_html=True)

# --- הגדרת מערכת הלוגים המקומית ---
LOG_FILE = "app_logs.txt"

def log_event(level, message):
    """רישום אירועים לקובץ לוגים מקומי"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {message}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception:
        pass

# אתחול לוג ראשוני
if not os.path.exists(LOG_FILE):
    log_event("SYSTEM", "מערכת הלוגים של CaPow Smart Fridge אותחלה בהצלחה.")

# --- כותרת ממותגת נקייה ---
st.markdown('<h1 style="text-align: right; margin-top: 20px;">המקרר החכם של <span class="capow-title">CaPow</span> ⚡</h1>', unsafe_allow_html=True)
st.markdown('<div style="text-align: right;"><p dir="ltr" style="direction: ltr; display: inline-block; font-size: 1.1rem; color: #6b7280; margin-top: -15px; margin-bottom: 30px;">100% Uptime for our team\'s energy!</p></div>', unsafe_allow_html=True)

# --- הגדרות חיבור מאובטח לענן (Streamlit Secrets) ---
# המפתחות נשמרים בצורה מאובטחת בענן של Streamlit ולא נחשפים בקוד הציבורי ב-GitHub!
JSONBIN_API_KEY = st.secrets.get("JSONBIN_API_KEY")
JSONBIN_BIN_ID = st.secrets.get("JSONBIN_BIN_ID")

# יצירת הקשר SSL לא מאומת כדי למנוע בעיות אבטחה בשרת Streamlit
try:
    ssl_context = ssl._create_unverified_context()
except Exception:
    ssl_context = None

# בדיקה ידידותית למשתמש למקרה שהמפתחות טרם הוגדרו בלוח הבקרה
if not JSONBIN_API_KEY or not JSONBIN_BIN_ID:
    st.info("👋 ברוכים הבאים למקרר החכם של CaPow!")
    st.markdown("""
    ### 🔐 שלב אחרון להפעלת הענן בצורה מאובטחת (Secrets):
    מכיוון שקוד ה-GitHub שלכם ציבורי, **אסור** לרשום את המפתחות ישירות בקוד! במקום זאת, נשמור אותם במערכת ה-Secrets המאובטחת של Streamlit:
    
    #### בשרת האינטרנט (Streamlit Cloud):
    1. כנסו ללוח הבקרה שלכם ב-**[share.streamlit.io](https://share.streamlit.io/)**.
    2. ליד האפליקציה שלכם, לחצו על שלוש הנקודות (**...**) ובחרו ב-**Settings**.
    3. עברו ללשונית **Secrets** בצד שמאל.
    4. הדביקו שם את השורות הבאות (החליפו במפתחות האמיתיים שלכם מהאתר `jsonbin.io`):
       ```toml
       JSONBIN_API_KEY = "ה-Master Key שלכם"
       JSONBIN_BIN_ID = "ה-Bin ID שלכם"
       ```
    5. לחצו על **Save** והאפליקציה שלכם תתעדכן, תתחבר ותעלה לאוויר באופן מאובטח ותקין לחלוטין!
    
    #### בהרצה מקומית על המחשב (במידה ותרצו):
    1. בתיקיית הפרויקט במחשב, צרו תיקייה חדשה בשם `.streamlit`
    2. בתוכה צרו קובץ בשם `secrets.toml`
    3. רשמו בתוכו את המפתחות באותו פורמט (כמו בשלב 4 למעלה).
    4. **חשוב:** וודאו שהתיקייה `.streamlit/` נמצאת בקובץ ה-`.gitignore` שלכם כדי שהיא לא תעלה בטעות ל-GitHub!
    """)
    st.stop()

# פונקציות עזר לקריאה וכתיבה מ-JSONBin.io
def load_all_data():
    url = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}/latest"
    headers = {
        "X-Master-Key": JSONBIN_API_KEY,
        "User-Agent": "Mozilla/5.0"
    }
    log_event("INFO", "מנסה לטעון נתונים מ-JSONBin.io...")
    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=5, context=ssl_context) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            log_event("INFO", "טעינת הנתונים מהענן עברה בהצלחה!")
            return res_data.get("record", {})
    except Exception as e:
        log_event("ERROR", f"שגיאה בטעינה מהענן: {str(e)}")
        
        # fallback לגיבוי מקומי
        log_event("WARNING", "מנסה לטעון מקובץ גיבוי מקומי...")
        if os.path.exists("local_backup.json"):
            try:
                with open("local_backup.json", "r", encoding="utf-8") as f:
                    log_event("INFO", "טעינה מגיבוי מקומי הצליחה!")
                    return json.load(f)
            except Exception as le:
                log_event("ERROR", f"שגיאה בקריאת הגיבוי המקומי: {str(le)}")
                
        return {"products_catalog": [], "shopping_list": []}

def save_all_data(data):
    # שומרים קודם כל גיבוי מקומי במחשב למקרה של ניתוק
    try:
        with open("local_backup.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        log_event("INFO", "גיבוי מקומי נשמר בהצלחה.")
    except Exception as e:
        log_event("ERROR", f"שגיאה בשמירת גיבוי מקומי: {str(e)}")

    url = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}"
    headers = {
        "X-Master-Key": JSONBIN_API_KEY,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    log_event("INFO", "מנסה לעדכן את קובץ הנתונים בענן של JSONBin.io...")
    try:
        payload = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=payload, headers=headers, method="PUT")
        with urllib.request.urlopen(req, timeout=5, context=ssl_context) as response:
            log_event("INFO", "עדכון הענן עבר בהצלחה מושלמת!")
            return True
    except Exception as e:
        log_event("ERROR", f"עדכון הענן נכשל: {str(e)}")
        return False

# טעינת המידע החי מהענן בזמן אמת!
db_data = load_all_data()
PRODUCTS = db_data.get("products_catalog", [])
shopping_list = db_data.get("shopping_list", [])

# --- אזור הוספת מוצרים ---
st.write("מה חסר במקרר?")

selected_product = st.selectbox("חיפוש מוצר קיים:", PRODUCTS)
custom_product = st.text_input("לא מצאת ברשימה? הקלד כאן (המוצר יישמר לפעמים הבאות):")

if st.button("הוסף לרשימה ➕"):
    item_to_add = ""
    
    if custom_product:
        item_to_add = custom_product
        if custom_product not in PRODUCTS:
            PRODUCTS.append(custom_product)
            db_data["products_catalog"] = PRODUCTS
            save_all_data(db_data)
    elif selected_product != "בחר מהרשימה...":
        item_to_add = selected_product
        
    if item_to_add:
        if item_to_add not in shopping_list:
            shopping_list.append(item_to_add)
            db_data["shopping_list"] = shopping_list
            if save_all_data(db_data):
                st.success(f"מעולה! '{item_to_add}' התווסף למאגר האנרגיה שלנו.")
            else:
                st.success(f"מעולה! '{item_to_add}' נשמר באופן מקומי (מצב אופליין זמני).")
            st.rerun()
        else:
            st.warning(f"'{item_to_add}' כבר נמצא ברשימה!")
    else:
        st.warning("אנא בחר מוצר או הקלד אחד חדש.")

st.divider()

# --- אזור רשימת הקניות (לקניין) ---
st.subheader("רשימת הקניות הנוכחית 🛒")

if shopping_list:
    for item in shopping_list:
        st.write(f"⚡ {item}")
    
    st.write("")
    if st.button("טעינה הושלמה! (מחיקת הרשימה) 🗑️"):
        db_data["shopping_list"] = []
        if save_all_data(db_data):
            st.success("הרשימה אופסה בהצלחה בענן!")
        else:
            st.success("הרשימה אופסה מקומית (מצב אופליין).")
        st.rerun()
else:
    st.info("אין חוסרים. הרובוטים יכולים להמשיך לנוע! 🤖")

st.divider()

# --- מרכז בקרה, בדיקת חיבור ולוגים (למנהל המערכת) ---
with st.expander("🛠️ מרכז בקרה, לוגים וחיבור לענן"):
    st.markdown("### אבחון וניטור חיבור המערכת")
    
    if st.button("🔌 בדיקת חיבור מהירה לענן"):
        test_success = save_all_data(db_data)
        if test_success:
            st.success("החיבור לענן תקין לחלוטין! (100% Uptime) ⚡")
            log_event("SYSTEM", "בדיקת חיבור יזומה עברה בהצלחה.")
        else:
            st.error("החיבור לענן נכשל. המערכת פועלת כרגע במצב גיבוי מקומי יציב.")
            log_event("SYSTEM", "בדיקת חיבור יזומה נכשלה.")
            
    st.write("📋 לוגים של האפליקציה (app_logs.txt):")
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs_content = f.read()
        st.text_area("לוגים של השרת", logs_content, height=250, disabled=True)
        
        if st.button("🗑️ נקה לוגים"):
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.write("")
            st.success("קובץ הלוגים נוקה בהצלחה.")
            st.rerun()
    else:
        st.info("אין לוגים זמינים כרגע.")
