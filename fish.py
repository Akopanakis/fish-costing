import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# ---------------------------------------------------------
# 1. ΡΥΘΜΙΣΕΙΣ & CSS (ΤΟ ΕΠΑΓΓΕΛΜΑΤΙΚΟ "LOOK & FEEL")
# ---------------------------------------------------------
st.set_page_config(page_title="FishPro ERP", layout="wide", page_icon="🏭")

# Custom CSS για να μοιάζει με ακριβό λογισμικό
st.markdown("""
<style>
    /* Κάρτες Μετρήσεων */
    .metric-container {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
        border-left: 5px solid #2E86C1;
    }
    /* Τίτλοι Ενοτήτων */
    .section-title {
        font-size: 20px;
        font-weight: bold;
        color: #333;
        margin-bottom: 15px;
        border-bottom: 2px solid #2E86C1;
        padding-bottom: 5px;
    }
    /* Warning Box */
    .warning-box {
        background-color: #FFF3CD;
        color: #856404;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #FFEEBA;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. MOCK DATA (ΓΙΑ ΝΑ ΕΧΕΙΣ ΕΙΚΟΝΑ ΑΜΕΣΩΣ)
# ---------------------------------------------------------
if 'db' not in st.session_state:
    # Δημιουργία ψεύτικων δεδομένων για τον τελευταίο μήνα
    dates = pd.date_range(end=datetime.now(), periods=15)
    data = []
    for d in dates:
        inp = np.random.randint(400, 800)
        yield_pct = np.random.uniform(68, 74)
        out = inp * (yield_pct / 100)
        glazing = np.random.uniform(13, 17)
        cost = np.random.uniform(3.5, 4.2)
        supplier = np.random.choice(['Aegean Fish', 'Northen Catch', 'Blue Sea Ltd'])
        
        data.append({
            'Date': d,
            'Lot_ID': f'L-{d.strftime("%y%m%d")}',
            'Supplier': supplier,
            'Input_Kg': inp,
            'Output_Kg': out,
            'Yield_Pct': yield_pct,
            'Glazing_Pct': glazing,
            'Quality_Score': np.random.randint(85, 100), # 0-100 score
            'Cost_Per_Kg': cost,
            'Profit_Margin': 4.80 - cost
        })
    st.session_state['db'] = pd.DataFrame(data)

df = st.session_state['db']

# ---------------------------------------------------------
# 3. SIDEBAR NAVIGATION (Η ΠΛΟΗΓΗΣΗ ΣΟΥ)
# ---------------------------------------------------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2942/2942544.png", width=60)
    st.title("FishPro ERP")
    st.caption("Factory & Quality Management")
    st.markdown("---")
    
    menu = st.radio(
        "Πλοήγηση:", 
        ["📊 Executive Dashboard", "🧪 Ποιοτικός Έλεγχος (QC)", "📝 Καταχώρηση Παρτίδας", "🗄️ Ιστορικό Παραγωγής"]
    )
    
    st.markdown("---")
    st.info("📅 Ημερομηνία: " + datetime.now().strftime("%d/%m/%Y"))

# ---------------------------------------------------------
# 4. ΣΕΛΙΔΕΣ (VIEWS)
# ---------------------------------------------------------

# === VIEW A: EXECUTIVE DASHBOARD ===
if menu == "📊 Executive Dashboard":
    st.markdown("<div class='section-title'>📊 Οικονομική Επισκόπηση & Παραγωγή</div>", unsafe_allow_html=True)
    
    # Top Level KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    # Υπολογισμοί Μέσων Όρων
    avg_yield = df['Yield_Pct'].mean()
    avg_margin = df['Profit_Margin'].mean()
    total_prod = df['Output_Kg'].sum()
    
    col1.metric("Μέση Απόδοση (Yield)", f"{avg_yield:.1f}%", delta=f"{avg_yield-71.2:.1f}%", help="Στόχος: 71.2%")
    col2.metric("Μέσο Κέρδος / Kg", f"{avg_margin:.2f} €", delta="vs Budget")
    col3.metric("Συνολική Παραγωγή (15ημ)", f"{total_prod/1000:.1f} τόνοι")
    col4.metric("Δείκτης Ποιότητας", f"{df['Quality_Score'].mean():.0f}/100", delta_color="off")
    
    st.markdown("---")
    
    # Main Charts
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("📈 Τάση Κόστους & Κέρδους")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['Date'], y=df['Cost_Per_Kg'], fill='tozeroy', name='Κόστος', line=dict(color='red')))
        fig.add_trace(go.Scatter(x=df['Date'], y=[4.80]*len(df), name='Τιμή Πώλησης', line=dict(color='green', dash='dash')))
        st.plotly_chart(fig, use_container_width=True)
        st.caption("💡 **Insight:** Όσο μεγαλύτερη η απόσταση της κόκκινης γραμμής από την πράσινη, τόσο μεγαλύτερο το κέρδος.")
        
    with c2:
        st.subheader("🏆 Απόδοση ανά Προμηθευτή")
        supp_grp = df.groupby('Supplier')['Yield_Pct'].mean().reset_index()
        fig2 = px.bar(supp_grp, x='Supplier', y='Yield_Pct', color='Yield_Pct', color_continuous_scale='Bluyl')
        fig2.add_hline(y=71.2, line_dash="dot", annotation_text="Στόχος")
        st.plotly_chart(fig2, use_container_width=True)

# === VIEW B: QUALITY CONTROL (QC) ===
elif menu == "🧪 Ποιοτικός Έλεγχος (QC)":
    st.markdown("<div class='section-title'>🧪 Τμήμα Ποιοτικού Ελέγχου</div>", unsafe_allow_html=True)
    
    # QC Summary
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Glazing Average", f"{df['Glazing_Pct'].mean():.1f}%", help="Στόχος: 15% (+/- 1%)")
    kpi2.metric("Απορρίψεις", "1.2%", delta="-0.3%", delta_color="inverse", help="Ψάρια που πετάχτηκαν")
    kpi3.metric("Παράπονα Πελατών", "0", delta_color="normal")
    
    st.markdown("---")
    
    col_qc1, col_qc2 = st.columns(2)
    
    with col_qc1:
        st.subheader("🎯 Έλεγχος Glazing (Επί Πάγου)")
        # Scatter plot για να δούμε τις αποκλίσεις
        fig_glaz = px.scatter(df, x='Date', y='Glazing_Pct', color='Supplier', size='Output_Kg',
                              title="Διασπορά Glazing ανά Παρτίδα")
        # Περιοχή Ασφαλείας (14% - 16%)
        fig_glaz.add_hrect(y0=14, y1=16, line_width=0, fillcolor="green", opacity=0.1, annotation_text="Ζώνη Ασφαλείας")
        st.plotly_chart(fig_glaz, use_container_width=True)
        
    with col_qc2:
        st.subheader("⚠️ Quality Alerts")
        # Εντοπισμός προβλημάτων
        problems = df[(df['Yield_Pct'] < 70) | (df['Glazing_Pct'] > 16) | (df['Glazing_Pct'] < 14)]
        
        if not problems.empty:
            st.error(f"Εντοπίστηκαν {len(problems)} προβληματικές παρτίδες!")
            st.dataframe(problems[['Date', 'Lot_ID', 'Supplier', 'Yield_Pct', 'Glazing_Pct']].style.format({'Yield_Pct': '{:.1f}%', 'Glazing_Pct': '{:.1f}%'}))
        else:
            st.success("✅ Όλες οι πρόσφατες παρτίδες είναι εντός προδιαγραφών.")

# === VIEW C: ΚΑΤΑΧΩΡΗΣΗ ===
elif menu == "📝 Καταχώρηση Παρτίδας":
    st.markdown("<div class='section-title'>📝 Δημιουργία Νέας Παρτίδας</div>", unsafe_allow_html=True)
    
    # Χρήση Tabs για να σπάσουμε τη διαδικασία σε βήματα (Wizard Style)
    tab1, tab2, tab3 = st.tabs(["1️⃣ Παραλαβή & Α' Ύλη", "2️⃣ Παραγωγή", "3️⃣ Ποιοτικός Έλεγχος (QC)"])
    
    with st.form("new_batch"):
        # ΒΗΜΑ 1
        with tab1:
            c1, c2 = st.columns(2)
            supplier = c1.selectbox("Προμηθευτής", ["Aegean Fish", "Northen Catch", "Blue Sea Ltd", "Άλλος"])
            raw_kg = c2.number_input("Κιλά Εισόδου (Raw)", min_value=0.0, step=10.0)
            lot_suffix = st.text_input("Κωδικός Ιχνηλασιμότητας (Προαιρετικό)", placeholder="π.χ. Τιμολόγιο 123")
        
        # ΒΗΜΑ 2
        with tab2:
            st.info("Στοιχεία Γραμμής Παραγωγής")
            c1, c2, c3 = st.columns(3)
            clean_kg = c1.number_input("Κιλά Καθαρό (Πριν το Glazing)", min_value=0.0)
            workers = c2.number_input("Αρ. Εργαζομένων", value=5)
            hours = c3.number_input("Ώρες Λειτουργίας", value=7.0)
            
        # ΒΗΜΑ 3
        with tab3:
            st.warning("Στοιχεία Εργαστηρίου")
            measured_glazing = st.slider("Μετρημένο Glazing (%)", 0, 30, 15)
            temp_core = st.number_input("Θερμοκρασία Πυρήνα (°C)", value=-18.0)
            quality_check = st.checkbox("✅ Οπτικός Έλεγχος & Έλεγχος Παρασίτων (OK)")
            
        submit = st.form_submit_button("💾 Οριστικοποίηση & Αποθήκευση")
        
        if submit:
            if raw_kg > 0 and clean_kg > 0:
                # Υπολογισμοί
                yield_cal = (clean_kg / raw_kg) * 100
                st.success("Η Παρτίδα αποθηκεύτηκε επιτυχώς!")
                
                # Άμεσο Feedback
                res_col1, res_col2 = st.columns(2)
                res_col1.metric("Απόδοση Παρτίδας", f"{yield_cal:.1f}%")
                
                if yield_cal < 70:
                    res_col2.error("⚠️ Χαμηλή Απόδοση! Ενημερώστε τον Διευθυντή.")
                else:
                    res_col2.success("✅ Απόδοση εντός στόχων.")
            else:
                st.error("Παρακαλώ συμπληρώστε τα κιλά εισόδου/εξόδου.")

# === VIEW D: ΙΣΤΟΡΙΚΟ ===
elif menu == "🗄️ Ιστορικό Παραγωγής":
    st.markdown("<div class='section-title'>🗄️ Αρχείο Δεδομένων</div>", unsafe_allow_html=True)
    
    # Filters
    col_fil1, col_fil2 = st.columns(2)
    filter_supp = col_fil1.multiselect("Φίλτρο Προμηθευτή", df['Supplier'].unique())
    
    # Filter Logic
    df_show = df if not filter_supp else df[df['Supplier'].isin(filter_supp)]
    
    st.dataframe(
        df_show.style.format({
            "Yield_Pct": "{:.1f}%", 
            "Glazing_Pct": "{:.1f}%",
            "Cost_Per_Kg": "{:.2f}€",
            "Date": "{:%d-%m-%Y}"
        }).background_gradient(subset=['Yield_Pct'], cmap='RdYlGn', vmin=65, vmax=75),
        use_container_width=True
    )
    
    st.download_button("📥 Εξαγωγή σε Excel", df_show.to_csv().encode('utf-8'), "production_data.csv")
