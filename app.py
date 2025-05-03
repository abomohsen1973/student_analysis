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
@st.cache_data(ttl=86400)
def load_data():
    """تحميل البيانات من Google Sheets"""
    try:
        # تحويل الرابط إلى صيغة التحميل المباشر
        SHEET_ID = "1oEMEBkpqFQth_D4skuBY2lAHznSLeim6"
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # التحقق من أن الملف صالح
        if not response.content.startswith(b'PK'):
            st.error("الملف ليس بصيغة Excel صالحة")
            return pd.DataFrame()
            
        excel_data = BytesIO(response.content)
        df = pd.read_excel(excel_data, engine='openpyxl')
        
        # الأعمدة المتوقعة (يجب تعديلها حسب ملفك)
        REQUIRED_COLUMNS = [
            'الفصل الدراسي', 'اسم المدرسة', 'الجنس', 'اسم الطالب', 'الصف',
            'القرآن الكريم', 'اللغة العربية', 'الرياضيات', 'العلوم',
            'اللغة الإنجليزية', 'المعدل', 'التقدير العام'
        ]
        
        # التحقق من الأعمدة
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            st.error(f"الأعمدة الناقصة: {', '.join(missing_cols)}")
            return pd.DataFrame()
        
        # تحويل الأعمدة الرقمية
        numeric_cols = ['القرآن الكريم', 'اللغة العربية', 'الرياضيات', 'العلوم', 'اللغة الإنجليزية', 'المعدل']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col].astype(str)
                    .str.replace('%', '')
                    .str.replace(',', ''),
                    errors='coerce'
                )
        
        # تحديد المرحلة التعليمية
        df['المرحلة'] = np.where(
            df['الصف'].str.contains('ابتدائي|1|2|3|4|5|6'),
            'ابتدائي',
            np.where(
                df['الصف'].str.contains('متوسط|7|8|9'),
                'متوسط',
                'غير محدد'
            )
        )
        
        # إضافة تاريخ التحديث
        df['آخر تحديث'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return df
    
    except requests.exceptions.RequestException as e:
        st.error(f"خطأ في الاتصال: {str(e)}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"خطأ غير متوقع: {str(e)}")
        return pd.DataFrame()

# ---------------------- وظائف التصور ----------------------
def plot_grades_distribution(data):
    fig = px.pie(
        data,
        names='التقدير العام',
        title='توزيع التقديرات'
    )
    st.plotly_chart(fig, use_container_width=True)

def plot_subject_scores(data):
    subjects = ['القرآن الكريم', 'اللغة العربية', 'الرياضيات', 'العلوم', 'اللغة الإنجليزية']
    avg_scores = data[subjects].mean().reset_index()
    avg_scores.columns = ['المادة', 'المتوسط']
    
    fig = px.bar(
        avg_scores,
        x='المادة',
        y='المتوسط',
        text='المتوسط',
        title='متوسط الدرجات حسب المادة'
    )
    fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

# ---------------------- الواجهة الرئيسية ----------------------
def main():
    st.title("📊 لوحة تحليل أداء الطلاب")
    
    # زر التحديث
    if st.button("🔄 تحديث البيانات"):
        st.cache_data.clear()
        st.rerun()
    
    # تحميل البيانات
    with st.spinner('جاري تحميل البيانات...'):
        data = load_data()
    
    if data.empty:
        st.error("""
        تعذر تحميل البيانات. يرجى:
        1. التأكد من أن الملف متاح للعامة
        2. التحقق من اتصال الإنترنت
        3. تجربة الرابط في متصفح آخر
        """)
        return
    
    st.success("تم تحميل البيانات بنجاح!")
    
    # ---------------------- الفلاتر ----------------------
    st.sidebar.header("خيارات التصفية")
    
    selected_stage = st.sidebar.selectbox(
        "المرحلة التعليمية",
        options=['الكل'] + sorted(data['المرحلة'].unique().tolist())
    )
    
    selected_semester = st.sidebar.selectbox(
        "الفصل الدراسي",
        options=['الكل'] + sorted(data['الفصل الدراسي'].unique().tolist())
    )
    
    # تطبيق الفلاتر
    filtered_data = data.copy()
    if selected_stage != 'الكل':
        filtered_data = filtered_data[filtered_data['المرحلة'] == selected_stage]
    if selected_semester != 'الكل':
        filtered_data = filtered_data[filtered_data['الفصل الدراسي'] == selected_semester]
    
    # ---------------------- المؤشرات ----------------------
    st.subheader("المؤشرات الرئيسية")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("عدد الطلاب", len(filtered_data))
    with col2:
        avg_score = filtered_data['المعدل'].mean()
        st.metric("المتوسط العام", f"{avg_score:.2f}")
    with col3:
        last_update = filtered_data['آخر تحديث'].iloc[0]
        st.metric("آخر تحديث", last_update)
    
    # ---------------------- التحليلات ----------------------
    st.subheader("توزيع التقديرات")
    plot_grades_distribution(filtered_data)
    
    st.subheader("أداء المواد الدراسية")
    plot_subject_scores(filtered_data)
    
    # عرض البيانات
    st.subheader("عرض البيانات")
    st.dataframe(filtered_data.head())

if __name__ == "__main__":
    main()