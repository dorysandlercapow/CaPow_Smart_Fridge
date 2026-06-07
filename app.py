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

    /* העלמת הסרגל העליון של Streamlit לחלוטין (Share, Edit, GitHub, Star) */
    [data-testid="stHeader"] {
        display: none !important;
    }
    
    /* העלמת הפוטר המובנה של Streamlit בתחתית הדף */
    footer {
        visibility: hidden !important;
    }

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

    /* עיצוב קוביות מוצר (Cards) */
    .product-card {
        background: white;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        text-align: center !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: all 0.2s ease-in-out;
        margin-bottom: 15px;
    }
    
    .product-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 15px -3px rgba(67, 100, 247, 0.1);
        border-color: #4364F7;
    }

    .product-icon {
        font-size: 2rem;
        margin-bottom: 8px;
        display: block;
        text-align: center !important;
    }

    .product-name {
        font-weight: 700;
        font-size: 1rem;
        color: #1f2937;
        margin-bottom: 12px;
        display: block;
        text-align: center !important;
    }

    /* עיצוב כפתורים קומפקטיים בתוך קוביות מוצרים */
    div.product-card-btn > div > button {
        background: #f3f4f6 !important;
        color: #1f2937 !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 6px !important;
        padding: 4px 12px !important;
        font-size: 0.85rem !important;
        font-weight: bold !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
    }

    div.product-card-btn > div > button:hover {
        background: linear-gradient(90deg, #4364F7, #6FB1FC) !important;
        color: white !important;
        border-color: transparent !important;
        box-shadow: 0 4px 10px rgba(67, 100, 247, 0.2) !important;
    }

    /* עיצוב כפתור מחיקה וניהול ראשי */
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
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 15px rgba(67, 100, 247, 0.3) !important;
        color: white !important;
    }
    
    /* עיצוב משודרג ללשוניות (Tabs) */
    div[data-testid="stTabBar"] {
        gap: 10px;
    }
    
    button[data-baseweb="tab"] {
        border-radius: 8px !important;
        padding: 8px 16px !important;
        background-color: #f3f4f6 !important;
        font-weight: bold !important;
        color: #4b5563 !important;
    }
    
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #4364F7 !important;
        color: white !important;
    }

    /* עיצוב התראות */
    div[data-testid="stAlert"] {
        direction: rtl;
        border-radius: 10px !important;
        border-right: 5px solid #4364F7 !important;
        border-left: none !important;
    }
    
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
st.markdown('<div style="text-align: right;"><p dir="ltr" style="direction: ltr; display: inline-block; font-size: 1.1rem; color: #6b7280; margin-top: -15px; margin-bottom: 20px;">100% Uptime for our team\'s energy!</p></div>', unsafe_allow_html=True)

# --- הגדרות חיבור מאובטח לענן (Streamlit Secrets) ---
JSONBIN_API_KEY = st.secrets.get("JSONBIN_API_KEY")
JSONBIN_BIN_ID = st.secrets.get("JSONBIN_BIN_ID")

try:
    ssl_context = ssl._create_unverified_context()
except Exception:
    ssl_context = None

# בדיקה ידידותית למשתמש למקרה שהמפתחות טרם הוגדרו בלוח הבקרה
if not JSONBIN_API_KEY or not JSONBIN_BIN_ID:
    st.info("👋 ברוכים הבאים למקרר החכם של CaPow!")
    st.markdown("""
    ### 🔐 שלב אחרון להפעלת הענן בצורה מאובטחת (Secrets):
    מכיוון שקוד ה-GitHub שלכם ציבורי, **אסור** לרשום את המפתחות ישירות בקוד! הגדירו אותם ב-Secrets של Streamlit:
    
    ```toml
    JSONBIN_API_KEY = "ה-Master Key שלכם"
    JSONBIN_BIN_ID = "ה-Bin ID שלכם"
    ```
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
                
        return {"shopping_list": []}

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
shopping_list = db_data.get("shopping_list", [])

# --- קטלוג מובנה ומסווג (נוקשה וממותג ללא הקלדות חופשיות) ---
CATEGORIZED_CATALOG = {
    "🥛 מוצרי חלב": [
        {"name": "חלב רגיל 3%", "icon": "🥛"},
        {"name": "חלב שיבולת שועל אלפרו", "icon": "🌾"},
        {"name": "חלב סויה תנובה", "icon": "🫘"},
        {"name": "קוטג' 5%", "icon": "🧀"},
        {"name": "גבינה לבנה 5%", "icon": "🥣"},
        {"name": "גבינה צהובה עמק", "icon": "🧀"},
        {"name": "יוגורט פרו תנובה", "icon": "🥣"},
        {"name": "חמאה", "icon": "🧈"}
    ],
    "🥤 שתייה קלה": [
        {"name": "קולה זירו פחיות", "icon": "🥤"},
        {"name": "קולה זירו בקבוק", "icon": "🍾"},
        {"name": "מים מינרלים שישייה", "icon": "💧"},
        {"name": "פחית קוקה קולה", "icon": "🥤"},
        {"name": "ספרייט זيرو פחית", "icon": "🍋"},
        {"name": "סודה מארז", "icon": "🫧"},
        {"name": "בירה שחורה", "icon": "🍺"}
    ],
    "🍞 מאפייה ולחם": [
        {"name": "לחם כוסמין פרוס", "icon": "🍞"},
        {"name": "לחם לבן פרוס", "icon": "🍞"},
        {"name": "פיתות מארז", "icon": "🫓"},
        {"name": "פריכיות אורז", "icon": "🌾"},
        {"name": "לחמניות", "icon": "🥖"}
    ],
    "🥨 נשנושים וקפה": [
        {"name": "קפסולות קפה", "icon": "☕"},
        {"name": "במבה אסם", "icon": "🥜"},
        {"name": "ביסלי גריל", "icon": "🥨"},
        {"name": "חטיפי אנרגיה", "icon": "🍫"},
        {"name": "תה ירוק ויסוצקי", "icon": "🍵"},
        {"name": "שוקולד פרה מריר", "icon": "🍫"},
        {"name": "שוקולד פרה חלב", "icon": "🍫"},
        {"name": "קפה טסטרס צ'ויס", "icon": "🫙"}
    ],
    "🍎 פירות וירקות": [
        {"name": "עגבניות", "icon": "🍅"},
        {"name": "מלפפונים", "icon": "🥒"},
        {"name": "לימונים", "icon": "🍋"},
        {"name": "בננות", "icon": "🍌"},
        {"name": "תפוחים ירוקים", "icon": "🍏"},
        {"name": "אבוקדו", "icon": "🥑"}
    ],
    "🧹 ניקיון ושונות": [
        {"name": "נייר סופג מארז", "icon": "🧻"},
        {"name": "סבון כלים פלמוליב", "icon": "🧴"},
        {"name": "טבליות למדיח", "icon": "🧼"},
        {"name": "נייר טואלט מארז", "icon": "🧻"},
        {"name": "כוסות נייר לקפה", "icon": "☕"}
    ]
}

# --- אזור הוספת מוצרים (גריד קוביות מותאם למובייל) ---
st.markdown("### מה נגמר במקרר? לחצו להוספה מהירה: ⚡")

# יצירת לשוניות (Tabs) עבור כל קטגוריה
tab_names = list(CATEGORIZED_CATALOG.keys())
tabs = st.tabs(tab_names)

for index, tab_name in enumerate(tab_names):
    with tabs[index]:
        products_in_cat = CATEGORIZED_CATALOG[tab_name]
        
        # יצירת גריד של קוביות (3 עמודות בכל שורה)
        col_count = 3
        cols = st.columns(col_count)
        
        for i, product in enumerate(products_in_cat):
            col_index = i % col_count
            with cols[col_index]:
                # הצגת קוביית מוצר בעיצוב HTML מותאם אישית
                st.markdown(f"""
                <div class="product-card">
                    <span class="product-icon">{product['icon']}</span>
                    <span class="product-name">{product['name']}</span>
                </div>
                """, unsafe_allow_html=True)
                
                # כפתור הוספה ייחודי לכל קובייה
                st.markdown('<div class="product-card-btn">', unsafe_allow_html=True)
                if st.button(f"הוסף ➕", key=f"btn_{product['name']}"):
                    item_name = f"{product['icon']} {product['name']}"
                    
                    if item_name not in shopping_list:
                        shopping_list.append(item_name)
                        db_data["shopping_list"] = shopping_list
                        save_all_data(db_data)
                        st.toast(f"✅ '{product['name']}' התווסף בהצלחה!", icon="⚡")
                        st.rerun()
                    else:
                        st.toast(f"⚠️ '{product['name']}' כבר ברשימה!", icon="💡")
                st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# --- אזור רשימת הקניות (לקניין) ---
st.subheader("רשימת הקניות הנוכחית 🛒")

if shopping_list:
    for item in shopping_list:
        st.write(f"{item}")
    
    st.write("")
    
    # הוספת שדה הזנת סיסמה מאובטח למניעת מחיקות בטעות
    buyer_password = st.text_input("מחיקת הרשימה דורשת סיסמת קניין:", type="password", key="buyer_pwd_input")
    
    if st.button("טעינה הושלמה! (מחיקת הרשימה) 🗑️"):
        if buyer_password == "1234":
            db_data["shopping_list"] = []
            if save_all_data(db_data):
                st.toast("הרשימה אופסה בהצלחה בענן! 🧹")
            else:
                st.toast("הרשימה אופסה מקומית (מצב אופליין).")
            st.rerun()
        elif buyer_password == "":
            st.warning("נא להזין סיסמה כדי למחוק את הרשימה.")
        else:
            st.error("סיסמה שגויה! הרשימה לא נמחקה.")
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
