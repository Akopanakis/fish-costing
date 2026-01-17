import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# --- ΡΥΘΜΙΣΕΙΣ UI ---
st.set_page_config(page_title="Fish Factory OS", layout="wide", page_icon="🏭")

# --- CSS ΓΙΑ "ΔΙΕΥΘΥΝΤΙΚΟ" LOOK ---
st.markdown("""
<style>
    .metric-card {background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #1f77b4;}
    .alert-card {background-color: #ffcccc; padding: 10px; border-radius: 5px; color: #990000; font-weight: bold;}
    .success-card {background-color: #ccffcc; padding: 10px; border-radius: 5px; color: #006600; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# --- ΔΕΔΟΜΕΝΑ (ΨΕΥΤΙΚΗ ΒΑΣΗ ΓΙΑ ΤΟ DEMO) ---
# Εδώ δημιουργούμε ένα ιστορικό παραγωγής για να έχεις κάτι να βλέπεις
if 'data' not in st.session_state:
    data = {
        'Date': pd.date_range(start='2023-10-01', periods=10),
        'Lot_ID': [f'LOT-2310{i}' for i in range(10)],
        'Supplier': ['Καΐκι "Αγ. Νικόλαος"', 'Ixthioculture SA', 'Καΐκι "Αγ. Νικόλαος"', 'Import Co', 'Ixthioculture SA']*2,
        'Input_Kg': [500, 600, 450, 800, 550, 520, 610, 440, 790, 560],
        'Output_Kg': [350, 430, 310, 550, 390, 360, 440, 305, 545, 400], # Καθαρό
        'Workers': [5, 6, 5, 8, 5, 5, 6, 5, 8, 5],
        'Hours': [7, 8, 6.5, 9, 7.5, 7, 8, 6, 9, 7.5],
        'Glazing_Pct': [14, 15, 12, 16, 15, 14, 15, 13, 15, 15] # Πραγματικό Glazing
    }
    st.session_state['data'] = pd.DataFrame(data)

df = st.session_state['data']

# --- SIDEBAR: ΡΥΘΜΙΣΕΙΣ & ΡΟΛΟΙ ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=80)
st.sidebar.title("Factory Control")

# Role Switcher (Το ζήτησες!)
user_role = st.sidebar.radio("👁️ Προβολή ως:", ["General Manager", "Production Foreman"])

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Παράμετροι Αγοράς")
market_price = st.sidebar.number_input("Τιμή Αγοράς (€/kg)", 2.30)
sell_price = st.sidebar.number_input("Τιμή Πώλησης (€/kg)", 4.80)
wage_hour = st.sidebar.number_input("Ωρομίσθιο (με ΙΚΑ)", 8.00)

# Navigation
page = st.sidebar.selectbox("Μενού", ["📊 Dashboard Διευθυντή", "🏭 Νέα Παραγωγή (Actual)", "📉 Ανάλυση Προμηθευτών"])

# --- ΥΠΟΛΟΓΙΣΜΟΙ KPI (Real-time) ---
df['Yield'] = (df['Output_Kg'] / df['Input_Kg']) * 100
df['Total_Labor_Cost'] = df['Workers'] * df['Hours'] * wage_hour
# Κόστος ανά κιλό ΤΕΛΙΚΟΥ προϊόντος (με το Glazing που μπήκε πραγματικά)
df['Final_Kg_Produced'] = df['Output_Kg'] * (1 / (1 - (df['Glazing_Pct']/100)))
df['Cost_Per_Kg'] = ( (df['Input_Kg'] * market_price) + df['Total_Labor_Cost'] + (df['Final_Kg_Produced'] * 0.43) ) / df['Final_Kg_Produced']
# (0.43 είναι συσκευασία+ενέργεια standard)

# =======================================================
# PAGE 1: DASHBOARD ΔΙΕΥΘΥΝΤΗ
# =======================================================
if page == "📊 Dashboard Διευθυντή":
    st.title("📊 Executive Dashboard")
    st.caption(f"Επισκόπηση Παραγωγής | Ρόλος: {user_role}")

    # Top Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    avg_yield = df['Yield'].mean()
    avg_glazing = df['Glazing_Pct'].mean()
    avg_cost = df['Cost_Per_Kg'].mean()
    last_run_date = df['Date'].max().strftime('%d/%m')

    col1.metric("Μέση Απόδοση (Yield)", f"{avg_yield:.1f}%", delta=f"{avg_yield-71.2:.1f}% vs Target")
    col2.metric("Μέσο Glazing", f"{avg_glazing:.1f}%", delta=f"{avg_glazing-15:.1f}% vs Target")
    
    if user_role == "General Manager":
        col3.metric("Μέσο Κόστος", f"{avg_cost:.2f} €/kg", delta=f"{(sell_price - avg_cost):.2f} € Margin", delta_color="inverse")
    else:
        col3.metric("Μέσο Κόστος", "🔒 HIDDEN", "Access Denied")
        
    col4.metric("Τελευταία Παραγωγή", last_run_date)

    # ALERTS SECTION (Αυτό που ήθελες για να μην έχεις εκπλήξεις)
    st.subheader("🚨 Active Alerts")
    
    c1, c2 = st.columns(2)
    # Yield Alert
    low_yield_runs = df[df['Yield'] < 28]
    if not low_yield_runs.empty:
        c1.error(f"⚠️ ΠΡΟΣΟΧΗ: {len(low_yield_runs)} παρτίδες είχαν φύρα κάτω από το όριο (28%)! Ελέγξτε τους προμηθευτές.")
    else:
        c1.success("✅ Όλες οι παρτίδες έχουν αποδεκτή απόδοση.")
        
    # Glazing Alert
    bad_glazing = df[(df['Glazing_Pct'] < 13) | (df['Glazing_Pct'] > 17)]
    if not bad_glazing.empty:
        c2.warning(f"⚠️ ΠΡΟΣΟΧΗ: {len(bad_glazing)} παρτίδες έχουν απόκλιση στο Glazing (>2%). Κίνδυνος ποιότητας.")
    else:
        c2.success("✅ Το Glazing είναι εντός ορίων.")

    # GRAPHS
    st.markdown("---")
    c_chart1, c_chart2 = st.columns(2)
    
    with c_chart1:
        st.subheader("📉 Τάση Κόστους vs Τιμή Πώλησης")
        if user_role == "General Manager":
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['Date'], y=df['Cost_Per_Kg'], name='Πραγματικό Κόστος', line=dict(color='red')))
            fig.add_trace(go.Scatter(x=df['Date'], y=[sell_price]*len(df), name='Τιμή Πώλησης', line=dict(color='green', dash='dash')))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Δεν έχετε δικαίωμα προβολής οικονομικών στοιχείων.")

    with c_chart2:
        st.subheader("⚖️ Απόδοση (Yield) ανά Παρτίδα")
        fig2 = px.bar(df, x='Lot_ID', y='Yield', color='Supplier', title="Ποια παρτίδα πήγε καλά;")
        # Προσθήκη γραμμής στόχου
        fig2.add_hline(y=71.2, line_dash="dot", annotation_text="Target Yield", annotation_position="bottom right")
        st.plotly_chart(fig2, use_container_width=True)

# =======================================================
# PAGE 2: ΚΑΤΑΧΩΡΗΣΗ ΠΑΡΑΓΩΓΗΣ (ACTUAL)
# =======================================================
elif page == "🏭 Νέα Παραγωγή (Actual)":
    st.title("📝 Ημερήσιο Δελτίο Παραγωγής")
    
    # Lot Number Generator
    today_str = datetime.now().strftime("%y%m%d")
    lot_suffix = st.sidebar.text_input("Lot Suffix", "A")
    auto_lot = f"LOT-{today_str}-{lot_suffix}"
    
    with st.form("production_form"):
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"🆔 New Batch ID: **{auto_lot}**")
            supplier = st.selectbox("Προμηθευτής", ["Καΐκι 'Αγ. Νικόλαος'", "Ixthioculture SA", "Import Co", "Άλλος"])
            input_w = st.number_input("⚖️ Κιλά Εισόδου (Ακατέργαστο)", min_value=0.0)
            output_w = st.number_input("🐟 Κιλά Εξόδου (Καθαρό Κρέας)", min_value=0.0)
        
        with col2:
            st.write("### 👥 Εργατικά & Ποιότητα")
            staff_num = st.number_input("Αριθμός Ατόμων", min_value=1, value=5)
            hours_worked = st.number_input("Ώρες Εργασίας", min_value=0.5, value=7.0)
            ice_pct = st.slider("❄️ Μετρημένο Glazing (%)", 0, 30, 15)
        
        submitted = st.form_submit_button("💾 Καταχώρηση Παραγωγής")
        
        if submitted and input_w > 0:
            # Υπολογισμοί "on the fly"
            actual_yield = (output_w / input_w) * 100
            target_yield = 71.2 # Στόχος
            
            st.success("Η παραγωγή καταχωρήθηκε!")
            
            # FEEDBACK ΣΤΟΝ ΔΙΕΥΘΥΝΤΗ
            st.markdown("### 🔎 Ανάλυση Παρτίδας")
            c1, c2, c3 = st.columns(3)
            
            c1.metric("Πραγματική Φύρα", f"{100-actual_yield:.1f}%", delta=f"{(100-actual_yield) - 28.8:.1f}%")
            
            # Υπολογισμός Κόστους για αυτή την παρτίδα
            final_kg = output_w * (1 / (1 - (ice_pct/100)))
            labor_cost = staff_num * hours_worked * wage_hour
            this_cost = ((input_w * market_price) + labor_cost + (final_kg * 0.43)) / final_kg
            
            if user_role == "General Manager":
                c2.metric("Τελικό Κόστος Παρτίδας", f"{this_cost:.2f} €/kg")
                if this_cost > sell_price:
                    st.error(f"⛔ ΖΗΜΙΑ! Αυτή η παρτίδα κόστισε {this_cost:.2f}€ ενώ πουλάμε {sell_price}€.")
                else:
                    st.balloons()
                    st.success(f"✅ ΚΕΡΔΟΣ: {sell_price - this_cost:.2f}€ ανά κιλό.")
            else:
                c2.info("Cost Data Hidden")

# =======================================================
# PAGE 3: ΑΝΑΛΥΣΗ ΠΡΟΜΗΘΕΥΤΩΝ
# =======================================================
elif page == "📉 Ανάλυση Προμηθευτών":
    st.title("🤝 Αξιολόγηση Προμηθευτών")
    st.write("Ποιος μας δίνει το καλύτερο ψάρι;")
    
    # Group by Supplier
    supplier_stats = df.groupby('Supplier').agg({
        'Yield': 'mean',
        'Input_Kg': 'sum',
        'Cost_Per_Kg': 'mean'
    }).reset_index()
    
    # Chart
    fig = px.scatter(supplier_stats, x='Yield', y='Cost_Per_Kg', size='Input_Kg', color='Supplier',
                     title="Σχέση Απόδοσης vs Κόστους (Το μέγεθος κύκλου είναι η ποσότητα)",
                     labels={'Yield': 'Μέση Απόδοση (%)', 'Cost_Per_Kg': 'Μέσο Κόστος (€)'})
    
    # Γραμμές Στόχων
    fig.add_vline(x=71.2, line_dash="dash", line_color="green", annotation_text="Target Yield")
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.info("""
    **Πώς να διαβάσεις αυτό το γράφημα:**
    * **Κάτω Δεξιά = Ο Ιδανικός Προμηθευτής** (Υψηλή Απόδοση, Χαμηλό Κόστος).
    * **Πάνω Αριστερά = Προς Διαγραφή** (Χαμηλή Απόδοση, Ακριβό Κόστος).
    """)
    
    st.dataframe(supplier_stats.style.highlight_max(axis=0, color='lightgreen'))
