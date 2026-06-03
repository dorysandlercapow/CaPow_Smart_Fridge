import streamlit as st
import os

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

# --- לוגו וכותרת ממותגת ---
# מנגנון שמחפש קובץ תמונה בתיקייה ומציג אותו אם הוא קיים
if os.path.exists("logo.png"):
    st.image("logo.png", width=180)
elif os.path.exists("logo.jpg"):
    st.image("logo.jpg", width=180)

st.markdown('<h1 style="text-align: right;">המקרר החכם של <span class="capow-title">CaPow</span> ⚡</h1>', unsafe_allow_html=True)
# תיקון הסלוגן באנגלית כך שישמור על כיווניות משמאל לימין אבל יוצמד לימין האתר
st.markdown('<div style="text-align: right;"><p dir="ltr" style="direction: ltr; display: inline-block; font-size: 1.1rem; color: #6b7280; margin-top: -15px; margin-bottom: 30px;">100% Uptime for our team\'s energy!</p></div>', unsafe_allow_html=True)

FILE_NAME = "shopping_list.txt"
CATALOG_FILE = "products_catalog.txt" 

# --- רשימת מוצרים נפוצים (ברירת מחדל) ---
DEFAULT_PRODUCTS = [
    "בחר מהרשימה...",
    "חלב רגיל 3%", "חלב דל שומן 1%", "חלב שיבולת שועל אלפרו", "חלב סויה תנובה",
    "קוטג' 5%", "גבינה לבנה 5%", "גבינה צהובה עמק",
    "קולה זירו", "פחית קוקה קולה", "ספרייט זירו", "מים מינרלים (שישייה)",
    "לחם מחיטה מלאה", "לחם לבן פרוס", "פיתות",
    "יוגורט פרו", "יוגורט מולר", "מעדן שוקולד",
    "נייר סופג", "נייר טואלט", "סבון כלים",
    "קפסולות קפה", "קפה שחור עלית", "נס קפה טסטרס צ'ויס",
    "במבה אסם", "ביסלי גריל", "שוקולד פרה"
]

# פונקציה לטעינת הקטלוג
def load_products():
    if not os.path.exists(CATALOG_FILE):
        with open(CATALOG_FILE, "w", encoding="utf-8") as file:
            for product in DEFAULT_PRODUCTS:
                file.write(product + "\n")
        return DEFAULT_PRODUCTS.copy()
    else:
        with open(CATALOG_FILE, "r", encoding="utf-8") as file:
            return [line.strip() for line in file.readlines() if line.strip()]

PRODUCTS = load_products()

# --- אזור הוספת מוצרים ---
st.write("מה חסר במקרר?")

selected_product = st.selectbox("חיפוש מוצר קיים:", PRODUCTS)
custom_product = st.text_input("לא מצאת ברשימה? הקלד כאן (המוצר יישמר לפעמים הבאות):")

if st.button("הוסף לרשימה ➕"):
    item_to_add = ""
    
    if custom_product:
        item_to_add = custom_product
        if custom_product not in PRODUCTS:
            with open(CATALOG_FILE, "a", encoding="utf-8") as file:
                file.write(custom_product + "\n")
    elif selected_product != "בחר מהרשימה...":
        item_to_add = selected_product
        
    if item_to_add:
        with open(FILE_NAME, "a", encoding="utf-8") as file:
            file.write(item_to_add + "\n")
        st.success(f"מעולה! '{item_to_add}' התווסף למאגר האנרגיה שלנו.")
    else:
        st.warning("אנא בחר מוצר או הקלד אחד חדש.")

st.divider()

# --- אזור רשימת הקניות (לקניין) ---
st.subheader("רשימת הקניות הנוכחית 🛒")

if os.path.exists(FILE_NAME):
    with open(FILE_NAME, "r", encoding="utf-8") as file:
        items = file.readlines()

    if items:
        for item in items:
            st.write(f"⚡ {item.strip()}")
        
        st.write("")
        if st.button("טעינה הושלמה! (מחיקת הרשימה) 🗑️"):
            os.remove(FILE_NAME)
            st.rerun()
    else:
         st.info("אין חוסרים. הרובוטים יכולים להמשיך לנוע! 🤖")
else:
    st.info("אין חוסרים. הרובוטים יכולים להמשיך לנוע! 🤖")
