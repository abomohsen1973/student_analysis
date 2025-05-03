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
@st.cache_data(ttl=3600)  # تحديث البيانات كل ساعة
def load_data():
    """تحميل البيانات من ملف CSV على Google Drive"""
    try:
        # رابط ملف CSV على Google Drive (تأكد من أنه بصيغة uc?id=)
        CSV_URL = "https://drive.google.com/uc?id=1VTcIyYiV-KwWU9rutlGLsThbiQOIpwpF"
        
        # قراءة البيانات مع تحديد الترميز العربي
        df = pd.read_csv(CSV_URL, usecols=range(19), encoding='utf-8')
        
        # أسماء الأعمدة المتوقعة
        column_names = [
            'الطالب', 'الجنس', 'الصف', 'الفصل الدراسي',
            'المادة1', 'المادة2', 'المادة3', 'المادة4', 'المادة5', 
            'المادة6', 'المادة7', 'المادة8', 'المادة9', 'المادة10',
            'المادة11', 'المادة12', 'المادة13', 'المعدل', 'التقدير العام'
        ]
        
        # تعيين أسماء الأعمدة مع التحقق من التوافق
        if len(df.columns) == len(column_names):
            df.columns = column_names
        else:
            st.warning("عدد الأعمدة في الملف لا يتطابق مع الأعمدة المتوقعة")
        
        # تنظيف البيانات
        df = df.replace(['', ' ', 'NaN', 'NA', 'N/A', 'nan', 'null'], np.nan)
        
        # تحويل الأعمدة الرقمية
        numeric_cols = [col for col in df.columns if col.startswith('المادة') or col == 'المعدل']
        for col in numeric_cols:
            if col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].str.replace('%', '', regex=False).astype(float)
        
        # تحديد المرحلة التعليمية
        if 'الصف' in df.columns:
            df['المرحلة'] = df['الصف'].apply(
                lambda x: 'ابتدائي' if pd.notna(x) and ('ابتدائي' in str(x) or '1' in str(x) or '2' in str(x) or '3' in str(x)) 
                else 'متوسط' if pd.notna(x) else 'غير محدد'
            )
        else:
            df['المرحلة'] = 'غير محدد'
        
        # إضافة عمود آخر تحديث
        df['آخر_تحديث'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return df
    
    except Exception as e:
        st.error(f"❌ خطأ في تحميل البيانات: {str(e)}")
        return pd.DataFrame()  # إرجاع DataFrame فارغ بدلاً من None

# ---------------------- وظائف مساعدة ----------------------
def create_bar_chart(data, x, y, title, color=None, barmode='group', text=None):
    """إنشاء مخطط شريطي مخصص"""
    fig = px.bar(
        data,
        x=x,
        y=y,
        color=color,
        barmode=barmode,
        title=title,
        text=text,
        template="plotly_white",
        height=500
    )
    if text:
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='inside')
    fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
    return fig

def create_pie_chart(data, values, names, title, hole=0.3):
    """إنشاء مخطط دائري مخصص"""
    return px.pie(
        data,
        values=values,
        names=names,
        title=title,
        hole=hole
    )

# ---------------------- واجهة المستخدم ----------------------
def main():
    # عنوان التطبيق
    st.title("لوحة تحليل أداء الطلاب 📊")
    
    # زر لتحديث البيانات يدويًا
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("🔄 تحديث البيانات", help="انقر لتحديث البيانات من المصدر"):
            st.cache_data.clear()
            st.rerun()
    
    # تحميل البيانات
    with st.spinner('⏳ جاري تحميل البيانات...'):
        data = load_data()
    
    if data is None or data.empty:
        st.error("⚠️ لا توجد بيانات متاحة للعرض. يرجى التحقق من اتصال الإنترنت أو صحة الملف.")
        return
    
    # ---------------------- الفلترات ----------------------
    with st.sidebar:
        st.header("🔍 خيارات التصفية")
        
        # اختيار المرحلة
        stage_options = ['ابتدائي', 'متوسط']
        if 'المرحلة' in data.columns:
            stage_options = sorted(data['المرحلة'].dropna().unique().tolist())
        stage = st.radio("🏫 المرحلة:", stage_options, horizontal=True)
        
        # اختيار الفصل الدراسي
        semester_options = ["كل الفصول"]
        if 'الفصل الدراسي' in data.columns:
            semester_options += sorted(data["الفصل الدراسي"].dropna().unique().tolist())
        semester = st.selectbox("📚 الفصل الدراسي", semester_options)
        
        # اختيار المدرسة
        school_options = ["كل المدارس"]
        if 'اسم المدرسة' in data.columns:
            school_options += sorted(data["اسم المدرسة"].dropna().unique().tolist())
        school = st.selectbox("🏛️ المدرسة:", school_options)
        
        # اختيار المادة
        subjects = [col for col in data.columns if col.startswith('المادة') and col in data.columns]
        subject = st.selectbox("📖 المادة:", ["كل المواد"] + sorted(subjects))
        
        # عدد المدارس المعروضة
        max_schools = 0
        if 'اسم المدرسة' in data.columns:
            max_schools = len(data["اسم المدرسة"].unique())
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
        st.error(f"❌ خطأ في تصفية البيانات: {str(e)}")
        st.stop()
    
    # ---------------------- المؤشرات الرئيسية ----------------------
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 عدد الطلاب", len(filtered_data))
    
    with col2:
        avg = filtered_data['المعدل'].mean(skipna=True) if 'المعدل' in filtered_data.columns else np.nan
        st.metric("📈 المتوسط العام", f"{avg:.2f}%" if not pd.isna(avg) else "غير متاح")
    
    with col3:
        st.metric("🕒 آخر تحديث", filtered_data['آخر_تحديث'].iloc[0] if 'آخر_تحديث' in filtered_data.columns else "غير معروف")
    
    with col4:
        if 'المواظبة' in filtered_data.columns:
            attendance = filtered_data['المواظبة'].mean(skipna=True)
            st.metric("📅 متوسط المواظبة", f"{attendance:.1f}%" if not pd.isna(attendance) else "غير متاح")
        else:
            st.metric("📅 متوسط المواظبة", "غير متاح")
    
    # ---------------------- تحليل المواد الدراسية ----------------------
    if not filtered_data.empty and subjects:
        st.markdown("---")
        st.subheader("📚 متوسط نتائج الطلاب لكل مادة")
        
        if semester == "كل الفصول" and 'الفصل الدراسي' in filtered_data.columns:
            avg_subject_scores = filtered_data.melt(
                id_vars=['الفصل الدراسي'],
                value_vars=subjects,
                var_name='المادة',
                value_name='الدرجة'
            ).groupby(['الفصل الدراسي', 'المادة'], dropna=False)['الدرجة'].mean().reset_index()
            
            fig = create_bar_chart(
                avg_subject_scores,
                x='المادة',
                y='الدرجة',
                color='الفصل الدراسي',
                title="متوسط نتائج الطلاب لكل مادة (مقسمة حسب الفصل)",
                text='الدرجة'
            )
        else:
            avg_subject_scores = filtered_data[subjects].mean().reset_index()
            avg_subject_scores.columns = ['المادة', 'الدرجة']
            
            fig = create_bar_chart(
                avg_subject_scores,
                x='المادة',
                y='الدرجة',
                title="متوسط نتائج الطلاب لكل مادة",
                text='الدرجة'
            )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # ---------------------- تحليل التقديرات ----------------------
        if 'التقدير العام' in filtered_data.columns:
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
                        st.plotly_chart(
                            create_pie_chart(
                                grade_dist,
                                values='عدد الطلاب',
                                names='التقدير',
                                title=f"توزيع التقديرات في {sem}"
                            ),
                            use_container_width=True
                        )
                    with col2:
                        st.plotly_chart(
                            create_bar_chart(
                                grade_dist,
                                x='التقدير',
                                y='عدد الطلاب',
                                title=f"توزيع التقديرات في {sem}"
                            ),
                            use_container_width=True
                        )
            else:
                grade_dist = filtered_data['التقدير العام'].value_counts().reindex(grade_order, fill_value=0).reset_index()
                grade_dist.columns = ['التقدير', 'عدد الطلاب']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(
                        create_pie_chart(
                            grade_dist,
                            values='عدد الطلاب',
                            names='التقدير',
                            title="توزيع التقديرات"
                        ),
                        use_container_width=True
                    )
                with col2:
                    st.plotly_chart(
                        create_bar_chart(
                            grade_dist,
                            x='التقدير',
                            y='عدد الطلاب',
                            title="توزيع التقديرات"
                        ),
                        use_container_width=True
                    )
        
        # ---------------------- تحليل المدارس ----------------------
        if subject != "كل المواد" and subject in filtered_data.columns and 'اسم المدرسة' in filtered_data.columns:
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
                
                # توزيع الدرجات للمادة المحددة
                st.subheader(f"📊 توزيع درجات {subject}")
                fig_dist = px.histogram(filtered_data, x=subject, nbins=20,
                                      title=f"توزيع درجات {subject}")
                st.plotly_chart(fig_dist, use_container_width=True)
            except Exception as e:
                st.error(f"❌ خطأ في تحليل المدارس: {str(e)}")

if __name__ == "__main__":
    main()