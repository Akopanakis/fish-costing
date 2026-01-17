import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import uuid

# ---------------------------------------------------------
# 1. ΡΥΘΜΙΣΕΙΣ & CSS
# ---------------------------------------------------------
st.set_page_config(page_title="FishFactory Pro", layout="wide", page_icon="🏭")

# Custom CSS για επαγγελματικό UI
st.markdown("""
<style>
    .main-header {font-size: 24px; font-weight: bold; color: #2C3E50; border-bottom: 2px solid #2C3E50; margin-bottom: 20px;}
    .sub-header {font-size: 18px; font-weight: bold; color: #5D6D7E; margin-top: 10px;}
    .metric-card {background-color: #F8F9F9; padding: 15px; border-radius: 8px; border-left: 5px solid #2874A6; box-shadow: 1px 1px 3px rgba(0,0,0,0.1);}
    .success-text {color: #196F3D; font-weight: bold;}
    .danger-text {color: #943126; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. INITIALIZATION (STATE)
# ---------------------------------------------------------

# A. Προεπιλεγμένα Προϊόντα (Για να μην είναι άδειο στην αρχή)
DEFAULT_PRODUCTS = {
    "GAV-3KG-STY": {"name": "Γαύρος Ακέφαλος - 3kg Φελιζόλ", "weight": 3.0, "pack_cost": 0.20, "desc": "Φελιζόλ Standard"},
    "GAV-10KG-BOX": {"name": "Γαύρος Ακέφαλος - 10kg Κιβώτιο", "weight": 10.0, "pack_cost": 0.60, "desc": "Χαρτοκιβώτιο + 2 Σακούλες"},
}

# B. Session State (Η μνήμη της εφαρμογής)
if 'inventory' not in st.session_state:
    st.session_state['inventory'] = pd.DataFrame(columns=['Lot_ID', 'Date', 'Supplier', 'Product_Type', 'Initial_Kg', 'Remaining_Kg', 'Buy_Price', 'Status'])

if 'production_log' not in st.session_state:
    st.session_state['production_log'] = pd.DataFrame(columns=[
        'Prod_ID', 'Date', 'Source_Lot', 'SKU_Name', 'Input_Kg', 'Output_Units', 'Total_Output_Kg',
        'Yield_Pct', 'Glazing_Sold', 'Glazing_Actual', 'Labor_Cost', 'Pack_Cost', 'Total_Cost_Kg'
    ])

# C. Βάση Προϊόντων (Δυναμική)
if 'products_db' not in st.session_state:
    st.session_state['products_db'] = DEFAULT_PRODUCTS

# ---------------------------------------------------------
# 3. SIDEBAR MENU
# ---------------------------------------------------------
with st.sidebar:
    st.title("🏭 FishFactory Pro")
    st.caption("Director's Console")
    st.markdown("---")
    
    menu = st.radio("Πλοήγηση:", [
        "📊 Dashboard",
        "📦 Αποθήκη (Ψάρι)",
        "🛠️ Διαχείριση Κωδικών (SKUs)",  # <-- ΝΕΟ!
        "⚙️ Καταχώρηση Παραγωγής",
        "📑 Ιστορικό & Αναφορές"
    ])
    st.markdown("---")
    st.info("💡 Tip: Στη 'Διαχείριση Κωδικών' μπορείτε να προσθέσετε νέα προϊόντα (π.χ. Φιλέτο).")

# ---------------------------------------------------------
# VIEW: DASHBOARD
# ---------------------------------------------------------
if menu == "📊 Dashboard":
    st.markdown("<div class='main-header'>📊 Executive Dashboard</div>", unsafe_allow_html=True)
    
    # Υπολογισμοί
    df_inv = st.session_state['inventory']
    df_prod = st.session_state['production_log']
    
    total_stock = df_inv['Remaining_Kg'].sum()
    active_lots = len(df_inv[df_inv['Remaining_Kg'] > 0])
    total_produced = df_prod['Total_Output_Kg'].sum() if not df_prod.empty else 0
    avg_yield = df_prod['Yield_Pct'].mean() if not df_prod.empty else 0
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Συνολικό Απόθεμα (Ψάρι)", f"{total_stock:,.0f} kg")
    col2.metric("Ενεργές Παρτίδες", str(active_lots))
    col3.metric("Παραγωγή (Σύνολο)", f"{total_produced:,.0f} kg")
    col4.metric("Μέση Απόδοση (Yield)", f"{avg_yield:.1f} %", delta="Target: 71.2%")
    
    st.markdown("---")
    
    if not df_prod.empty:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Παραγωγή ανά Προϊόν (SKU)")
            fig = px.pie(df_prod, names='SKU_Name', values='Total_Output_Kg', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.subheader("Εξέλιξη Απόδοσης (Yield)")
            fig2 = px.line(df_prod, x='Date', y='Yield_Pct', markers=True, title="Yield Trend")
            fig2.add_hline(y=71.2, line_dash="dot", annotation_text="Target")
            st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------------
# VIEW: ΑΠΟΘΗΚΗ (INVENTORY)
# ---------------------------------------------------------
elif menu == "📦 Αποθήκη (Ψάρι)":
    st.markdown("<div class='main-header'>📦 Διαχείριση Αποθήκης Α' Υλών</div>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["➕ Νέα Παραλαβή", "📋 Τρέχον Απόθεμα"])
    
    with tab1:
        with st.form("receipt_form"):
            c1, c2 = st.columns(2)
            supplier = c1.text_input("Προμηθευτής", "π.χ. Voulgaris Fishing")
            product_type = c2.selectbox("Είδος Ψαριού", ["Γαύρος", "Σαρδέλα", "Κολιός", "Άλλο"])
            
            c3, c4 = st.columns(2)
            kg_in = c3.number_input("Συνολικό Βάρος (kg)", 1000.0, step=100.0)
            price_in = c4.number_input("Τιμή Αγοράς (€/kg)", 2.30, step=0.1)
            
            lot_ref = st.text_input("Κωδικός Τιμολογίου / Lot (Προαιρετικό)")
            
            if st.form_submit_button("📥 Καταχώρηση"):
                final_lot_id = lot_ref if lot_ref else f"LOT-{datetime.now().strftime('%y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
                new_row = {
                    'Lot_ID': final_lot_id, 'Date': datetime.now(), 'Supplier': supplier,
                    'Product_Type': product_type, 'Initial_Kg': kg_in, 'Remaining_Kg': kg_in,
                    'Buy_Price': price_in, 'Status': 'Active'
                }
                st.session_state['inventory'] = pd.concat([st.session_state['inventory'], pd.DataFrame([new_row])], ignore_index=True)
                st.success(f"Η παρτίδα {final_lot_id} καταχωρήθηκε!")

    with tab2:
        df_i = st.session_state['inventory']
        active = df_i[df_i['Remaining_Kg'] > 0]
        st.dataframe(active, use_container_width=True)

# ---------------------------------------------------------
# VIEW: PRODUCT MANAGER (ΤΟ ΝΕΟ FEATURE)
# ---------------------------------------------------------
elif menu == "🛠️ Διαχείριση Κωδικών (SKUs)":
    st.markdown("<div class='main-header'>🛠️ Διαχείριση Προϊόντων & Συσκευασιών</div>", unsafe_allow_html=True)
    st.info("Εδώ ορίζετε τις 'Συνταγές' των προϊόντων σας. Αυτά θα εμφανίζονται ως επιλογές στην Παραγωγή.")
    
    col_list, col_add = st.columns([1, 1])
    
    with col_add:
        st.markdown("<div class='sub-header'>➕ Προσθήκη Νέου Κωδικού</div>", unsafe_allow_html=True)
        with st.form("add_sku_form"):
            new_name = st.text_input("Όνομα Προϊόντος", placeholder="π.χ. Γαύρος Φιλέτο 10kg")
            new_weight = st.number_input("Καθαρό Βάρος Συσκευασίας (kg)", min_value=0.1, value=10.0)
            new_cost = st.number_input("Πρότυπο Κόστος Υλικών Συσκευασίας (€/τμχ)", min_value=0.0, value=0.80, help="Πόσο κοστίζουν το κουτί, οι σακούλες και η ετικέτα μαζί;")
            new_desc = st.text_area("Περιγραφή Υλικών", placeholder="π.χ. Κουτί Master + 2 Σακούλες vacuum")
            
            if st.form_submit_button("💾 Αποθήκευση Κωδικού"):
                if new_name:
                    # Δημιουργία μοναδικού ID για το σύστημα
                    sku_id = f"SKU-{str(uuid.uuid4())[:6].upper()}"
                    st.session_state['products_db'][sku_id] = {
                        "name": new_name,
                        "weight": new_weight,
                        "pack_cost": new_cost,
                        "desc": new_desc
                    }
                    st.success(f"Το προϊόν '{new_name}' προστέθηκε επιτυχώς!")
                    st.rerun() # Refresh για να φανεί στον πίνακα
                else:
                    st.error("Το όνομα προϊόντος είναι υποχρεωτικό.")

    with col_list:
        st.markdown("<div class='sub-header'>📋 Υπάρχοντες Κωδικοί</div>", unsafe_allow_html=True)
        
        products = st.session_state['products_db']
        
        if products:
            # Μετατροπή σε πίνακα για εμφάνιση
            prod_list = []
            for pid, data in products.items():
                prod_list.append({
                    "ID": pid,
                    "Όνομα": data['name'],
                    "Βάρος (kg)": data['weight'],
                    "Κόστος Συσκ. (€)": data['pack_cost'],
                    "Περιγραφή": data['desc']
                })
            st.dataframe(pd.DataFrame(prod_list).set_index("Όνομα"), use_container_width=True)
            
            # Επιλογή διαγραφής
            to_delete = st.selectbox("Επιλογή για διαγραφή", list(products.keys()), format_func=lambda x: products[x]['name'])
            if st.button("🗑️ Διαγραφή Επιλεγμένου"):
                del st.session_state['products_db'][to_delete]
                st.warning("Διαγράφηκε.")
                st.rerun()
        else:
            st.info("Δεν υπάρχουν προϊόντα.")

# ---------------------------------------------------------
# VIEW: ΠΑΡΑΓΩΓΗ
# ---------------------------------------------------------
elif menu == "⚙️ Καταχώρηση Παραγωγής":
    st.markdown("<div class='main-header'>⚙️ Καταχώρηση Παραγωγής</div>", unsafe_allow_html=True)
    
    # 1. Επιλογή Α' Ύλης
    df_inv = st.session_state['inventory']
    active_lots = df_inv[df_inv['Remaining_Kg'] > 0]['Lot_ID'].tolist()
    
    if not active_lots:
        st.error("Η Αποθήκη είναι άδεια! Κάντε παραλαβή πρώτα.")
    else:
        col_lot, col_info = st.columns(2)
        selected_lot = col_lot.selectbox("1. Επιλογή Παρτίδας (Α' Ύλη)", active_lots)
        lot_data = df_inv[df_inv['Lot_ID'] == selected_lot].iloc[0]
        col_info.info(f"Προμηθευτής: {lot_data['Supplier']} | Υπόλοιπο: {lot_data['Remaining_Kg']} kg | Τιμή: {lot_data['Buy_Price']}€")
        
        st.markdown("---")
        
        with st.form("prod_form"):
            st.markdown("<div class='sub-header'>2. Στοιχεία Παραγωγής</div>", unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            input_kg = c1.number_input("⚖️ Input (kg Ακατέργαστου)", min_value=0.0, max_value=float(lot_data['Remaining_Kg']))
            
            # ΔΥΝΑΜΙΚΗ ΕΠΙΛΟΓΗ ΠΡΟΪΟΝΤΟΣ
            products = st.session_state['products_db']
            sku_key = c2.selectbox("📦 Τελικό Προϊόν", list(products.keys()), format_func=lambda x: products[x]['name'])
            selected_sku = products[sku_key]
            
            output_units = c3.number_input(f"🔢 Τεμάχια ({selected_sku['weight']}kg)", min_value=0, step=1)
            
            st.caption(f"Επιλεγμένο Κόστος Συσκευασίας: {selected_sku['pack_cost']}€ / τμχ ({selected_sku['desc']})")
            
            # OPTIONAL FIELDS
            with st.expander("🛠️ Εργατικά & Glazing (Προαιρετικά)", expanded=False):
                ce1, ce2 = st.columns(2)
                workers = ce1.number_input("Αρ. Εργατών", 5)
                hours = ce2.number_input("Ώρες", 7.0)
                
                cg1, cg2 = st.columns(2)
                g_sold = cg1.slider("Glazing Πώλησης %", 0, 40, 15)
                g_actual = cg2.slider("Glazing Μέτρησης %", 0, 40, 15)

            if st.form_submit_button("✅ Οριστικοποίηση"):
                if input_kg > 0 and output_units > 0:
                    # Calculations
                    total_out_kg = output_units * selected_sku['weight']
                    clean_fish_per_unit = selected_sku['weight'] * (1 - (g_actual/100))
                    total_clean_used = output_units * clean_fish_per_unit
                    yield_pct = (total_clean_used / input_kg) * 100
                    
                    # Costs
                    labor_c = workers * hours * 8.0
                    pack_c = output_units * selected_sku['pack_cost']
                    raw_c = input_kg * lot_data['Buy_Price']
                    total_c = labor_c + pack_c + raw_c
                    cost_per_kg = total_c / total_out_kg
                    
                    # Save
                    new_log = {
                        'Prod_ID': str(uuid.uuid4())[:8], 'Date': datetime.now(),
                        'Source_Lot': selected_lot, 'SKU_Name': selected_sku['name'],
                        'Input_Kg': input_kg, 'Output_Units': output_units,
                        'Total_Output_Kg': total_out_kg, 'Yield_Pct': yield_pct,
                        'Glazing_Sold': g_sold, 'Glazing_Actual': g_actual,
                        'Labor_Cost': labor_c, 'Pack_Cost': pack_c, 'Total_Cost_Kg': cost_per_kg
                    }
                    st.session_state['production_log'] = pd.concat([st.session_state['production_log'], pd.DataFrame([new_log])], ignore_index=True)
                    
                    # Update Stock
                    idx = df_inv.index[df_inv['Lot_ID'] == selected_lot][0]
                    st.session_state['inventory'].at[idx, 'Remaining_Kg'] -= input_kg
                    
                    st.success("Καταχωρήθηκε!")
                    st.metric("Τελικό Κόστος", f"{cost_per_kg:.2f} €/kg", delta=f"Yield: {yield_pct:.1f}%")

# ---------------------------------------------------------
# VIEW: ΙΣΤΟΡΙΚΟ
# ---------------------------------------------------------
elif menu == "📑 Ιστορικό & Αναφορές":
    st.markdown("<div class='main-header'>📑 Ιστορικό Παραγωγής</div>", unsafe_allow_html=True)
    df_log = st.session_state['production_log']
    if not df_log.empty:
        st.dataframe(df_log, use_container_width=True)
        
        # Profitability Chart (Assuming sell price ~4.80 for demo)
        df_log['Estimated_Profit'] = 4.80 - df_log['Total_Cost_Kg']
        fig = px.bar(df_log, x='SKU_Name', y='Estimated_Profit', color='Yield_Pct', title="Εκτίμηση Κέρδους ανά Προϊόν (με Τιμή Πώλησης 4.80€)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Δεν υπάρχουν δεδομένα.")
