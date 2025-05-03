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
    except Exception as e:
        st.error(f"حدث خطأ أثناء تحميل البيانات: {e}")
        
        # تغيير الثيم إلى الفاتح
st.set_page_config(page_title="لوحة تحليل أداء الطلاب", page_icon="📊", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
    <style>
        .reportview-container {
            background-color: #FFFFFF;
            color: #000000;
        }
        .sidebar .sidebar-content {
            background-color: #F5F5F5;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #007BFF;
        }
        .stButton > button {
            background-color: #007BFF;
            color: white;
        }
        .stSelectbox > div > div {
            background-color: #E9ECEF;
            color: black;
        }
    </style>
""", unsafe_allow_html=True)

# عنوان التطبيق (محور ومُنسق)
st.markdown("""
    <div style='text-align: center; font-size: 36px; font-weight: bold; color: darkgreen;'>
        لوحة تحليل أداء الطلاب
    </div>
""", unsafe_allow_html=True)

# وصف التطبيق
st.markdown("""
    <div style='text-align: center; font-size: 20px; color: ##333333;'>
        تحليل بيانات نتائج اختبارات الطلاب للعام الدراسي 1445هـ / 1446هـ للمرحلتين الابتدائية والمتوسطة
    </div>
""", unsafe_allow_html=True)

# رفع ملف Excel
uploaded_file = st.file_uploader("رفع ملف إكسل", type=["xlsx"])
if uploaded_file is not None:
    # قراءة البيانات من الملف
    data = pd.read_excel(uploaded_file)

    # تنظيف البيانات
    data.dropna(inplace=True)
    data['المعدل'] = data['المعدل'].str.replace('%', '').astype(float)

    # استخراج أسماء المواد من الأعمدة
    subjects = [
        col for col in data.columns
        if col not in ['الفصل الدراسي', 'اسم المدرسة', 'الجنس', 'اسم الطالب', 'الصف', 'السلوك', 'المواظبة', 'المعدل', 'التقدير العام']
    ]

    # تعريف الترتيب المخصص للتقديرات
    grade_order = ["ممتاز", "جيد جداً", "جيد", "مقبول"]

    # خيارات التصفية
    st.sidebar.header("خيارات التصفية")
    semester = st.sidebar.selectbox("اختر الفصل الدراسي", ["كل الفصول"] + list(data["الفصل الدراسي"].unique()))
    school = st.sidebar.selectbox("اختر المدرسة", ["كل المدارس"] + list(data["اسم المدرسة"].unique()))
    gender = st.sidebar.selectbox("اختر الجنس", ["كل الأجناس"] + list(data["الجنس"].unique()))
    grade = st.sidebar.selectbox("اختر الصف", ["كل الصفوف"] + list(data["الصف"].unique()))
    subject = st.sidebar.selectbox("اختر المادة", ["كل المواد"] + subjects)

    # تطبيق التصفية
    filtered_data = data.copy()
    if semester != "كل الفصول":
        filtered_data = filtered_data[filtered_data["الفصل الدراسي"] == semester]
    if school != "كل المدارس":
        filtered_data = filtered_data[filtered_data["اسم المدرسة"] == school]
    if gender != "كل الأجناس":
        filtered_data = filtered_data[filtered_data["الجنس"] == gender]
    if grade != "كل الصفوف":
        filtered_data = filtered_data[filtered_data["الصف"] == grade]
    if subject != "كل المواد":
        filtered_data = filtered_data[filtered_data[subject] > 0]  # تصفية حسب المادة

    # عرض عدد الطلاب بعد التصفية بتنسيق محسن
    st.markdown(f"""
        <div style='text-align: center; font-size: 24px; font-weight: bold; color: #007BFF;'>
            عدد الطلاب بعد التصفية: {len(filtered_data)}
        </div>
    """, unsafe_allow_html=True)

    # تحليل البيانات
    if not filtered_data.empty:
        # مؤشر لمتوسط نتائج الطلاب لكل مادة
        st.subheader("متوسط نتائج الطلاب لكل مادة")
        if semester == "كل الفصول":
            # حساب المتوسط لكل مادة لكل فصل
            avg_subject_scores = filtered_data.melt(
                id_vars=['الفصل الدراسي'],
                value_vars=subjects,
                var_name='المادة',
                value_name='الدرجة'
            ).groupby(['الفصل الدراسي', 'المادة'])['الدرجة'].mean().reset_index()

            # إنشاء مخطط الأعمدة مع النص داخل الأعمدة
            fig = px.bar(
                avg_subject_scores,
                x='المادة',
                y='الدرجة',
                color='الفصل الدراسي',
                barmode='group',
                title="متوسط نتائج الطلاب لكل مادة (مقسمة حسب الفصل)",
                labels={'الدرجة': 'متوسط الدرجة', 'المادة': 'المادة'},
                text='الدرجة',  # إضافة النص داخل الأعمدة
                template="plotly_white"
            )
            # تحديث خصائص النص
            fig.update_traces(texttemplate='%{text:.2f}', textposition='inside', marker=dict(line=dict(color='white', width=1)))
        else:
            # حساب المتوسط لكل مادة فقط لهذا الفصل
            avg_subject_scores = filtered_data[subjects].mean().reset_index()
            avg_subject_scores.columns = ['المادة', 'الدرجة']

            # إنشاء مخطط الأعمدة
            fig = px.bar(
                avg_subject_scores,
                x='المادة',
                y='الدرجة',
                title="متوسط نتائج الطلاب لكل مادة",
                labels={'الدرجة': 'متوسط الدرجة', 'المادة': 'المادة'},
                template="plotly_white"
            )

        st.plotly_chart(fig, use_container_width=True)

        # المؤشرات الأخرى (بدون تعديل)
        st.subheader("توزيع الطلاب حسب التقديرات لكل فصل دراسي")
        semesters = filtered_data["الفصل الدراسي"].unique()

        for sem in semesters:
            semester_data = filtered_data[filtered_data["الفصل الدراسي"] == sem]
            
            # حساب توزيع التقديرات مع الترتيب المخصص
            grade_distribution = semester_data['التقدير العام'].value_counts().reindex(grade_order, fill_value=0)

            # التأكد من أن البيانات هي DataFrame
            if isinstance(grade_distribution, pd.Series):
                grade_distribution = grade_distribution.reset_index()
                grade_distribution.columns = ['التقدير', 'عدد الطلاب']

            # تقسيم الصفحة إلى عمودين
            col1, col2 = st.columns(2)

            with col1:
                # مؤشر دائري لتوزيع الطلاب
                fig = px.pie(
                    grade_distribution,
                    values='عدد الطلاب',
                    names='التقدير',
                    title=f"توزيع الطلاب حسب التقديرات في {sem}",
                    hole=0.3
                )
                fig.update_layout(template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # مخطط شريطي لتوزيع التقديرات
                fig = px.bar(
                    grade_distribution,
                    x='التقدير',
                    y='عدد الطلاب',
                    labels={'التقدير': 'التقدير', 'عدد الطلاب': 'عدد الطلاب'},
                    title=f"توزيع الطلاب حسب التقديرات في {sem}"
                )
                fig.update_layout(template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)

        # مقارنة بين الفصول الدراسية
        st.subheader("مقارنة بين الفصول الدراسية")
        overall_grade_distribution = filtered_data.groupby('الفصل الدراسي')['التقدير العام'].value_counts().unstack(fill_value=0)

        # إعادة ترتيب الأعمدة حسب الترتيب المخصص للتقديرات
        overall_grade_distribution = overall_grade_distribution.reindex(columns=grade_order, fill_value=0)

        # تحويل البيانات إلى صيغة طويلة لاستخدامها في مخطط Plotly
        melted_data = overall_grade_distribution.reset_index().melt(id_vars='الفصل الدراسي', var_name='التقدير', value_name='عدد الطلاب')

        # مخطط شريطي للمقارنة
        fig = px.bar(
            melted_data,
            x='الفصل الدراسي',
            y='عدد الطلاب',
            color='التقدير',
            barmode='group',
            title="مقارنة توزيع التقديرات بين الفصول الدراسية",
            labels={'عدد الطلاب': 'عدد الطلاب', 'التقدير': 'التقدير'}
        )
        fig.update_layout(template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

        # تحليل أداء المواد الدراسية
        if subject != "كل المواد":
            st.subheader(f"تحليل أداء الطلاب في {subject}")
            subject_performance = filtered_data[[subject, 'التقدير العام']].dropna()
            fig = px.histogram(
                subject_performance,
                x=subject,
                nbins=20,
                title=f"توزيع درجات الطلاب في {subject}",
                labels={subject: 'الدرجة', 'count': 'عدد الطلاب'}
            )
            fig.update_layout(template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

       # مؤشر متوسط المعدل للمدارس - نسخة مطورة
if 'المعدل' in filtered_data.columns:
    st.subheader("تحليل أداء المدارس حسب متوسط المعدل")
    
    # حساب المتوسط لكل مدرسة
    avg_school_rates = filtered_data.groupby('اسم المدرسة')['المعدل'].agg(['mean', 'count']).reset_index()
    avg_school_rates.columns = ['اسم المدرسة', 'متوسط المعدل', 'عدد الطلاب']
    
    # فلترة المدارس التي لديها عدد طلاب كافي (اختياري)
    avg_school_rates = avg_school_rates[avg_school_rates['عدد الطلاب'] >= 5]  # على الأقل 5 طلاب
    
    # إنشاء علامات تبويب لعرض النتائج
    tab1, tab2 = st.tabs(["أفضل 20 مدرسة", "أسوأ 20 مدرسة"])
    
    with tab1:
        # أفضل 20 مدرسة (تنازلي)
        top_schools = avg_school_rates.sort_values(by='متوسط المعدل', ascending=False).head(20)
        
        # إضافة عمود الترتيب
        top_schools['الترتيب'] = range(1, len(top_schools)+1)
        
        # عرض الجدول
        st.markdown("### أفضل 20 مدرسة حسب متوسط المعدل (تنازلياً)")
        st.dataframe(
            top_schools[['الترتيب', 'اسم المدرسة', 'متوسط المعدل', 'عدد الطلاب']].style
                .format({'متوسط المعدل': '{:.2f}%'})
                .background_gradient(cmap='Blues', subset=['متوسط المعدل'])
                .set_properties(**{'text-align': 'right', 'direction': 'rtl'}),
            height=600
        )
        
        # المخطط البياني
        fig_top = px.bar(
            top_schools,
            x='متوسط المعدل',
            y='اسم المدرسة',
            orientation='h',
            title="أفضل 20 مدرسة حسب متوسط المعدل",
            labels={'متوسط المعدل': 'متوسط المعدل (%)', 'اسم المدرسة': ''},
            color='متوسط المعدل',
            color_continuous_scale='Blues',
            text='متوسط المعدل',
            hover_data=['عدد الطلاب']
        )
        fig_top.update_traces(texttemplate='%{text:.2f}%', textposition='inside')
        fig_top.update_layout(yaxis={'categoryorder': 'total ascending'}, template="plotly_white")
        st.plotly_chart(fig_top, use_container_width=True)
    
    with tab2:
        # أقل 20 مدرسة (تصاعدي)
        bottom_schools = avg_school_rates.sort_values(by='متوسط المعدل', ascending=True).head(20)
        
        # إضافة عمود الترتيب
        bottom_schools['الترتيب'] = range(1, len(bottom_schools)+1)
        
        # عرض الجدول
        st.markdown("### أقل 20 مدرسة حسب متوسط المعدل (تصاعدياً)")
        st.dataframe(
            bottom_schools[['الترتيب', 'اسم المدرسة', 'متوسط المعدل', 'عدد الطلاب']].style
                .format({'متوسط المعدل': '{:.2f}%'})
                .background_gradient(cmap='Reds_r', subset=['متوسط المعدل'])
                .set_properties(**{'text-align': 'right', 'direction': 'rtl'}),
            height=600
        )
        
        # المخطط البياني
        fig_bottom = px.bar(
            bottom_schools,
            x='متوسط المعدل',
            y='اسم المدرسة',
            orientation='h',
            title="أقل 20 مدرسة حسب متوسط المعدل",
            labels={'متوسط المعدل': 'متوسط المعدل (%)', 'اسم المدرسة': ''},
            color='متوسط المعدل',
            color_continuous_scale='Reds',
            text='متوسط المعدل',
            hover_data=['عدد الطلاب']
        )
        fig_bottom.update_traces(texttemplate='%{text:.2f}%', textposition='inside')
        fig_bottom.update_layout(yaxis={'categoryorder': 'total descending'}, template="plotly_white")
        st.plotly_chart(fig_bottom, use_container_width=True)
    
    # إضافة تحليل إضافي
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("أعلى معدل مدرسة", f"{top_schools.iloc[0]['متوسط المعدل']:.2f}%", 
                 delta=f"فرق {top_schools.iloc[0]['متوسط المعدل'] - avg_school_rates['متوسط المعدل'].mean():.2f}% عن المتوسط العام")
    
    with col2:
        st.metric("أدنى معدل مدرسة", f"{bottom_schools.iloc[0]['متوسط المعدل']:.2f}%", 
                 delta=f"فرق {bottom_schools.iloc[0]['متوسط المعدل'] - avg_school_rates['متوسط المعدل'].mean():.2f}% عن المتوسط العام",
                 delta_color="inverse")
    
    with col3:
        st.metric("المتوسط العام للمدارس", f"{avg_school_rates['متوسط المعدل'].mean():.2f}%")
        
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})  # ترتيب المدارس من أعلى إلى أسفل
        st.plotly_chart(fig, use_container_width=True)