import streamlit as st
import urllib.request
import json

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

# --- כותרת ממותגת נקייה ---
st.markdown('<h1 style="text-align: right; margin-top: 20px;">המקרר החכם של <span class="capow-title">CaPow</span> ⚡</h1>', unsafe_allow_html=True)
st.markdown('<div style="text-align: right;"><p dir="ltr" style="direction: ltr; display: inline-block; font-size: 1.1rem; color: #6b7280; margin-top: -15px; margin-bottom: 30px;">100% Uptime for our team\'s energy!</p></div>', unsafe_allow_html=True)

# --- הגדרות מסד הנתונים בענן (KVDB) ---
DB_BUCKET_ID = "capow_fridge_secure_bucket_2026_9f8e7d"
SHOPPING_LIST_KEY = "shopping_list"
CATALOG_KEY = "products_catalog"

# פונקציות עזר לקריאה וכתיבה מהענן באמצעות ספריות פייתון מובנות בלבד
def get_from_cloud(key, default_value):
    url = f"https://kvdb.io/{DB_BUCKET_ID}/{key}"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception:
        # אם המפתח עדיין לא קיים בענן, נחזיר את ערך ברירת המחדל
        return default_value

def save_to_cloud(key, data):
    url = f"https://kvdb.io/{DB_BUCKET_ID}/{key}"
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='PUT'  # שינוי מ-POST ל-PUT כדי לתמוך ב-API של KVDB
        )
        with urllib.request.urlopen(req) as response:
            return response.read()
    except Exception as e:
        st.error(f"שגיאה בשמירה לענן: {e}")

# --- רשימת מוצרים נפוצים (ברירת מחדל אם הענן ריק) ---
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

# טעינת המידע החי מהענן בזמן אמת!
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
            save_to_cloud(CATALOG_KEY, PRODUCTS)
    elif selected_product != "בחר מהרשימה...":
        item_to_add = selected_product
        
    if item_to_add:
        # הוספת המוצר לרשימת הקניות השמורה בענן
        if item_to_add not in shopping_list:
            shopping_list.append(item_to_add)
            save_to_cloud(SHOPPING_LIST_KEY, shopping_list)
            st.success(f"מעולה! '{item_to_add}' התווסף למאגר האנרגיה שלנו.")
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
        # איפוס רשימת הקניות בענן
        save_to_cloud(SHOPPING_LIST_KEY, [])
        st.success("הרשימה אופסה בהצלחה!")
        st.rerun()
else:
    st.info("אין חוסרים. הרובוטים יכולים להמשיך לנוע! 🤖")
