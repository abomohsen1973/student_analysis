<<<<<<< HEAD
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np

# ---------------------- إعدادات التطبيق ----------------------
st.set_page_config(
    page_title="لوحة تحليل أداء الطلاب",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------- أنماط CSS للتطبيق ----------------------
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

# ---------------------- تحميل البيانات من Google Drive ----------------------
@st.cache_data(ttl=None)  # لا تحديث تلقائي - تحديث يدوي فقط
def load_data():
    """تحميل البيانات من ملف CSV على Google Drive"""
    try:
        # رابط ملف CSV على Google Drive (تأكد من أنه بصيغة uc?id=)
        CSV_URL = "https://drive.google.com/uc?id=1VTcIyYiV-KwWU9rutlGLsThbiQOIpwpF"
        
        # قراءة البيانات من الرابط (قراءة أول 19 عمودًا فقط: A إلى S)
        df = pd.read_csv(CSV_URL, usecols=range(19))  # استخدام أول 19 عمودًا فقط
        
        # تحديد أسماء الأعمدة يدويًا (اختياري إذا لم تكن متوفرة في CSV)
        column_names = [
            'الطالب', 'الجنس', 'الصف', 'الفصل الدراسي',
            'المادة1', 'المادة2', 'المادة3', 'المادة4', 'المادة5', 
            'المادة6', 'المادة7', 'المادة8', 'المادة9', 'المادة10',
            'المادة11', 'المادة12', 'المادة13', 'المعدل', 'التقدير العام'
        ]
        
        # تعيين أسماء الأعمدة (إذا كانت غير موجودة في CSV)
        if len(df.columns) == 19:
            df.columns = column_names
        
        # تنظيف البيانات
        df = df.replace(['', ' ', 'NaN', 'NA', 'N/A'], np.nan)
        
        # تحويل عمود المعدل إلى رقمي
        if 'المعدل' in df.columns:
            df['المعدل'] = df['المعدل'].str.replace('%', '', regex=False).astype(float)
        
        # تحديد المرحلة التعليمية
        df['المرحلة'] = df['الصف'].apply(lambda x: 'ابتدائي' if pd.notna(x) and 'ابتدائي' in str(x) else 'متوسط')
        
        # إضافة عمود آخر تحديث
        df['آخر_تحديث'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return df
    
    except Exception as e:
        st.error(f"❌ خطأ في تحميل البيانات: {e}")
        return None

# ---------------------- واجهة المستخدم ----------------------
def main():
    # عنوان التطبيق
    st.title("لوحة تحليل أداء الطلاب 📊")
    
    # زر لتحديث البيانات يدويًا
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("🔄 تحديث البيانات"):
            st.cache_data.clear()
            st.rerun()
    
    # تحميل البيانات
    with st.spinner('⏳ جاري تحميل البيانات...'):
        data = load_data()
    
    if data is None or data.empty:
        st.warning("⚠️ لا توجد بيانات متاحة للعرض.")
        return
    
    # ---------------------- الفلترات ----------------------
    with st.sidebar:
        st.header("🔍 خيارات التصفية")
        
        # اختيار الفصل الدراسي
        if 'الفصل الدراسي' in data.columns:
            semester_options = ["كل الفصول"] + sorted(data["الفصل الدراسي"].dropna().unique())
        else:
            semester_options = ["كل الفصول"]
        semester = st.selectbox("📚 الفصل الدراسي", semester_options)
        
        # اختيار المرحلة
        stage = st.radio("🏫 المرحلة:", ['ابتدائي', 'متوسط'], horizontal=True)
        
        # اختيار المدرسة
        if 'اسم المدرسة' in data.columns:
            school_options = ["كل المدارس"] + sorted(data["اسم المدرسة"].dropna().unique())
        else:
            school_options = ["كل المدارس"]
        school = st.selectbox("🏛️ المدرسة:", school_options)
        
        # اختيار المادة
        subjects = [col for col in data.columns if col not in [
            'الفصل الدراسي', 'اسم المدرسة', 'الجنس', 'اسم الطالب', 
            'الصف', 'السلوك', 'المواظبة', 'المعدل', 'التقدير العام', 
            'المرحلة', 'آخر_تحديث'
        ] if col in data.columns]
        
        if not subjects:
            st.warning("⚠️ لا توجد مواد متاحة للتحليل")
            subject = "لا توجد مواد"
        else:
            subject = st.selectbox("📖 المادة:", ["كل المواد"] + sorted(subjects))
        
        # عدد المدارس المعروضة
        if 'اسم المدرسة' in data.columns:
            max_schools = len(data["اسم المدرسة"].unique())
        else:
            max_schools = 0
        schools_to_show = st.slider(
            "🔢 عدد المدارس المعروضة للمقارنة",
            min_value=5,
            max_value=min(30, max_schools) if max_schools > 0 else 5,
            value=10,
            step=1
        )
    
    # ---------------------- تصفية البيانات ----------------------
    try:
        filtered_data = data[data['المرحلة'] == stage]
        
        if semester != "كل الفصول" and 'الفصل الدراسي' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data["الفصل الدراسي"] == semester]
        
        if school != "كل المدارس" and 'اسم المدرسة' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data["اسم المدرسة"] == school]
    except Exception as e:
        st.error(f"❌ خطأ في تصفية البيانات: {e}")
        return
    
    # ---------------------- المؤشرات الرئيسية ----------------------
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 عدد الطلاب", len(filtered_data))
    
    with col2:
        if 'المعدل' in filtered_data.columns:
            avg = filtered_data['المعدل'].mean(skipna=True)
            st.metric("📈 المتوسط العام", f"{avg:.2f}%" if not pd.isna(avg) else "غير متاح")
        else:
            st.metric("📈 المتوسط العام", "غير متاح")
    
    with col3:
        st.metric("🕒 آخر تحديث", filtered_data['آخر_تحديث'].iloc[0])
    
    with col4:
        if 'المواظبة' in filtered_data.columns:
            attendance = filtered_data['المواظبة'].mean(skipna=True)
            st.metric("📅 متوسط المواظبة", f"{attendance:.1f}%" if not pd.isna(attendance) else "غير متاح")
        else:
            st.metric("📅 متوسط المواظبة", "غير متاح")
    
    # ---------------------- عرض ملاحظات البيانات ----------------------
    if 'المادة1' in filtered_data.columns and subjects:
        missing_data_count = filtered_data[subjects].isna().any(axis=1).sum()
        if missing_data_count > 0:
            st.info(f"ℹ️ ملاحظة: يوجد {missing_data_count} طالبًا لديهم بيانات ناقصة في بعض المواد.")
    
    # ---------------------- تحليل المواد الدراسية ----------------------
    if not filtered_data.empty:
        st.markdown("---")
        st.subheader("📚 متوسط نتائج الطلاب لكل مادة")
        
        if semester == "كل الفصول" and 'الفصل الدراسي' in filtered_data.columns:
            avg_subject_scores = filtered_data.melt(
                id_vars=['الفصل الدراسي'],
                value_vars=subjects,
                var_name='المادة',
                value_name='الدرجة'
            ).groupby(['الفصل الدراسي', 'المادة'], dropna=False)['الدرجة'].mean().reset_index()
            
            fig = px.bar(
                avg_subject_scores,
                x='المادة',
                y='الدرجة',
                color='الفصل الدراسي',
                barmode='group',
                title="متوسط نتائج الطلاب لكل مادة (مقسمة حسب الفصل)",
                labels={'الدرجة': 'متوسط الدرجة'},
                text='الدرجة',
                template="plotly_white",
                height=500
            )
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='inside')
            fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
        else:
            avg_subject_scores = filtered_data[subjects].mean().reset_index()
            avg_subject_scores.columns = ['المادة', 'الدرجة']
            
            fig = px.bar(
                avg_subject_scores,
                x='المادة',
                y='الدرجة',
                title="متوسط نتائج الطلاب لكل مادة",
                labels={'الدرجة': 'متوسط الدرجة'},
                text='الدرجة',
                template="plotly_white",
                height=500
            )
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='inside')
        
        st.plotly_chart(fig, use_container_width=True)
        
        # ---------------------- تحليل التقديرات ----------------------
        st.markdown("---")
        st.subheader("🏆 توزيع الطلاب حسب التقديرات")
        
        grade_order = ["ممتاز", "جيد جداً", "جيد", "مقبول"]
        
        if semester == "كل الفصول" and 'الفصل الدراسي' in filtered_data.columns:
            semesters = filtered_data["الفصل الدراسي"].unique()
            for sem in semesters:
                sem_data = filtered_data[filtered_data["الفصل الدراسي"] == sem]
                grade_dist = sem_data['التقدير العام'].value_counts().reindex(grade_order, fill_value=0).reset_index()
                grade_dist.columns = ['التقدير', 'عدد الطلاب']
                
                col1, col2 = st.columns(2)
                with col1:
                    fig_pie = px.pie(grade_dist, values='عدد الطلاب', names='التقدير',
                                    title=f"توزيع التقديرات في {sem}", hole=0.3)
                    st.plotly_chart(fig_pie, use_container_width=True)
                with col2:
                    fig_bar = px.bar(grade_dist, x='التقدير', y='عدد الطلاب',
                                    title=f"توزيع التقديرات في {sem}")
                    st.plotly_chart(fig_bar, use_container_width=True)
        else:
            grade_dist = filtered_data['التقدير العام'].value_counts().reindex(grade_order, fill_value=0).reset_index()
            grade_dist.columns = ['التقدير', 'عدد الطلاب']
            
            col1, col2 = st.columns(2)
            with col1:
                fig_pie = px.pie(grade_dist, values='عدد الطلاب', names='التقدير',
                                title="توزيع التقديرات", hole=0.3)
                st.plotly_chart(fig_pie, use_container_width=True)
            with col2:
                fig_bar = px.bar(grade_dist, x='التقدير', y='عدد الطلاب',
                                title="توزيع التقديرات")
                st.plotly_chart(fig_bar, use_container_width=True)
        
        # ---------------------- مقارنة الفصول الدراسية ----------------------
        if semester == "كل الفصول" and 'الفصل الدراسي' in filtered_data.columns:
            st.markdown("---")
            st.subheader("📈 مقارنة بين الفصول الدراسية")
            
            grade_comp = filtered_data.groupby('الفصل الدراسي')['التقدير العام'].value_counts().unstack().reindex(columns=grade_order, fill_value=0)
            grade_comp = grade_comp.reset_index().melt(id_vars='الفصل الدراسي', var_name='التقدير', value_name='عدد الطلاب')
            
            fig = px.bar(grade_comp, x='الفصل الدراسي', y='عدد الطلاب', color='التقدير',
                        barmode='group', title="مقارنة توزيع التقديرات بين الفصول")
            st.plotly_chart(fig, use_container_width=True)
        
        # ---------------------- تحليل المدارس (عند اختيار مادة) ----------------------
        if subject != "كل المواد" and subject != "لا توجد مواد" and 'اسم المدرسة' in filtered_data.columns and subject in filtered_data.columns:
            st.markdown("---")
            st.subheader(f"🏫 تحليل أداء المدارس في {subject}")
            
            try:
                school_avg = filtered_data.groupby('اسم المدرسة')[subject].mean().reset_index()
                school_avg = school_avg.sort_values(by=subject, ascending=False)
                
                top_schools = school_avg.head(schools_to_show)
                fig_top = px.bar(
                    top_schools, 
                    x=subject, 
                    y='اسم المدرسة', 
                    orientation='h',
                    title=f"أعلى {schools_to_show} مدارس في {subject}", 
                    color=subject, 
                    color_continuous_scale='Tealgrn'
                )
                
                if len(school_avg) >= schools_to_show:
                    bottom_schools = school_avg.tail(schools_to_show).sort_values(by=subject)
                    fig_bottom = px.bar(
                        bottom_schools, 
                        x=subject, 
                        y='اسم المدرسة', 
                        orientation='h',
                        title=f"أقل {schools_to_show} مدارس في {subject}", 
                        color=subject, 
                        color_continuous_scale='Sunsetdark'
                    )
                    col1, col2 = st.columns(2)
                    with col1:
                        st.plotly_chart(fig_top, use_container_width=True)
                    with col2:
                        st.plotly_chart(fig_bottom, use_container_width=True)
                else:
                    st.plotly_chart(fig_top, use_container_width=True)
                    st.warning(f"⚠️ عدد المدارس المتاحة ({len(school_avg)}) أقل من العدد المطلوب عرضه ({schools_to_show})")
                
                # ---------------------- توزيع الدرجات للمادة المحددة ----------------------
                st.subheader(f"📊 توزيع درجات {subject}")
                fig_dist = px.histogram(filtered_data, x=subject, nbins=20,
                                      title=f"توزيع درجات {subject}")
                st.plotly_chart(fig_dist, use_container_width=True)
            except Exception as e:
                st.error(f"❌ خطأ في تحليل المدارس: {e}")

if __name__ == "__main__":
=======
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np

# ---------------------- إعدادات التطبيق ----------------------
st.set_page_config(
    page_title="لوحة تحليل أداء الطلاب",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------- أنماط CSS للتطبيق ----------------------
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

# ---------------------- تحميل البيانات من Google Drive ----------------------
@st.cache_data(ttl=None)  # لا تحديث تلقائي - تحديث يدوي فقط
def load_data():
    """تحميل البيانات من ملف CSV على Google Drive"""
    try:
        # رابط ملف CSV على Google Drive (تأكد من أنه بصيغة uc?id=)
        CSV_URL = "https://drive.google.com/uc?id=1VTcIyYiV-KwWU9rutlGLsThbiQOIpwpF"
        
        # قراءة البيانات من الرابط (قراءة أول 19 عمودًا فقط: A إلى S)
        df = pd.read_csv(CSV_URL, usecols=range(19))  # استخدام أول 19 عمودًا فقط
        
        # تحديد أسماء الأعمدة يدويًا (اختياري إذا لم تكن متوفرة في CSV)
        column_names = [
            'الطالب', 'الجنس', 'الصف', 'الفصل الدراسي',
            'المادة1', 'المادة2', 'المادة3', 'المادة4', 'المادة5', 
            'المادة6', 'المادة7', 'المادة8', 'المادة9', 'المادة10',
            'المادة11', 'المادة12', 'المادة13', 'المعدل', 'التقدير العام'
        ]
        
        # تعيين أسماء الأعمدة (إذا كانت غير موجودة في CSV)
        if len(df.columns) == 19:
            df.columns = column_names
        
        # تنظيف البيانات
        df = df.replace(['', ' ', 'NaN', 'NA', 'N/A'], np.nan)
        
        # تحويل عمود المعدل إلى رقمي
        if 'المعدل' in df.columns:
            df['المعدل'] = df['المعدل'].str.replace('%', '', regex=False).astype(float)
        
        # تحديد المرحلة التعليمية
        df['المرحلة'] = df['الصف'].apply(lambda x: 'ابتدائي' if pd.notna(x) and 'ابتدائي' in str(x) else 'متوسط')
        
        # إضافة عمود آخر تحديث
        df['آخر_تحديث'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return df
    
    except Exception as e:
        st.error(f"❌ خطأ في تحميل البيانات: {e}")
        return None

# ---------------------- واجهة المستخدم ----------------------
def main():
    # عنوان التطبيق
    st.title("لوحة تحليل أداء الطلاب 📊")
    
    # زر لتحديث البيانات يدويًا
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("🔄 تحديث البيانات"):
            st.cache_data.clear()
            st.rerun()
    
    # تحميل البيانات
    with st.spinner('⏳ جاري تحميل البيانات...'):
        data = load_data()
    
    if data is None or data.empty:
        st.warning("⚠️ لا توجد بيانات متاحة للعرض.")
        return
    
    # ---------------------- الفلترات ----------------------
    with st.sidebar:
        st.header("🔍 خيارات التصفية")
        
        # اختيار الفصل الدراسي
        if 'الفصل الدراسي' in data.columns:
            semester_options = ["كل الفصول"] + sorted(data["الفصل الدراسي"].dropna().unique())
        else:
            semester_options = ["كل الفصول"]
        semester = st.selectbox("📚 الفصل الدراسي", semester_options)
        
        # اختيار المرحلة
        stage = st.radio("🏫 المرحلة:", ['ابتدائي', 'متوسط'], horizontal=True)
        
        # اختيار المدرسة
        if 'اسم المدرسة' in data.columns:
            school_options = ["كل المدارس"] + sorted(data["اسم المدرسة"].dropna().unique())
        else:
            school_options = ["كل المدارس"]
        school = st.selectbox("🏛️ المدرسة:", school_options)
        
        # اختيار المادة
        subjects = [col for col in data.columns if col not in [
            'الفصل الدراسي', 'اسم المدرسة', 'الجنس', 'اسم الطالب', 
            'الصف', 'السلوك', 'المواظبة', 'المعدل', 'التقدير العام', 
            'المرحلة', 'آخر_تحديث'
        ] if col in data.columns]
        
        if not subjects:
            st.warning("⚠️ لا توجد مواد متاحة للتحليل")
            subject = "لا توجد مواد"
        else:
            subject = st.selectbox("📖 المادة:", ["كل المواد"] + sorted(subjects))
        
        # عدد المدارس المعروضة
        if 'اسم المدرسة' in data.columns:
            max_schools = len(data["اسم المدرسة"].unique())
        else:
            max_schools = 0
        schools_to_show = st.slider(
            "🔢 عدد المدارس المعروضة للمقارنة",
            min_value=5,
            max_value=min(30, max_schools) if max_schools > 0 else 5,
            value=10,
            step=1
        )
    
    # ---------------------- تصفية البيانات ----------------------
    try:
        filtered_data = data[data['المرحلة'] == stage]
        
        if semester != "كل الفصول" and 'الفصل الدراسي' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data["الفصل الدراسي"] == semester]
        
        if school != "كل المدارس" and 'اسم المدرسة' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data["اسم المدرسة"] == school]
    except Exception as e:
        st.error(f"❌ خطأ في تصفية البيانات: {e}")
        return
    
    # ---------------------- المؤشرات الرئيسية ----------------------
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 عدد الطلاب", len(filtered_data))
    
    with col2:
        if 'المعدل' in filtered_data.columns:
            avg = filtered_data['المعدل'].mean(skipna=True)
            st.metric("📈 المتوسط العام", f"{avg:.2f}%" if not pd.isna(avg) else "غير متاح")
        else:
            st.metric("📈 المتوسط العام", "غير متاح")
    
    with col3:
        st.metric("🕒 آخر تحديث", filtered_data['آخر_تحديث'].iloc[0])
    
    with col4:
        if 'المواظبة' in filtered_data.columns:
            attendance = filtered_data['المواظبة'].mean(skipna=True)
            st.metric("📅 متوسط المواظبة", f"{attendance:.1f}%" if not pd.isna(attendance) else "غير متاح")
        else:
            st.metric("📅 متوسط المواظبة", "غير متاح")
    
    # ---------------------- عرض ملاحظات البيانات ----------------------
    if 'المادة1' in filtered_data.columns and subjects:
        missing_data_count = filtered_data[subjects].isna().any(axis=1).sum()
        if missing_data_count > 0:
            st.info(f"ℹ️ ملاحظة: يوجد {missing_data_count} طالبًا لديهم بيانات ناقصة في بعض المواد.")
    
    # ---------------------- تحليل المواد الدراسية ----------------------
    if not filtered_data.empty:
        st.markdown("---")
        st.subheader("📚 متوسط نتائج الطلاب لكل مادة")
        
        if semester == "كل الفصول" and 'الفصل الدراسي' in filtered_data.columns:
            avg_subject_scores = filtered_data.melt(
                id_vars=['الفصل الدراسي'],
                value_vars=subjects,
                var_name='المادة',
                value_name='الدرجة'
            ).groupby(['الفصل الدراسي', 'المادة'], dropna=False)['الدرجة'].mean().reset_index()
            
            fig = px.bar(
                avg_subject_scores,
                x='المادة',
                y='الدرجة',
                color='الفصل الدراسي',
                barmode='group',
                title="متوسط نتائج الطلاب لكل مادة (مقسمة حسب الفصل)",
                labels={'الدرجة': 'متوسط الدرجة'},
                text='الدرجة',
                template="plotly_white",
                height=500
            )
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='inside')
            fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
        else:
            avg_subject_scores = filtered_data[subjects].mean().reset_index()
            avg_subject_scores.columns = ['المادة', 'الدرجة']
            
            fig = px.bar(
                avg_subject_scores,
                x='المادة',
                y='الدرجة',
                title="متوسط نتائج الطلاب لكل مادة",
                labels={'الدرجة': 'متوسط الدرجة'},
                text='الدرجة',
                template="plotly_white",
                height=500
            )
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='inside')
        
        st.plotly_chart(fig, use_container_width=True)
        
        # ---------------------- تحليل التقديرات ----------------------
        st.markdown("---")
        st.subheader("🏆 توزيع الطلاب حسب التقديرات")
        
        grade_order = ["ممتاز", "جيد جداً", "جيد", "مقبول"]
        
        if semester == "كل الفصول" and 'الفصل الدراسي' in filtered_data.columns:
            semesters = filtered_data["الفصل الدراسي"].unique()
            for sem in semesters:
                sem_data = filtered_data[filtered_data["الفصل الدراسي"] == sem]
                grade_dist = sem_data['التقدير العام'].value_counts().reindex(grade_order, fill_value=0).reset_index()
                grade_dist.columns = ['التقدير', 'عدد الطلاب']
                
                col1, col2 = st.columns(2)
                with col1:
                    fig_pie = px.pie(grade_dist, values='عدد الطلاب', names='التقدير',
                                    title=f"توزيع التقديرات في {sem}", hole=0.3)
                    st.plotly_chart(fig_pie, use_container_width=True)
                with col2:
                    fig_bar = px.bar(grade_dist, x='التقدير', y='عدد الطلاب',
                                    title=f"توزيع التقديرات في {sem}")
                    st.plotly_chart(fig_bar, use_container_width=True)
        else:
            grade_dist = filtered_data['التقدير العام'].value_counts().reindex(grade_order, fill_value=0).reset_index()
            grade_dist.columns = ['التقدير', 'عدد الطلاب']
            
            col1, col2 = st.columns(2)
            with col1:
                fig_pie = px.pie(grade_dist, values='عدد الطلاب', names='التقدير',
                                title="توزيع التقديرات", hole=0.3)
                st.plotly_chart(fig_pie, use_container_width=True)
            with col2:
                fig_bar = px.bar(grade_dist, x='التقدير', y='عدد الطلاب',
                                title="توزيع التقديرات")
                st.plotly_chart(fig_bar, use_container_width=True)
        
        # ---------------------- مقارنة الفصول الدراسية ----------------------
        if semester == "كل الفصول" and 'الفصل الدراسي' in filtered_data.columns:
            st.markdown("---")
            st.subheader("📈 مقارنة بين الفصول الدراسية")
            
            grade_comp = filtered_data.groupby('الفصل الدراسي')['التقدير العام'].value_counts().unstack().reindex(columns=grade_order, fill_value=0)
            grade_comp = grade_comp.reset_index().melt(id_vars='الفصل الدراسي', var_name='التقدير', value_name='عدد الطلاب')
            
            fig = px.bar(grade_comp, x='الفصل الدراسي', y='عدد الطلاب', color='التقدير',
                        barmode='group', title="مقارنة توزيع التقديرات بين الفصول")
            st.plotly_chart(fig, use_container_width=True)
        
        # ---------------------- تحليل المدارس (عند اختيار مادة) ----------------------
        if subject != "كل المواد" and subject != "لا توجد مواد" and 'اسم المدرسة' in filtered_data.columns and subject in filtered_data.columns:
            st.markdown("---")
            st.subheader(f"🏫 تحليل أداء المدارس في {subject}")
            
            try:
                school_avg = filtered_data.groupby('اسم المدرسة')[subject].mean().reset_index()
                school_avg = school_avg.sort_values(by=subject, ascending=False)
                
                top_schools = school_avg.head(schools_to_show)
                fig_top = px.bar(
                    top_schools, 
                    x=subject, 
                    y='اسم المدرسة', 
                    orientation='h',
                    title=f"أعلى {schools_to_show} مدارس في {subject}", 
                    color=subject, 
                    color_continuous_scale='Tealgrn'
                )
                
                if len(school_avg) >= schools_to_show:
                    bottom_schools = school_avg.tail(schools_to_show).sort_values(by=subject)
                    fig_bottom = px.bar(
                        bottom_schools, 
                        x=subject, 
                        y='اسم المدرسة', 
                        orientation='h',
                        title=f"أقل {schools_to_show} مدارس في {subject}", 
                        color=subject, 
                        color_continuous_scale='Sunsetdark'
                    )
                    col1, col2 = st.columns(2)
                    with col1:
                        st.plotly_chart(fig_top, use_container_width=True)
                    with col2:
                        st.plotly_chart(fig_bottom, use_container_width=True)
                else:
                    st.plotly_chart(fig_top, use_container_width=True)
                    st.warning(f"⚠️ عدد المدارس المتاحة ({len(school_avg)}) أقل من العدد المطلوب عرضه ({schools_to_show})")
                
                # ---------------------- توزيع الدرجات للمادة المحددة ----------------------
                st.subheader(f"📊 توزيع درجات {subject}")
                fig_dist = px.histogram(filtered_data, x=subject, nbins=20,
                                      title=f"توزيع درجات {subject}")
                st.plotly_chart(fig_dist, use_container_width=True)
            except Exception as e:
                st.error(f"❌ خطأ في تحليل المدارس: {e}")

if __name__ == "__main__":
>>>>>>> 438b900873abe7dc6d7a40ae7a11bcda8a0c065e
    main()