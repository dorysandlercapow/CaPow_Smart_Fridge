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

# --- הגדרות מסד הנתונים בענן (kvdb.io) ---
# מזהה תיקייה תקין ב-100% (מתחיל ב-0 ובאורך של 20 תווים בדיוק)
DB_BUCKET_ID = "0capowfridge2026upti"
SHOPPING_LIST_KEY = "shopping_list"
CATALOG_KEY = "products_catalog"

# הגדרת כותרות דפדפן (Headers) קבועות כדי למנוע חסימה של שרתי ה-API בענן
REQUEST_HEADERS = {
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# יצירת הקשר SSL לא מאומת כדי לעקוף בעיות תעודה פוטנציאליות בשרת ה-Streamlit
try:
    ssl_context = ssl._create_unverified_context()
except Exception:
    ssl_context = None

# פונקציות עזר לקריאה וכתיבה מהענן עם מנגנון גיבוי מקומי אוטומטי (Fallback)
def get_from_cloud(key, default_value):
    url = f"https://kvdb.io/{DB_BUCKET_ID}/{key}"
    log_event("INFO", f"מנסה לקרוא נתונים מ-kvdb.io עבור המפתח: {key}")
    try:
        req = urllib.request.Request(url, headers=REQUEST_HEADERS, method="GET")
        # שימוש ב-ssl_context לעקיפת שגיאות תעודת אבטחה בענן
        with urllib.request.urlopen(req, timeout=5, context=ssl_context) as response:
            data_str = response.read().decode('utf-8')
            log_event("INFO", f"קריאה מהענן הצליחה עבור המפתח: {key}")
            return json.loads(data_str)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            log_event("WARNING", f"המפתח {key} לא נמצא עדיין בענן (שגיאת 404). מחזיר ערך ברירת מחדל.")
            return default_value
        else:
            log_event("ERROR", f"שגיאת HTTP {e.code} בקריאה משרת kvdb.io עבור {key}: {e.reason}")
    except Exception as e:
        log_event("ERROR", f"שגיאה כללית בקריאה משרת kvdb.io עבור {key}: {str(e)}")
    
    # שלב הגיבוי המקומי במידה והענן לא זמין
    log_event("WARNING", f"הקריאה מ-kvdb.io נכשלה. מנסה לקרוא מקובץ גיבוי מקומי עבור {key}...")
    local_file = f"local_backup_{key}.json"
    if os.path.exists(local_file):
        try:
            with open(local_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                log_event("INFO", f"קריאה מקובץ גיבוי מקומי הצליחה עבור {key}")
                return data
        except Exception as local_err:
            log_event("ERROR", f"שגיאה בקריאת הגיבוי המקומי עבור {key}: {str(local_err)}")
    
    return default_value

def save_to_cloud(key, data):
    # שומרים קודם כל גיבוי מקומי במקרה של ניתוק עתידי
    local_file = f"local_backup_{key}.json"
    try:
        with open(local_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        log_event("INFO", f"שמירת גיבוי מקומי הצליחה עבור {key}")
    except Exception as local_err:
        log_event("ERROR", f"שגיאה בשמירת גיבוי מקומי עבור {key}: {str(local_err)}")

    # כתיבה לענן kvdb.io
    url = f"https://kvdb.io/{DB_BUCKET_ID}/{key}"
    log_event("INFO", f"מנסה לשמור נתונים לשרת kvdb.io עבור {key}...")
    try:
        payload = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=payload,
            headers=REQUEST_HEADERS,
            method='PUT'  # kvdb.io דורש שימוש ב-PUT לצורך כתיבה/עדכון של מפתחות
        )
        with urllib.request.urlopen(req, timeout=5, context=ssl_context) as response:
            res_body = response.read().decode('utf-8')
            log_event("INFO", f"שמירה לענן kvdb.io הצליחה עבור {key}. תגובת השרת: {res_body}")
            return True
    except urllib.error.HTTPError as e:
        error_details = e.read().decode('utf-8') if e else ""
        log_event("ERROR", f"שגיאת HTTP {e.code} בשמירה לענן kvdb.io עבור {key}: {e.reason}. פירוט: {error_details}")
    except Exception as e:
        log_event("ERROR", f"שגיאה כללית בשמירה לענן kvdb.io עבור {key}: {str(e)}")
    
    return False

# --- רשימת מוצרים נפוצים ---
DEFAULT_PRODUCTS = [
    "בחר מהרשימה...",
    "חלב רגיל 3%", "חלב דל שומן 1%", "חלב שיבולת שועל אלפרו", "חלב סויה תנובה",
    "קוטג' 5%", "גבינה לבנה 5%", "גבינה צהובה עמק",
    "קולה זירו", "פחית קוקה קולה", "ספרייט זيرو", "מים מינרלים (שישייה)",
    "לחם מחיטה מלאה", "לחם לבן פרוס", "פיתות",
    "יוגורט פרו", "יוגורט מולר", "מעדן שוקולד",
    "נייר סופג", "נייר טואלט", "סבון כלים",
    "קפסולות קפה", "קפה שחור עלית", "נס קפה טסטרס צ'ויס",
    "במבה אסם", "ביסלי גריל", "שוקולד פרה"
]

# טעינת המידע החי מהענן בזמן אמת (או מהגיבוי המקומי)
PRODUCTS = get_from_cloud(CATALOG_KEY, DEFAULT_PRODUCTS)
shopping_list = get_from_cloud(SHOPPING_LIST_KEY, [])

# --- אזור הוספת מוצרים ---
st.write("מה חסר במקרר?")

selected_product = st.selectbox("חיפוש מוצר קיים:", PRODUCTS)
custom_product = st.text_input("לא מצאת ברשימה? הקלד כאן (המוצר יישמר לפעמים הבאות):")

if st.button("הוסף לרשימה ➕"):
    item_to_add = ""
    
    if custom_product:
        item_to_add = custom_product
        # עדכון קטלוג המוצרים בענן אם זה מוצר חדש
        if custom_product not in PRODUCTS:
            PRODUCTS.append(custom_product)
            if save_to_cloud(CATALOG_KEY, PRODUCTS):
                st.info("המוצר החדש נשמר בהצלחה בענן!")
            else:
                st.warning("המוצר נשמר באופן מקומי בלבד (אין חיבור לענן).")
    elif selected_product != "בחר מהרשימה...":
        item_to_add = selected_product
        
    if item_to_add:
        # הוספת המוצר לרשימת הקניות השמורה בענן
        if item_to_add not in shopping_list:
            shopping_list.append(item_to_add)
            if save_to_cloud(SHOPPING_LIST_KEY, shopping_list):
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
        # איפוס רשימת הקניות בענן ובגיבוי
        if save_to_cloud(SHOPPING_LIST_KEY, []):
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
    
    # כפתור בדיקת חיבור יזום
    if st.button("🔌 בדיקת חיבור מהירה לענן"):
        test_success = save_to_cloud("test_connection_key", {"status": "success", "time": str(datetime.datetime.now())})
        if test_success:
            st.success("החיבור לענן תקין לחלוטין! (100% Uptime) ⚡")
            log_event("SYSTEM", "בדיקת חיבור יזומה עברה בהצלחה.")
        else:
            st.error("החיבור לענן נכשל. המערכת פועלת כרגע במצב גיבוי מקומי יציב.")
            log_event("SYSTEM", "בדיקת חיבור יזומה נכשלה.")
            
    # הצגת קובץ הלוגים
    st.write("📋 לוגים של האפליקציה (app_logs.txt):")
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs_content = f.read()
        st.text_area("לוגים של השרת", logs_content, height=250, disabled=True)
        
        # כפתור ניקוי לוגים
        if st.button("🗑️ נקה לוגים"):
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.write("")
            st.success("קובץ הלוגים נוקה בהצלחה.")
            st.rerun()
    else:
        st.info("אין לוגים זמינים כרגע.")
