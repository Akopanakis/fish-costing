import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import uuid
import numpy as np

# ---------------------------------------------------------
# 1. ΡΥΘΜΙΣΕΙΣ & CSS (DESIGN)
# ---------------------------------------------------------
st.set_page_config(page_title="FishFactory ERP", layout="wide", page_icon="🏭")

# Custom CSS για διαχωρισμό ρόλων και επαγγελματικό look
st.markdown("""
<style>
    /* Headers */
    .role-header {padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 20px;}
    .operator-mode {background-color: #E8F8F5; color: #148F77; border: 1px solid #148F77;}
    .director-mode {background-color: #F4ECF7; color: #884EA0; border: 1px solid #884EA0;}
    
    /* Metrics */
    .metric-box {padding: 15px; border-radius: 8px; background-color: #f9f9f9; border-left: 5px solid #333;}
    
    /* Simulator Results */
    .sim-profit {background-color: #d4edda; color: #155724; padding: 20px; border-radius: 10px; text-align: center; font-size: 24px; font-weight: bold;}
    .sim-loss {background-color: #f8d7da; color: #721c24; padding: 20px; border-radius: 10px; text-align: center; font-size: 24px; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. STATE MANAGEMENT (Η ΜΝΗΜΗ ΤΗΣ ΕΦΑΡΜΟΓΗΣ)
# ---------------------------------------------------------

# A. Default SKUs (Οι συνταγές σου)
DEFAULT_SKUS = {
    "SKU-001": {"name": "🐟 Γαύρος Ακέφαλος 3kg (Φελιζόλ)", "weight": 3.0, "pack_cost": 0.20, "desc": "Φελιζόλ"},
    "SKU-002": {"name": "📦 Γαύρος Ακέφαλος 10kg (Κιβώτιο)", "weight": 10.0, "pack_cost": 0.60, "desc": "Χαρτοκιβώτιο + 2 Σακούλες"},
    "SKU-003": {"name": "🥡 Σαρδέλα IQF 1kg (Σακούλα)", "weight": 1.0, "pack_cost": 0.08, "desc": "Σακούλα Λιανικής"},
}

# B. Initialization
if 'inventory' not in st.session_state:
    # Δημιουργία μερικών δεδομένων για να μην είναι άδειο (Demo Data)
    st.session_state['inventory'] = pd.DataFrame([
        {'Lot_ID': 'LOT-DEMO-01', 'Date': datetime.now()-timedelta(days=2), 'Supplier': 'Voulgaris Fishing', 'Product_Type': 'Γαύρος', 'Initial_Kg': 2000.0, 'Remaining_Kg': 800.0, 'Buy_Price': 2.30, 'Status': 'Active'},
        {'Lot_ID': 'LOT-DEMO-02', 'Date': datetime.now()-timedelta(days=1), 'Supplier': 'Aegean Catch', 'Product_Type': 'Σαρδέλα', 'Initial_Kg': 1000.0, 'Remaining_Kg': 1000.0, 'Buy_Price': 1.80, 'Status': 'Active'}
    ])

if 'production_log' not in st.session_state:
    st.session_state['production_log'] = pd.DataFrame(columns=[
        'Prod_ID', 'Date', 'Source_Lot', 'Supplier', 'SKU_Name', 'Input_Kg', 'Output_Units', 
        'Total_Output_Kg', 'Yield_Pct', 'Total_Cost_Kg', 'Labor_Cost', 'Pack_Cost'
    ])

if 'products_db' not in st.session_state:
    st.session_state['products_db'] = DEFAULT_SKUS

if 'director_settings' not in st.session_state:
    st.session_state['director_settings'] = {'overhead_per_kg': 0.40, 'min_margin_pct': 15}

# ---------------------------------------------------------
# 3. SIDEBAR (ΤΟ ΤΙΜΟΝΙ)
# ---------------------------------------------------------
with st.sidebar:
    st.title("🏭 FishFactory ERP")
    
    # ROLE SWITCHER
    st.write("---")
    role = st.radio("Επιλογή Ρόλου:", ["👤 Operator", "👔 Director"])
    st.write("---")
    
    if role == "👤 Operator":
        menu = st.radio("Μενού Λειτουργίας:", ["📦 Αποθήκη (Παραλαβές)", "⚙️ Παραγωγή (Daily Log)", "🛠️ Διαχείριση Κωδικών"])
        st.info("Εισαγωγή Δεδομένων & Παραγωγή")
    else:
        menu = st.radio("Μενού Διοίκησης:", ["📊 Dashboard & Analytics", "🤝 Deal Simulator", "🏆 Αξιολόγηση Προμηθευτών", "⚙️ Ρυθμίσεις Κοστολόγησης"])
        st.success("Ανάλυση, Τιμολόγηση & Στρατηγική")

# ---------------------------------------------------------
# ΚΟΣΜΟΣ 1: OPERATOR (DATA ENTRY)
# ---------------------------------------------------------
if role == "👤 Operator":
    st.markdown("<div class='role-header operator-mode'>OPERATOR MODE: Καταχώρηση Δεδομένων</div>", unsafe_allow_html=True)
    
    # --- VIEW: ΑΠΟΘΗΚΗ ---
    if menu == "📦 Αποθήκη (Παραλαβές)":
        st.subheader("📦 Διαχείριση Α' Υλών")
        tab1, tab2 = st.tabs(["➕ Νέα Παραλαβή", "📋 Τρέχον Στοκ"])
        
        with tab1:
            with st.form("receipt"):
                c1, c2 = st.columns(2)
                supplier = c1.text_input("Προμηθευτής")
                product = c2.selectbox("Είδος", ["Γαύρος", "Σαρδέλα", "Κολιός", "Άλλο"])
                c3, c4 = st.columns(2)
                kg = c3.number_input("Κιλά", 1000.0, step=100.0)
                price = c4.number_input("Τιμή Αγοράς (€/kg)", 2.0, step=0.1)
                
                if st.form_submit_button("📥 Αποθήκευση"):
                    lot_id = f"LOT-{datetime.now().strftime('%y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
                    new_inv = {'Lot_ID': lot_id, 'Date': datetime.now(), 'Supplier': supplier, 'Product_Type': product, 'Initial_Kg': kg, 'Remaining_Kg': kg, 'Buy_Price': price, 'Status': 'Active'}
                    st.session_state['inventory'] = pd.concat([st.session_state['inventory'], pd.DataFrame([new_inv])], ignore_index=True)
                    st.success(f"Παραλαβή {lot_id} OK!")
        
        with tab2:
            df_i = st.session_state['inventory']
            active = df_i[df_i['Remaining_Kg']>0]
            st.dataframe(active[['Lot_ID', 'Product_Type', 'Remaining_Kg', 'Initial_Kg', 'Buy_Price', 'Supplier']], use_container_width=True)

    # --- VIEW: ΠΑΡΑΓΩΓΗ ---
    elif menu == "⚙️ Παραγωγή (Daily Log)":
        st.subheader("⚙️ Ημερήσιο Δελτίο Παραγωγής")
        
        df_inv = st.session_state['inventory']
        active_lots = df_inv[df_inv['Remaining_Kg'] > 0]['Lot_ID'].tolist()
        
        if not active_lots:
            st.error("Δεν υπάρχει στοκ! Πηγαίνετε στην Αποθήκη.")
        else:
            c_lot, c_sku = st.columns(2)
            sel_lot = c_lot.selectbox("1. Παρτίδα (Πηγή)", active_lots)
            lot_data = df_inv[df_inv['Lot_ID'] == sel_lot].iloc[0]
            
            products = st.session_state['products_db']
            sel_sku_key = c_sku.selectbox("2. Προϊόν (SKU)", list(products.keys()), format_func=lambda x: products[x]['name'])
            sku_data = products[sel_sku_key]
            
            st.info(f"ℹ️ Επιλέξατε: **{sku_data['name']}**. Κόστος Συσκευασίας: **{sku_data['pack_cost']}€**")
            
            with st.form("prod_run"):
                c1, c2 = st.columns(2)
                input_kg = c1.number_input("⚖️ Input (kg Ακατέργαστου)", min_value=0.0, max_value=float(lot_data['Remaining_Kg']))
                output_units = c2.number_input(f"📦 Τεμάχια ({sku_data['weight']}kg)", min_value=0)
                
                # Expanders για λεπτομέρειες
                with st.expander("🛠️ Εργατικά & Λεπτομέρειες (Προαιρετικά)"):
                    ce1, ce2 = st.columns(2)
                    workers = ce1.number_input("Εργάτες", 5)
                    hours = ce2.number_input("Ώρες", 7.0)
                
                if st.form_submit_button("✅ Καταχώρηση Παραγωγής"):
                    if input_kg > 0 and output_units > 0:
                        # Calculations
                        total_out = output_units * sku_data['weight']
                        yield_pct = (total_out / input_kg) * 100 # Απλοποιημένη απόδοση για το παράδειγμα
                        
                        raw_cost = input_kg * lot_data['Buy_Price']
                        labor_cost = workers * hours * 8.0 # 8€/ώρα default
                        pack_cost = output_units * sku_data['pack_cost']
                        total_cost = raw_cost + labor_cost + pack_cost
                        cost_per_kg = total_cost / total_out
                        
                        # Save Log
                        new_log = {
                            'Prod_ID': str(uuid.uuid4())[:6], 'Date': datetime.now(),
                            'Source_Lot': sel_lot, 'Supplier': lot_data['Supplier'], 'SKU_Name': sku_data['name'],
                            'Input_Kg': input_kg, 'Output_Units': output_units, 'Total_Output_Kg': total_out,
                            'Yield_Pct': yield_pct, 'Total_Cost_Kg': cost_per_kg,
                            'Labor_Cost': labor_cost, 'Pack_Cost': pack_cost
                        }
                        st.session_state['production_log'] = pd.concat([st.session_state['production_log'], pd.DataFrame([new_log])], ignore_index=True)
                        
                        # Reduce Stock
                        idx = df_inv.index[df_inv['Lot_ID'] == sel_lot][0]
                        st.session_state['inventory'].at[idx, 'Remaining_Kg'] -= input_kg
                        
                        st.success(f"Παραγωγή ΟΚ! Κόστος: {cost_per_kg:.2f}€/kg")

    # --- VIEW: SKU MANAGER ---
    elif menu == "🛠️ Διαχείριση Κωδικών":
        st.subheader("🛠️ Product Recipes (SKUs)")
        
        with st.form("new_sku"):
            st.write("Προσθήκη Νέου Κωδικού")
            c1, c2, c3 = st.columns(3)
            n_name = c1.text_input("Όνομα", "π.χ. Γαύρος Φιλέτο")
            n_w = c2.number_input("Βάρος (kg)", 1.0)
            n_c = c3.number_input("Κόστος Υλικών (€)", 0.50)
            if st.form_submit_button("Προσθήκη"):
                sid = f"SKU-{len(st.session_state['products_db'])+1:03d}"
                st.session_state['products_db'][sid] = {"name": n_name, "weight": n_w, "pack_cost": n_c, "desc": "Custom"}
                st.success("Προστέθηκε!")
                st.rerun()
        
        # Λίστα
        st.write("Υπάρχοντες Κωδικοί:")
        st.json(st.session_state['products_db'])

# ---------------------------------------------------------
# ΚΟΣΜΟΣ 2: DIRECTOR (DECISION MAKING)
# ---------------------------------------------------------
else:
    st.markdown("<div class='role-header director-mode'>DIRECTOR MODE: Στρατηγική & Αποφάσεις</div>", unsafe_allow_html=True)
    
    # Settings (Hidden power)
    overhead = st.session_state['director_settings']['overhead_per_kg']
    
    # --- VIEW: DASHBOARD ---
    if menu == "📊 Dashboard & Analytics":
        st.subheader("📊 Factory Overview")
        df_log = st.session_state['production_log']
        
        if df_log.empty:
            st.info("Δεν υπάρχουν δεδομένα παραγωγής ακόμα.")
        else:
            # KPIS
            avg_cost_prod = df_log['Total_Cost_Kg'].mean()
            real_avg_cost = avg_cost_prod + overhead
            
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Production Volume", f"{df_log['Total_Output_Kg'].sum():,.0f} kg")
            k2.metric("Factory Cost", f"{avg_cost_prod:.2f} €/kg", help="Κόστος Ψάρι + Εργατικά + Υλικά")
            k3.metric("REAL Cost (w/ Overheads)", f"{real_avg_cost:.2f} €/kg", delta=f"+{overhead}€ overhead", delta_color="inverse", help="Συμπεριλαμβάνει τα γενικά έξοδα γραφείου/ενοίκια")
            k4.metric("Avg Yield", f"{df_log['Yield_Pct'].mean():.1f}%")
            
            st.markdown("---")
            
            # CHART
            st.subheader("📉 Ανάλυση Κόστους ανά Παραγωγή")
            # Δημιουργία γραφήματος που δείχνει το "αόρατο" overhead
            df_log['Overhead_Cost'] = overhead
            df_log['Raw_Material_Only'] = df_log['Total_Cost_Kg'] - (df_log['Labor_Cost']/df_log['Total_Output_Kg']) - (df_log['Pack_Cost']/df_log['Total_Output_Kg'])
            
            # Stacked Bar Chart
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df_log['Date'], y=df_log['Raw_Material_Only'], name='Α\' Ύλη'))
            fig.add_trace(go.Bar(x=df_log['Date'], y=df_log['Labor_Cost']/df_log['Total_Output_Kg'], name='Εργατικά'))
            fig.add_trace(go.Bar(x=df_log['Date'], y=df_log['Pack_Cost']/df_log['Total_Output_Kg'], name='Συσκευασία'))
            fig.add_trace(go.Bar(x=df_log['Date'], y=df_log['Overhead_Cost'], name='Overheads (Γραφείο)', marker_color='gray'))
            
            fig.update_layout(barmode='stack', title='Σύνθεση Πραγματικού Κόστους (€/kg)')
            st.plotly_chart(fig, use_container_width=True)

    # --- VIEW: DEAL SIMULATOR (TO ΚΛΕΙΔΙ) ---
    elif menu == "🤝 Deal Simulator":
        st.subheader("🤝 Προσομοιωτής Εμπορικής Συμφωνίας")
        st.info("Χρησιμοποιήστε αυτό το εργαλείο όταν μιλάτε με πελάτη για να δείτε αν συμφέρει η προσφορά.")
        
        # 1. Inputs
        col_in, col_res = st.columns([1, 1])
        
        with col_in:
            st.markdown("#### Παράμετροι Συμφωνίας")
            
            # Επιλογή προϊόντος για να πάρουμε το κόστος βάσης
            df_log = st.session_state['production_log']
            if not df_log.empty:
                base_cost = df_log['Total_Cost_Kg'].mean() # Παίρνουμε τον μέσο όρο ιστορικού
            else:
                base_cost = 3.80 # Default αν δεν έχει δεδομένα
                
            qty_tons = st.slider("Ποσότητα (Τόνοι)", 1, 50, 10)
            price_offer = st.number_input("Τιμή Πώλησης (€/kg)", value=4.50, step=0.05)
            payment_terms = st.selectbox("Πληρωμή", ["Μετρητοίς (0%)", "30 Ημέρες (1%)", "60 Ημέρες (2%)", "90 Ημέρες (3%)"])
            
            # Υπολογισμός Κόστους Χρήματος
            finance_cost_pct = int(payment_terms.split('(')[1].replace('%)','')) / 100
            finance_cost_abs = price_offer * finance_cost_pct
        
        # 2. Logic
        real_cost_basis = base_cost + overhead
        total_revenue = qty_tons * 1000 * price_offer
        total_cost_goods = qty_tons * 1000 * real_cost_basis
        total_finance_cost = total_revenue * finance_cost_pct
        
        net_profit = total_revenue - total_cost_goods - total_finance_cost
        profit_margin = (net_profit / total_revenue) * 100
        
        # 3. Results (Visual)
        with col_res:
            st.markdown("#### Αποτέλεσμα")
            st.write(f"Σενάριο: {qty_tons} τόνοι @ {price_offer}€")
            
            if net_profit > 0:
                st.markdown(f"<div class='sim-profit'>ΚΕΡΔΟΣ<br>+{net_profit:,.0f} €</div>", unsafe_allow_html=True)
                st.balloons()
            else:
                st.markdown(f"<div class='sim-loss'>ΖΗΜΙΑ<br>{net_profit:,.0f} €</div>", unsafe_allow_html=True)
            
            st.write("---")
            st.write("**Ανάλυση ανά Κιλό:**")
            st.text(f"Τιμή Πώλησης:      {price_offer:.2f} €")
            st.text(f"- Κόστος Παραγωγής: {base_cost:.2f} €")
            st.text(f"- Overheads:        {overhead:.2f} €")
            st.text(f"- Χρηματοοικονομικά:{finance_cost_abs:.2f} €")
            st.markdown(f"**= Καθαρό: {price_offer - real_cost_basis - finance_cost_abs:.2f} € ({profit_margin:.1f}%)**")

    # --- VIEW: SUPPLIER INTELLIGENCE ---
    elif menu == "🏆 Αξιολόγηση Προμηθευτών":
        st.subheader("🏆 Ποιος προμηθευτής είναι ο καλύτερος;")
        df_log = st.session_state['production_log']
        
        if not df_log.empty:
            # Group by Supplier
            supp_stats = df_log.groupby('Supplier').agg({
                'Yield_Pct': 'mean',
                'Total_Cost_Kg': 'mean',
                'Total_Output_Kg': 'sum'
            }).reset_index()
            
            fig = px.scatter(supp_stats, x='Yield_Pct', y='Total_Cost_Kg', size='Total_Output_Kg', color='Supplier',
                             title="Απόδοση vs Κόστους (Το μέγεθος είναι η ποσότητα)",
                             labels={'Yield_Pct': 'Μέση Απόδοση (%)', 'Total_Cost_Kg': 'Κόστος Παραγωγής (€/kg)'})
            
            st.plotly_chart(fig, use_container_width=True)
            st.caption("💡 Στόχος: Θέλουμε τους προμηθευτές να είναι **Κάτω Δεξιά** (Χαμηλό Κόστος, Υψηλή Απόδοση).")
        else:
            st.info("Χρειάζονται δεδομένα παραγωγής για αυτό το γράφημα.")

    # --- VIEW: SETTINGS ---
    elif menu == "⚙️ Ρυθμίσεις Κοστολόγησης":
        st.subheader("⚙️ Παράμετροι Διοίκησης")
        st.warning("Προσοχή: Αυτές οι αλλαγές επηρεάζουν όλους τους υπολογισμούς κερδοφορίας.")
        
        new_ov = st.number_input("Γενικά Βιομηχανικά Έξοδα (Overhead) ανά Kg", value=0.40, step=0.01, help="Ενοίκια, Ρεύμα, Διοίκηση διαιρεμένα με τους τόνους παραγωγής")
        st.session_state['director_settings']['overhead_per_kg'] = new_ov
        st.success(f"Το 'Αόρατο Κόστος' ορίστηκε στα {new_ov}€/kg.")
