import streamlit as st
from pypdf import PdfReader, PdfWriter
from pypdf._page import PageObject
from io import BytesIO

# ---------------- 1. الدوال الحسابية (المنطق الخاص بك) ----------------

def next_multiple_of_4(n: int) -> int:
    return n + (-n % 4)

def booklet_spreads_english(total_pages: int):
    if total_pages % 4 != 0:
        raise ValueError("❌ عدد الصفحات يجب أن يكون من مضاعفات 4.")
    sheets = total_pages // 4
    spreads = []
    for i in range(sheets):
        spreads.append((total_pages - 2 * i, 1 + 2 * i))      # Front
        spreads.append((2 + 2 * i, total_pages - 1 - 2 * i))  # Back
    return spreads

def booklet_spreads_rtl(total_pages: int):
    eng = booklet_spreads_english(total_pages)
    return [(R, L) for (L, R) in eng]

# ---------------- 2. دالة المعالجة الرئيسية ----------------

def process_imposition(input_pdf_file, opening_mode, pages_mode, manual_val):
    reader = PdfReader(input_pdf_file)
    pdf_pages = len(reader.pages)
    
    # تحديد العدد المستهدف للصفحات
    if pages_mode == "AUTO":
        target_pages = next_multiple_of_4(pdf_pages)
    else:
        target_pages = int(manual_val)
        if target_pages < pdf_pages:
            raise ValueError(f"العدد اليدوي ({target_pages}) أصغر من صفحات الملف ({pdf_pages})")

    # إضافة صفحات فارغة إذا لزم الأمر
    pages_list = list(reader.pages)
    while len(pages_list) < target_pages:
        p0 = pages_list[0]
        blank = PageObject.create_blank_page(width=float(p0.mediabox.width), height=float(p0.mediabox.height))
        pages_list.append(blank)
    
    # حساب ترتيب السبريد
    if opening_mode == "RTL":
        spreads = booklet_spreads_rtl(target_pages)
    else:
        spreads = booklet_spreads_english(target_pages)
    
    writer = PdfWriter()
    # نأخذ مقاس أول صفحة كأساس
    w = float(pages_list[0].mediabox.width)
    h = float(pages_list[0].mediabox.height)

    # دمج الصفحات في سبريدات (2-up)
    for (L, R) in spreads:
        new_page = PageObject.create_blank_page(width=w * 2, height=h)
        new_page.merge_page(pages_list[L - 1])
        new_page.merge_translated_page(pages_list[R - 1], w, 0)
        writer.add_page(new_page)
    
    # تصدير الملف لذاكرة السيرفر
    output_stream = BytesIO()
    writer.write(output_stream)
    return output_stream.getvalue()

# ---------------- 3. واجهة المستخدم (Streamlit) ----------------

st.set_page_config(page_title="نظام الإمبوزيشن الذكي", layout="centered")

st.title("🖨️ نظام الإمبوزيشن أونلاين")
st.write("ارفع ملف PDF وسيقوم السيرفر بترتيبه لك ككتاب (Booklet) فوراً.")

# إعدادات المستخدم
with st.sidebar:
    st.header("⚙️ الإعدادات")
    opening = st.radio("اتجاه الكتاب (Opening):", ["RTL (عربي/يمين)", "LTR (إنجليزي/يسار)"])
    mode = st.radio("نظام الصفحات:", ["AUTO (تلقائي)", "MANUAL (يدوي)"])
    manual_n = 0
    if mode == "MANUAL (يدوي)":
        manual_n = st.number_input("أدخل عدد الصفحات (مضاعفات 4):", min_value=4, step=4, value=12)

# رفع الملف
uploaded_file = st.file_uploader("اختر ملف PDF الخاص بك", type="pdf")

if uploaded_file:
    if st.button("🚀 ابدأ المعالجة"):
        try:
            with st.spinner("جاري ترتيب الصفحات وتحويلها..."):
                # تشغيل المنطق
                op_mode = "RTL" if "RTL" in opening else "LTR"
                pg_mode = "AUTO" if "AUTO" in mode else "MANUAL"
                
                result_pdf = process_imposition(uploaded_file, op_mode, pg_mode, manual_n)
                
                st.success("✅ اكتملت المعالجة بنجاح!")
                st.download_button(
                    label="📥 تحميل الملف الجاهز للطباعة",
                    data=result_pdf,
                    file_name="Imposed_Booklet.pdf",
                    mime="application/pdf"
                )
        except Exception as e:
            st.error(f"حدث خطأ: {e}")

st.divider()
st.caption("برمجة خاصة للمطابع - معالجة سحابية آمنة")
