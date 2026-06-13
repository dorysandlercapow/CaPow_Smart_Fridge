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

    /* עיצוב קוביות המוצרים - גריד מודרני */
    .product-card {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 16px;
        text-align: center !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        transition: all 0.2s ease-in-out;
    }
    .product-card:hover {
        box-shadow: 0 4px 12px rgba(67, 100, 247, 0.08);
        border-color: #4364F7;
    }
</style>
""", unsafe_allow_html=True)

# אתחול משתנה state כדי למנוע שגיאות מפתח בהרצה ראשונה
if "user_note" not in st.session_state:
    st.session_state["user_note"] = ""

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
JSONBIN_API_KEY = st.secrets.get("JSONBIN_API_KEY")
JSONBIN_BIN_ID = st.secrets.get("JSONBIN_BIN_ID")
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD")
BUYER_PASSWORD = st.secrets.get("BUYER_PASSWORD")

# יצירת הקשר SSL לא מאומת
try:
    ssl_context = ssl._create_unverified_context()
except Exception:
    ssl_context = None

# בדיקה ידידותית למשתמש למקרה שהמפתחות טרם הוגדרו בלוח הבקרה
if not JSONBIN_API_KEY or not JSONBIN_BIN_ID or not ADMIN_PASSWORD or not BUYER_PASSWORD:
    st.info("👋 ברוכים הבאים למקרר החכם של CaPow!")
    st.markdown("""
    ### 🔐 שלב אחרון להפעלת הענן בצורה מאובטחת (Secrets):
    יש להגדיר את המפתחות והסיסמאות שלכם ב-Secrets של Streamlit.
    העתיקו והדביקו את השורות הבאות (עם הערכים שלכם):
    
    \`\`\`toml
    JSONBIN_API_KEY = "ה-Master Key שלכם"
    JSONBIN_BIN_ID = "ה-Bin ID שלכם"
    ADMIN_PASSWORD = "סיסמה_לניהול_הקטלוג"
    BUYER_PASSWORD = "סיסמה_למחיקת_העגלה"
    \`\`\`
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
            return res_data.get("record", {})
    except Exception as e:
        log_event("ERROR", f"שגיאה בטעינה מהענן: {str(e)}")
        if os.path.exists("local_backup.json"):
            try:
                with open("local_backup.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

def save_all_data(data):
    try:
        with open("local_backup.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass

    url = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}"
    headers = {
        "X-Master-Key": JSONBIN_API_KEY,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    try:
        payload = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=payload, headers=headers, method="PUT")
        with urllib.request.urlopen(req, timeout=5, context=ssl_context) as response:
            return True
    except Exception as e:
        log_event("ERROR", f"עדכון הענן נכשל: {str(e)}")
        return False

# טעינת המידע החי מהענן
db_data = load_all_data()
shopping_list = db_data.get("shopping_list", [])

# אם אין קטגוריות בענן, נאתחל מבנה ריק (ללא רשימות קשיחות בקוד!)
if "categories" not in db_data:
    db_data["categories"] = {}
    save_all_data(db_data)

CATEGORIES = db_data["categories"]

# פונקציית הוספה מהירה עם תמיכה בחובת הערה ל"אחר"
def add_product_to_list(name, emoji):
    note = st.session_state.get("user_note", "").strip()
    
    # וידוא חובה: אי אפשר לבחור "אחר" בלי לפרט בהערה!
    if name == "אחר" and not note:
        st.toast("⚠️ חובה להקליד למטה מה חסר לכם לפני שמוסיפים 'אחר'!", icon="⚠️")
        return
        
    final_item = f"{emoji} {name}" if name != "אחר" else f"{emoji} מוצר אחר"
    if note:
        final_item += f" ({note})"
        
    # בדיקת כפילויות התומכת גם בפריטים ישנים (מחרוזות) וגם בחדשים (מילונים עם תאריך)
    exists = False
    for item in shopping_list:
        item_name = item["item"] if isinstance(item, dict) else item
        if item_name == final_item:
            exists = True
            break
            
    if not exists:
        # יצירת חותמת זמן של התאריך הנוכחי
        current_date = datetime.datetime.now().strftime("%d/%m/%Y")
        shopping_list.append({"item": final_item, "date": current_date})
        
        db_data["shopping_list"] = shopping_list
        if save_all_data(db_data):
            st.toast(f"התווסף בהצלחה: {final_item} ⚡", icon="✅")
            st.session_state["user_note"] = ""
            st.rerun()
        else:
            st.error("תקלה בשמירה לענן.")
    else:
        st.warning(f"'{final_item}' כבר קיים ברשימה!")

# --- 1. אזור בחירת מוצרים ---
st.markdown("### 1. לחצו על המוצר שחסר במקרר: 👇")

if not CATEGORIES:
    st.info("הקטלוג כרגע ריק! 🛠️ מנהל המערכת, היכנסו לפאנל הניהול למטה כדי לבנות את קטגוריות המוצרים שלכם.")
else:
    # יצירת לשוניות חלוקה מבוססות קטגוריות דינמיות מהענן
    tabs = st.tabs(list(CATEGORIES.keys()))
    
    for tab, (cat_name, items) in zip(tabs, CATEGORIES.items()):
        with tab:
            cols = st.columns(3)
            for idx, item in enumerate(items):
                col = cols[idx % 3]
                with col:
                    with st.container(border=True):
                        st.markdown(f"<div style='text-align: center; font-size: 1.15rem; font-weight: bold;'>{item['emoji']} {item['name']}</div>", unsafe_allow_html=True)
                        st.write("")
                        st.button(
                            "הוסף ➕", 
                            key=f"btn_{cat_name}_{idx}_{item['name']}", 
                            on_click=add_product_to_list, 
                            args=(item['name'], item['emoji']),
                            use_container_width=True
                        )

st.write("")
st.divider()

# --- 2. אזור הזנת הערה ---
st.markdown("### 2. רוצים להוסיף הערה מיוחדת? ✍️")
st.text_input(
    "הקלידו כאן הערה או פירוט למוצר 'אחר' ואז לחצו על ה-➕ למעלה:",
    key="user_note",
    placeholder="למשל: 'רק חלב שיבולת שועל', או '3 חבילות קבנוס'..."
)

st.divider()

# --- אזור רשימת הקניות הנוכחית ---
st.subheader("רשימת הקניות הנוכחית 🛒")

if shopping_list:
    # יצירת רשימה אחידה (תמיכה לאחור במוצרים ישנים שנשמרו בלי תאריך)
    display_list = []
    for i in shopping_list:
        if isinstance(i, str):
            display_list.append({"item": i, "date": "לפני העדכון"})
        else:
            display_list.append(i)

    # שימוש ב-form כדי לאפשר סימון של כמה מוצרים בלי לרענן את המסך בכל לחיצה
    with st.form("buyer_cart_form"):
        st.markdown("**סמנו ב-V את המוצרים שקניתם/אספתם:** (מה שלא יסומן יישאר בעגלה)")
        
        checked_items = []
        for idx, prod in enumerate(display_list):
            # יצירת תיבת סימון (צ'קבוקס) לכל מוצר עם התאריך שבו התבקש
            is_checked = st.checkbox(f"{prod['item']} 📅 [נוסף ב: {prod['date']}]", key=f"chk_prod_{idx}")
            checked_items.append(is_checked)
        
        st.write("")
        buyer_password_input = st.text_input("עדכון הרשימה דורש סיסמת קניין:", type="password", key="buyer_pwd_input")
        
        submit_update = st.form_submit_button("עדכן עגלה (מחק את מה שסומן ב-V) 🗑️")
        
        if submit_update:
            if buyer_password_input == BUYER_PASSWORD:
                # משאירים ברשימה רק את המוצרים ש*לא* סומנו ב-V
                new_shopping_list = [prod for i, prod in enumerate(display_list) if not checked_items[i]]
                
                db_data["shopping_list"] = new_shopping_list
                if save_all_data(db_data):
                    st.toast("הרשימה עודכנה בהצלחה! 🧹", icon="🗑️")
                    st.rerun()
                else:
                    st.success("הרשימה עודכנה מקומית.")
            elif buyer_password_input == "":
                st.warning("נא להזין סיסמה כדי לעדכן את הרשימה.")
            else:
                st.error("סיסמה שגויה! הרשימה לא התעדכנה.")
else:
    st.info("אין חוסרים. הרובוטים יכולים להמשיך לנוע! 🤖")

st.divider()

# --- ממשק מנהל: עריכת קטלוג וקטגוריות דינמיות ---
with st.expander("⚙️ ממשק מנהל (ניהול ועריכת הקטלוג)"):
    st.markdown("### הוספה והסרה של מוצרים וקטגוריות")
    st.info("💡 הזינו את סיסמת המנהל שהגדרתם ב-Secrets.")
    admin_pwd = st.text_input("סיסמת מנהל:", type="password", key="admin_password_input")
    
    if admin_pwd == ADMIN_PASSWORD:
        st.success("גישת מנהל אושרה! בחר פעולה:")
        tab_add_cat, tab_edit_prod = st.tabs(["📁 ניהול קטגוריות", "📦 ניהול מוצרים בקטגוריה"])
        
        # 1. ניהול קטגוריות
        with tab_add_cat:
            new_cat_name = st.text_input("שם קטגוריה חדשה (כולל אמוג'י, למשל '🧼 מוצרי ניקיון'):", key="new_cat_input")
            if st.button("➕ הוסף קטגוריה"):
                if new_cat_name and new_cat_name not in db_data["categories"]:
                    db_data["categories"][new_cat_name] = [{"name": "אחר", "emoji": "❓"}]
                    if save_all_data(db_data):
                        st.toast("קטגוריה נוספה!", icon="✅")
                        st.rerun()
            
            st.markdown("---")
            if db_data["categories"]:
                cat_to_del = st.selectbox("בחר קטגוריה למחיקה:", list(db_data["categories"].keys()), key="cat_del_sel")
                if st.button("🗑️ מחק קטגוריה שלמה"):
                    del db_data["categories"][cat_to_del]
                    if save_all_data(db_data):
                        st.toast("קטגוריה נמחקה!", icon="🗑️")
                        st.rerun()
            else:
                st.info("אין קטגוריות למחיקה.")
                    
        # 2. ניהול מוצרים
        with tab_edit_prod:
            if db_data["categories"]:
                cat_to_edit = st.selectbox("בחר קטגוריה כדי לערוך את המוצרים שבה:", list(db_data["categories"].keys()), key="cat_edit_sel")
                if cat_to_edit:
                    st.markdown("**➕ הוספת מוצר חדש:**")
                    c_name, c_emj, c_btn = st.columns([3, 1, 1])
                    new_p_name = c_name.text_input("שם המוצר:", key=f"p_name_{cat_to_edit}")
                    new_p_emoji = c_emj.text_input("אמוג'י:", key=f"p_emj_{cat_to_edit}")
                    
                    if c_btn.button("הוסף מוצר"):
                        if new_p_name:
                            # הוספת המוצר לפני ה"אחר" שתמיד יהיה בסוף אם אפשר
                            new_item = {"name": new_p_name, "emoji": new_p_emoji or "📦"}
                            db_data["categories"][cat_to_edit].insert(-1, new_item) # מכניס לפני האחרון
                            if save_all_data(db_data):
                                st.toast("מוצר חדש נוסף לקטגוריה!", icon="✅")
                                st.rerun()
                    
                    st.markdown("---")
                    st.markdown("**🗑️ מוצרים קיימים (לחץ על הפח למחיקה):**")
                    for p_idx, p in enumerate(db_data["categories"][cat_to_edit]):
                        col1, col2 = st.columns([4, 1])
                        col1.markdown(f"{p['emoji']} {p['name']}")
                        if p['name'] != "אחר": # לא מרשים למחוק את פריט החובה 'אחר'
                            if col2.button("🗑️", key=f"del_{cat_to_edit}_{p_idx}_{p['name']}"):
                                db_data["categories"][cat_to_edit].remove(p)
                                save_all_data(db_data)
                                st.rerun()
                        else:
                            col2.markdown("🔒 **קבוע**")
            else:
                st.info("נא להוסיף קטגוריה ראשונה תחת 'ניהול קטגוריות' לפני הוספת מוצרים.")
    elif admin_pwd != "":
        st.error("סיסמה שגויה.")

# --- אבחון ולוגים (מנהל מערכת ראשי) ---
with st.expander("🩺 אבחון שרת ולוגים (למפתחים)"):
    if st.button("🔌 בדיקת חיבור מהירה לענן"):
        if save_all_data(db_data):
            st.success("החיבור לענן תקין לחלוטין! (100% Uptime) ⚡")
        else:
            st.error("החיבור לענן נכשל.")
            
    st.write("📋 לוגים של האפליקציה:")
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            st.text_area("לוגים", f.read(), height=150, disabled=True)
