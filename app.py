import streamlit as st
from pypdf import PdfReader, PdfWriter
from pypdf._page import PageObject
from io import BytesIO

# --- انقل هنا كل الدوال الحسابية من كودك الأصلي ---
# (mm_to_pt, booklet_spreads_rtl, build_external_crop_commands, إلخ...)

def process_pdf(input_pdf, opening_mode, pages_mode, manual_n):
    reader = PdfReader(input_pdf)
    pdf_pages = len(reader.pages)
    
    # تحديد عدد الصفحات المستهدف
    if pages_mode == "AUTO":
        target = pdf_pages + (-pdf_pages % 4)
    else:
        target = int(manual_n)
    
    # توفير الصفحات الناقصة (Padding)
    while len(reader.pages) < target:
        p0 = reader.pages[0]
        reader.pages.append(PageObject.create_blank_page(width=float(p0.mediabox.width), height=float(p0.mediabox.height)))
    
    # حساب السبريدات (نفس منطق كودك)
    spreads = booklet_spreads_rtl(target) if opening_mode == "RTL" else booklet_spreads_english(target)
    
    writer = PdfWriter()
    w = float(reader.pages[0].mediabox.width)
    h = float(reader.pages[0].mediabox.height)
    
    for (L, R) in spreads:
        # هنا تضع منطق دمج الصفحات وعلامات القص من كودك
        # سأختصرها هنا للتوضيح فقط:
        new_page = PageObject.create_blank_page(width=w*2, height=h)
        new_page.merge_page(reader.pages[L-1])
        new_page.merge_translated_page(reader.pages[R-1], w, 0)
        writer.add_page(new_page)
    
    # حفظ النتيجة في ذاكرة السيرفر لإرسالها للعميل
    output_stream = BytesIO()
    writer.write(output_stream)
    return output_stream.getvalue()

# --- واجهة الويب (Streamlit) ---
st.set_page_config(page_title="Imposition Online", layout="centered")
st.title("نظام الإمبوزيشن للمطابع 🖨️")

uploaded_file = st.file_uploader("ارفع ملف الـ PDF المراد توزيعه", type="pdf")

col1, col2 = st.columns(2)
with col1:
    opening = st.radio("اتجاه الكتاب (Opening)", ["RTL (عربي)", "LTR (إنجليزي)"])
with col2:
    mode = st.radio("عدد الصفحات", ["AUTO (تلقائي)", "MANUAL (يدوي)"])

if st.button("بدء عملية المعالجة"):
    if uploaded_file:
        with st.spinner("جاري ترتيب الصفحات..."):
            result = process_pdf(uploaded_file, opening[:3], mode[:4], 12)
            st.success("تم تجهيز الملف!")
            st.download_button("تحميل ملف الإمبوزيشن جاهز للطباعة", data=result, file_name="imposed_output.pdf")
    else:
        st.error("الرجاء رفع ملف أولاً")