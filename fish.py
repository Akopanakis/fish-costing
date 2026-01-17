import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import uuid

# ---------------------------------------------------------
# 1. ΡΥΘΜΙΣΕΙΣ & PRODUCT DATA (ΣΥΝΤΑΓΕΣ)
# ---------------------------------------------------------
st.set_page_config(page_title="FishPro ERP", layout="wide", page_icon="🏭")

# CSS για επαγγελματική εμφάνιση
st.markdown("""
<style>
    .big-font {font-size:18px !important; font-weight: bold;}
    .success-box {padding:10px; border-radius:5px; background-color:#d4edda; color:#155724;}
    .warning-box {padding:10px; border-radius:5px; background-color:#fff3cd; color:#856404;}
    .stExpander {border: 1px solid #ddd; border-radius: 5px;}
</style>
""", unsafe_allow_html=True)

# ΒΑΣΗ ΔΕΔΟΜΕΝΩΝ ΠΡΟΪΟΝΤΩΝ (SKUs)
# Εδώ ορίζουμε τα κόστη συσκευασίας που μου έδωσες
# Σακούλα: 1.5€ / 30τμχ = 0.05€ ανά σακούλα
PRODUCTS_DB = {
    "CUSTOM": {
        "name": "---- Χειροκίνητη Επιλογή ----",
        "weight": 1, 
        "pack_cost": 0.0
    },
    "GAV-3KG-STY": {
        "name": "🐟 Γαύρος Ακέφαλος - 3kg Φελιζόλ",
        "weight": 3.0,
        "pack_cost": 0.20, # 0.20€ το τεμάχιο φελιζόλ
        "desc": "Συσκευασία: Φελιζόλ (0,20€)"
    },
    "GAV-10KG-BOX": {
        "name": "📦 Γαύρος Ακέφαλος - 10kg Κιβώτιο (2x5kg)",
        "weight": 10.0,
        "pack_cost": 0.60, # 0.50€ Κιβώτιο + (2 * 0.05€ Σακούλες)
        "desc": "Συσκευασία: Χαρτοκιβώτιο (0,50€) + 2 Σακούλες (0,10€)"
    }
}

# ---------------------------------------------------------
# 2. INITIALIZATION (STATE)
# ---------------------------------------------------------
# Αποθήκη (Παρτίδες που παραλάβαμε)
if 'inventory' not in st.session_state:
    st.session_state['inventory'] = pd.DataFrame(columns=[
        'Lot_ID', 'Date', 'Supplier', 'Product_Type', 'Initial_Kg', 'Remaining_Kg', 'Buy_Price', 'Status'
    ])

# Ιστορικό Παραγωγής
if 'production_log' not in st.session_state:
    st.session_state['production_log'] = pd.DataFrame(columns=[
        'Prod_ID', 'Date', 'Source_Lot', 'SKU', 'Input_Kg', 'Output_Units', 'Total_Output_Kg',
        'Yield_Pct', 'Glazing_Sold', 'Glazing_Actual', 'Labor_Cost', 'Pack_Cost', 'Total_Cost_Kg'
    ])

# ---------------------------------------------------------
# 3. SIDEBAR MENU
# ---------------------------------------------------------
with st.sidebar:
    st.title("🏭 FishFactory OS")
    st.caption("Frozen Food Management")
    st.markdown("---")
    
    menu = st.radio("Μενού:", [
        "📦 Αποθήκη & Παραλαβές", 
        "⚙️ Καταχώρηση Παραγωγής", 
        "📊 Αναφορές & Κοστολόγηση"
    ])
    st.markdown("---")
    st.info("💡 Tip: Τα εργατικά και η συσκευασία είναι πλέον προαιρετικά.")

# ---------------------------------------------------------
# VIEW 1: ΑΠΟΘΗΚΗ (INVENTORY)
# ---------------------------------------------------------
if menu == "📦 Αποθήκη & Παραλαβές":
    st.header("📦 Διαχείριση Αποθήκης (Α' Ύλες)")
    
    tab1, tab2 = st.tabs(["➕ Νέα Παραλαβή", "📋 Απόθεμα (Stock)"])
    
    with tab1:
        st.subheader("Καταχώρηση Τιμολογίου Αγοράς")
        with st.form("receipt_form"):
            col1, col2 = st.columns(2)
            rec_date = col1.date_input("Ημερομηνία", datetime.now())
            supplier = col2.text_input("Προμηθευτής", "π.χ. Voulgaris Fishing")
            
            col3, col4 = st.columns(2)
            product_raw = col3.selectbox("Είδος", ["Γαύρος", "Σαρδέλα", "Κολιός", "Άλλο"])
            qty_kg = col4.number_input("Συνολικό Βάρος (kg)", min_value=1.0, value=2000.0, step=100.0)
            
            price = st.number_input("Τιμή Αγοράς (€/kg)", min_value=0.0, value=2.30, step=0.1)
            
            submit_receipt = st.form_submit_button("📥 Καταχώρηση Παραλαβής")
            
            if submit_receipt:
                new_lot_id = f"LOT-{datetime.now().strftime('%y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
                new_entry = {
                    'Lot_ID': new_lot_id,
                    'Date': rec_date,
                    'Supplier': supplier,
                    'Product_Type': product_raw,
                    'Initial_Kg': qty_kg,
                    'Remaining_Kg': qty_kg,
                    'Buy_Price': price,
                    'Status': 'Active'
                }
                st.session_state['inventory'] = pd.concat([st.session_state['inventory'], pd.DataFrame([new_entry])], ignore_index=True)
                st.success(f"Η παρτίδα {new_lot_id} δημιουργήθηκε!")

    with tab2:
        st.subheader("Τρέχον Απόθεμα")
        df_inv = st.session_state['inventory']
        
        # Φίλτρο για να δείχνει μόνο τα ενεργά
        active_stock = df_inv[df_inv['Remaining_Kg'] > 0]
        
        if not active_stock.empty:
            st.dataframe(active_stock[['Lot_ID', 'Product_Type', 'Remaining_Kg', 'Initial_Kg', 'Buy_Price', 'Date']], use_container_width=True)
            
            # Μπάρες υπολοίπου
            for index, row in active_stock.iterrows():
                progress = row['Remaining_Kg'] / row['Initial_Kg']
                st.write(f"**{row['Product_Type']} ({row['Lot_ID']})** - {row['Remaining_Kg']}kg left")
                st.progress(progress)
        else:
            st.info("Η αποθήκη είναι άδεια. Κάντε μια παραλαβή.")

# ---------------------------------------------------------
# VIEW 2: ΠΑΡΑΓΩΓΗ (DAILY RUN)
# ---------------------------------------------------------
elif menu == "⚙️ Καταχώρηση Παραγωγής":
    st.header("⚙️ Ημερήσιο Δελτίο Παραγωγής")
    
    # Βήμα 1: Επιλογή Παρτίδας (Από πού τραβάμε;)
    df_inv = st.session_state['inventory']
    active_lots = df_inv[df_inv['Remaining_Kg'] > 0]['Lot_ID'].tolist()
    
    if not active_lots:
        st.error("Δεν υπάρχουν διαθέσιμες παρτίδες στην αποθήκη! Πηγαίνετε στην 'Αποθήκη' για παραλαβή.")
        st.stop()
        
    col_sel1, col_sel2 = st.columns(2)
    selected_lot_id = col_sel1.selectbox("1. Επιλογή Παρτίδας (Α' Ύλη)", active_lots)
    
    # Ανάκτηση δεδομένων παρτίδας
    lot_data = df_inv[df_inv['Lot_ID'] == selected_lot_id].iloc[0]
    current_stock = lot_data['Remaining_Kg']
    buy_price = lot_data['Buy_Price']
    
    col_sel2.info(f"📦 Διαθέσιμο Υπόλοιπο: **{current_stock} kg**\n\n💰 Τιμή Αγοράς: **{buy_price} €/kg**")
    
    st.markdown("---")
    
    with st.form("production_form"):
        st.subheader("2. Στοιχεία Επεξεργασίας")
        
        c1, c2, c3 = st.columns(3)
        input_kg = c1.number_input("⚖️ Κιλά που πήραμε (Input)", min_value=0.0, max_value=float(current_stock), value=min(500.0, float(current_stock)))
        
        # Επιλογή Προϊόντος (SKU)
        sku_key = c2.selectbox("📦 Τελικό Προϊόν (SKU)", list(PRODUCTS_DB.keys()), format_func=lambda x: PRODUCTS_DB[x]['name'])
        selected_sku = PRODUCTS_DB[sku_key]
        
        output_units = c3.number_input(f"🔢 Τεμάχια Παραγωγής ({selected_sku['weight']}kg)", min_value=0, step=1)
        
        # Υπολογισμός κιλών εξόδου αυτόματα
        calc_output_kg = output_units * selected_sku['weight']
        st.caption(f"Συνολικό Βάρος Εξόδου: {calc_output_kg} kg")

        # ---------------------------------------------------
        # ΠΡΟΑΙΡΕΤΙΚΑ ΠΕΔΙΑ (ΣΕ EXPANDERS)
        # ---------------------------------------------------
        
        with st.expander("❄️ Glazing (Πάγος) - Προαιρετικό", expanded=True):
            cg1, cg2 = st.columns(2)
            glazing_sold = cg1.slider("Target Glazing (Πώληση %)", 0, 30, 15, help="Με τι ποσοστό το πουλάμε;")
            glazing_actual = cg2.slider("Actual Glazing (Μέτρηση %)", 0, 30, 15, help="Τι μετρήσαμε πραγματικά;")
            
            if glazing_actual > glazing_sold:
                st.warning(f"⚠️ Προσοχή: Βάζετε {glazing_actual - glazing_sold}% περισσότερο πάγο/νερό από ότι χρεώνετε.")
        
        with st.expander("🛠️ Εργατικά & Συσκευασία (Κοστολόγηση) - Προαιρετικό"):
            use_labor = st.checkbox("Υπολογισμός Κόστους Εργατικών", value=False)
            labor_cost_total = 0.0
            if use_labor:
                cl1, cl2 = st.columns(2)
                workers = cl1.number_input("Αρ. Εργατών", value=5)
                hours = cl2.number_input("Ώρες Βάρδιας", value=7.0)
                wage = 8.0 # Default 8 ευρώ/ώρα
                labor_cost_total = workers * hours * wage
                st.caption(f"Σύνολο Εργατικών: {labor_cost_total} €")

            use_pack = st.checkbox("Υπολογισμός Κόστους Συσκευασίας", value=True)
            pack_cost_total = 0.0
            if use_pack:
                # Αν είναι Custom, ζητάμε τιμή, αλλιώς παίρνουμε από τη βάση
                if sku_key == "CUSTOM":
                    custom_pack_price = st.number_input("Κόστος Υλικών ανά τεμάχιο (€)", value=0.0)
                    pack_cost_total = output_units * custom_pack_price
                else:
                    unit_pack_cost = selected_sku['pack_cost']
                    st.write(f"ℹ️ {selected_sku['desc']}")
                    pack_cost_total = output_units * unit_pack_cost
                st.caption(f"Σύνολο Συσκευασίας: {pack_cost_total:.2f} €")

        submit_prod = st.form_submit_button("✅ Καταχώρηση Παραγωγής")
        
        if submit_prod and input_kg > 0:
            # Υπολογισμοί
            # 1. Καθαρό Κρέας (Πόσο ψάρι "έφαγε" η παραγωγή από την είσοδο)
            # Αν το προϊόν είναι 10kg με 15% πάγο, το καθαρό ψάρι είναι 8.5kg
            clean_weight_per_unit = selected_sku['weight'] * (1 - (glazing_actual/100))
            total_clean_fish_used = output_units * clean_weight_per_unit
            
            # 2. Απόδοση (Yield)
            yield_pct = (total_clean_fish_used / input_kg) * 100
            
            # 3. Κοστολόγηση
            raw_material_cost = input_kg * buy_price
            total_production_cost = raw_material_cost + labor_cost_total + pack_cost_total
            cost_per_kg_final = total_production_cost / calc_output_kg if calc_output_kg > 0 else 0
            
            # Αποθήκευση στο Log
            new_prod_entry = {
                'Prod_ID': str(uuid.uuid4())[:8],
                'Date': datetime.now(),
                'Source_Lot': selected_lot_id,
                'SKU': selected_sku['name'],
                'Input_Kg': input_kg,
                'Output_Units': output_units,
                'Total_Output_Kg': calc_output_kg,
                'Yield_Pct': yield_pct,
                'Glazing_Sold': glazing_sold,
                'Glazing_Actual': glazing_actual,
                'Labor_Cost': labor_cost_total,
                'Pack_Cost': pack_cost_total,
                'Total_Cost_Kg': cost_per_kg_final
            }
            st.session_state['production_log'] = pd.concat([st.session_state['production_log'], pd.DataFrame([new_prod_entry])], ignore_index=True)
            
            # Ενημέρωση Αποθήκης (Μείωση Αποθέματος)
            # Βρίσκουμε το index της παρτίδας και αφαιρούμε τα κιλά
            idx = df_inv.index[df_inv['Lot_ID'] == selected_lot_id][0]
            st.session_state['inventory'].at[idx, 'Remaining_Kg'] -= input_kg
            
            st.success("Η παραγωγή καταχωρήθηκε και το απόθεμα ενημερώθηκε!")
            
            # Quick Stats
            st.metric("Απόδοση (Yield)", f"{yield_pct:.1f}%")
            st.metric("Τελικό Κόστος", f"{cost_per_kg_final:.2f} €/kg")

# ---------------------------------------------------------
# VIEW 3: ΑΝΑΦΟΡΕΣ (REPORTS)
# ---------------------------------------------------------
elif menu == "📊 Αναφορές & Κοστολόγηση":
    st.header("📊 Αναφορές Παραγωγής")
    
    df_log = st.session_state['production_log']
    
    if df_log.empty:
        st.info("Δεν υπάρχουν ακόμα εγγραφές παραγωγής.")
    else:
        st.subheader("Ιστορικό Παραγωγών")
        st.dataframe(df_log[['Date', 'Source_Lot', 'SKU', 'Input_Kg', 'Total_Output_Kg', 'Yield_Pct', 'Total_Cost_Kg']], use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Απόδοση ανά Παρτίδα")
            fig = px.bar(df_log, x='Source_Lot', y='Yield_Pct', color='SKU', title="Yield % per Batch")
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.subheader("Ανάλυση Κόστους Τελευταίας Παραγωγής")
            last_run = df_log.iloc[-1]
            
            # Pie Chart για το πού πήγαν τα λεφτά
            # Υπολογίζουμε το κόστος Α' Ύλης ξανά πρόχειρα (Input * 2.30 μέσος όρος ή πρέπει να το σώζουμε)
            # Εδώ για το demo θα πάρουμε τα αποθηκευμένα κόστη
            costs = {
                'Εργατικά': last_run['Labor_Cost'],
                'Συσκευασία': last_run['Pack_Cost'],
                "Α' Ύλη (Εκτίμηση)": (last_run['Total_Cost_Kg'] * last_run['Total_Output_Kg']) - last_run['Labor_Cost'] - last_run['Pack_Cost']
            }
            
            fig_pie = px.pie(values=list(costs.values()), names=list(costs.keys()), title=f"Κόστος: {last_run['SKU']}")
            st.plotly_chart(fig_pie, use_container_width=True)


