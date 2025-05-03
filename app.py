import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import numpy as np
from datetime import datetime
import plotly.express as px

# ---------------------- إعدادات التطبيق ----------------------
st.set_page_config(
    page_title="لوحة تحليل أداء الطلاب",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------- أنماط CSS ----------------------
st.markdown("""
<style>
.stMetric {text-align: center;}
.st-b7 {font-size: 16px !important;}
.reportview-container .main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}
@media screen and (max-width: 768px) {
    .stSelectbox, .stRadio, .stSlider {width: 100% !important;}
}
</style>
""", unsafe_allow_html=True)

# ---------------------- تحميل البيانات ----------------------
@st.cache_data(ttl=86400)  # تخزين لمدة 24 ساعة
def load_data():
    """تحميل البيانات من Google Drive"""
    try:
        # معلومات الملف
        FILE_ID = "1oEMEBkpqFQth_D4skuBY2lAHznSLeim6"
        
        # روابط تحميل بديلة
        DOWNLOAD_URLS = [
            f"https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=xlsx",
            f"https://drive.google.com/uc?id={FILE_ID}&export=download",
            f"https://www.googleapis.com/drive/v3/files/{FILE_ID}?alt=media"
        ]
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
        
        for url in DOWNLOAD_URLS:
            try:
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code == 200 and response.content.startswith(b'PK'):
                    excel_data = BytesIO(response.content)
                    
                    # قراءة ملف Excel مع تحديد الأعمدة المطلوبة
                    df = pd.read_excel(
                        excel_data,
                        engine='openpyxl',
                        header=0,
                        usecols="A:S"  # تحديد الأعمدة من A إلى S
                    )
                    
                    # تنظيف الأسماء
                    df.columns = df.columns.str.strip()
                    
                    # الأعمدة المتوقعة
                    REQUIRED_COLS = [
                        'الفصل الدراسي', 'اسم المدرسة', 'الجنس', 'الطالب', 'الصف',
                        'القرآن الكريم والدراسات الإسلامية', 'اللغة العربية',
                        'الدراسات الاجتماعية', 'الرياضيات', 'العلوم',
                        'اللغة الإنجليزية', 'المهارات الرقمية',
                        'التربية البدنية والدفاع عن النفس',
                        'المهارات الحياتية والأسرية', 'التربية الفنية',
                        'السلوك', 'المواظبة', 'المعدل', 'التقدير العام'
                    ]
                    
                    # التحقق من الأعمدة
                    missing_cols = [col for col in REQUIRED_COLS if col not in df.columns]
                    if missing_cols:
                        st.warning(f"الأعمدة الناقصة: {', '.join(missing_cols)}")
                        return pd.DataFrame()
                    
                    # تحويل الأعمدة الرقمية
                    NUMERIC_COLS = [col for col in REQUIRED_COLS if col not in 
                                  ['الفصل الدراسي', 'اسم المدرسة', 'الجنس', 'الطالب', 'الصف', 'التقدير العام']]
                    
                    for col in NUMERIC_COLS:
                        df[col] = pd.to_numeric(
                            df[col].astype(str)
                            .str.replace('%', '')
                            .str.replace(',', '.'),
                            errors='coerce'
                        )
                    
                    # تحديد المرحلة التعليمية
                    df['المرحلة'] = df['الصف'].apply(
                        lambda x: 'ابتدائي' if isinstance(x, str) and ('ابتدائي' in x or any(g in x for g in ['1', '2', '3', '4', '5', '6']))
                        else 'متوسط' if isinstance(x, str) and ('متوسط' in x or any(g in x for g in ['7', '8', '9']))
                        else 'غير محدد'
                    )
                    
                    # إضافة طابع زمني
                    df['آخر_تحديث'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    return df
                
            except Exception as e:
                continue
        
        st.error("فشل تحميل الملف من جميع المصادر")
        return pd.DataFrame()
    
    except Exception as e:
        st.error(f"خطأ غير متوقع: {str(e)}")
        return pd.DataFrame()

# ---------------------- وظائف التصور ----------------------
def create_bar_chart(data, x, y, title, color=None, text=None):
    fig = px.bar(
        data,
        x=x,
        y=y,
        color=color,
        title=title,
        text=text,
        template="plotly_white"
    )
    if text:
        fig.update_traces(texttemplate='%{text:.1f}', textposition='inside')
    fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
    return fig

def create_pie_chart(data, names, values, title):
    return px.pie(
        data,
        names=names,
        values=values,
        title=title,
        hole=0.3
    )

# ---------------------- الواجهة الرئيسية ----------------------
def main():
    st.title("📊 لوحة تحليل أداء الطلاب")
    
    # تحميل البيانات
    with st.spinner('جاري تحميل البيانات...'):
        data = load_data()
    
    if data.empty:
        st.error("لا يمكن عرض البيانات بسبب مشكلة في التحميل")
        return
    
    # ---------------------- الفلاتر ----------------------
    with st.sidebar:
        st.header("🔍 خيارات التصفية")
        
        # فلتر المرحلة
        stage = st.radio(
            "المرحلة التعليمية",
            options=data['المرحلة'].unique(),
            horizontal=True
        )
        
        # فلتر الفصل الدراسي
        semester = st.selectbox(
            "الفصل الدراسي",
            options=["الكل"] + sorted(data['الفصل الدراسي'].dropna().unique().tolist())
        )
        
        # فلتر المدرسة
        school = st.selectbox(
            "المدرسة",
            options=["الكل"] + sorted(data['اسم المدرسة'].dropna().unique().tolist())
        )
    
    # ---------------------- تصفية البيانات ----------------------
    filtered_data = data[data['المرحلة'] == stage]
    if semester != "الكل":
        filtered_data = filtered_data[filtered_data['الفصل الدراسي'] == semester]
    if school != "الكل":
        filtered_data = filtered_data[filtered_data['اسم المدرسة'] == school]
    
    # ---------------------- المؤشرات ----------------------
    st.subheader("📈 المؤشرات الرئيسية")
    cols = st.columns(4)
    with cols[0]:
        st.metric("عدد الطلاب", len(filtered_data))
    with cols[1]:
        avg = filtered_data['المعدل'].mean()
        st.metric("المتوسط العام", f"{avg:.2f}")
    with cols[2]:
        st.metric("آخر تحديث", filtered_data['آخر_تحديث'].iloc[0])
    with cols[3]:
        attendance = filtered_data['المواظبة'].mean()
        st.metric("متوسط المواظبة", f"{attendance:.1f}%")
    
    # ---------------------- التحليلات ----------------------
    st.subheader("📊 توزيع التقديرات")
    grade_dist = filtered_data['التقدير العام'].value_counts().reset_index()
    grade_dist.columns = ['التقدير', 'العدد']
    
    fig1 = create_pie_chart(grade_dist, 'التقدير', 'العدد', "توزيع التقديرات")
    st.plotly_chart(fig1, use_container_width=True)
    
    st.subheader("📚 أداء المواد الدراسية")
    subjects = [col for col in data.columns if any(x in col for x in ['القرآن', 'اللغة', 'الدراسات', 'الرياضيات', 'العلوم'])]
    subject_avg = filtered_data[subjects].mean().reset_index()
    subject_avg.columns = ['المادة', 'المتوسط']
    
    fig2 = create_bar_chart(subject_avg, 'المادة', 'المتوسط', "متوسط الدرجات حسب المادة", text='المتوسط')
    st.plotly_chart(fig2, use_container_width=True)

if __name__ == "__main__":
    main()