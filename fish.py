import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="Fish Costing Pro", layout="wide", page_icon="🐟")

# --- ΤΙΤΛΟΣ ---
col_h1, col_h2 = st.columns([1, 6])
with col_h1:
    st.write("# 🐟")
with col_h2:
    st.title("Εργαλείο Κοστολόγησης & Παραγωγής")
    st.caption("Υπολογισμός Κόστους, Νεκρού Σημείου και Στρατηγικής Αγορών")

st.markdown("---")

# ==========================================
# 1. SIDEBAR - ΕΙΣΑΓΩΓΗ ΔΕΔΟΜΕΝΩΝ
# ==========================================
st.sidebar.header("📝 Δεδομένα Παραγωγής")

# A. Βασικά Στοιχεία
st.sidebar.subheader("Τιμές & Προϊόν")
product_name = st.sidebar.text_input("Προϊόν", "Γαύρος Ακέφαλος IQF")
selling_price = st.sidebar.number_input("Τιμή Πώλησης (€/kg)", value=4.80, step=0.10)
raw_material_price = st.sidebar.number_input("Τιμή Αγοράς Α' Ύλης (€/kg)", value=2.30, step=0.10)

# B. Δεδομένα Test (Η καρδιά του υπολογισμού)
st.sidebar.subheader("Αποτέλεσμα Test (Δοκιμής)")
input_kg = st.sidebar.number_input("Κιλά Εισόδου (Ακατέργαστο)", value=60.0)
output_kg = st.sidebar.number_input("Κιλά Εξόδου (Καθαρό)", value=42.7)
ice_percentage = st.sidebar.slider("Ποσοστό Επί Πάγου (Glazing %)", 0, 40, 15)

# C. Έξοδα
st.sidebar.subheader("Λειτουργικά Έξοδα")
workers = st.sidebar.number_input("Αριθμός Εργατών", value=5)
daily_wage = st.sidebar.number_input("Ημερομίσθιο ανά άτομο (€)", value=64.0)
packaging_cost = st.sidebar.number_input("Κόστος Συσκευασίας (€/kg)", value=0.18)
utility_cost = st.sidebar.number_input("Ενέργεια & Λοιπά (€/kg)", value=0.25)

# ==========================================
# 2. ΥΠΟΛΟΓΙΣΜΟΙ (BACKEND LOGIC)
# ==========================================

# Έλεγχος για διαίρεση με το μηδέν
if input_kg > 0:
    yield_raw = (output_kg / input_kg) # Πόσο κρέας βγάζουμε από 1 κιλό
    raw_cost_clean = raw_material_price / yield_raw # Κόστος καθαρού κρέατος
else:
    yield_raw = 0
    raw_cost_clean = 0

# Υπολογισμός με τον πάγο
# Αν βάλουμε 15% πάγο, τότε το 1 κιλό τελικού προϊόντος έχει 850γρ κρέας.
factor_ice = 1 / (1 - (ice_percentage / 100))
final_raw_cost = raw_cost_clean / factor_ice 

# Σύνολα Κόστους
total_variable_cost = final_raw_cost + packaging_cost + utility_cost
total_fixed_cost = workers * daily_wage # Σταθερό κόστος ημέρας

# Κέρδος (Margin)
margin_per_kg = selling_price - total_variable_cost
margin_per_box = margin_per_kg * 3 # Για κιβώτιο 3 κιλών

# Νεκρό Σημείο (Break Even)
if margin_per_kg > 0:
    be_kg = total_fixed_cost / margin_per_kg
    be_boxes = be_kg / 3
else:
    be_kg = 0
    be_boxes = 0

# Εκτίμηση Ημερήσιας Παραγωγής (Βάσει του Test)
# Υποθέτουμε ότι το Test των 'input_kg' έγινε σε 35 λεπτά (όπως είχες πει).
# Αν θες να το αλλάζεις, θα μπορούσαμε να βάλουμε κι αυτό input, αλλά το κρατάω σταθερό για απλότητα.
minutes_test = 35 
production_capacity_raw = (input_kg / minutes_test) * 60 * 8 # Σε 8 ώρες
production_capacity_final = (production_capacity_raw * yield_raw) * (1 + (ice_percentage/100)) # Με τον πάγο

# ==========================================
# 3. MAIN DASHBOARD - KPI CARDS
# ==========================================

col1, col2, col3, col4 = st.columns(4)
col1.metric("Κόστος Παραγωγής", f"{total_variable_cost:.2f} €/kg", delta="Χωρίς Εργατικά")
col2.metric("Κέρδος ανά Κιλό", f"{margin_per_kg:.2f} €", delta_color="normal")
col3.metric("Νεκρό Σημείο (Κιβώτια)", f"{int(be_boxes)} τμχ", help="Πόσα πρέπει να πουλήσεις για να βγάλεις τα έξοδα")
col4.metric("Εκτίμηση Κέρδους Ημέρας", f"{(production_capacity_final * margin_per_kg) - total_fixed_cost:.0f} €", help="Αν δουλέψουν φουλ 8ωρο")

# ==========================================
# 4. ΓΡΑΦΗΜΑ & ΑΝΑΛΥΣΗ (ΤΟ ΖΗΤΟΥΜΕΝΟ ΣΟΥ)
# ==========================================

st.subheader("📊 Γράφημα Νεκρού Σημείου")

if margin_per_kg > 0:
    # Σχεδιασμός Γραφήματος
    x_max = max(800, be_kg * 2) # Να προσαρμόζεται το γράφημα
    x = np.linspace(0, x_max, 100)
    revenue = selling_price * x
    cost = total_fixed_cost + (total_variable_cost * x)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(x, revenue, label='Έσοδα (Τζίρος)', color='green', linewidth=2)
    ax.plot(x, cost, label='Συνολικό Κόστος', color='red', linestyle='--', linewidth=2)
    
    # Σημείο Break Even
    ax.scatter(be_kg, be_kg * selling_price, color='black', s=120, zorder=5)
    ax.text(be_kg, (be_kg * selling_price) * 1.1, f' Break-Even\n {int(be_boxes)} Κιβώτια', color='black', fontweight='bold')

    # Περιοχές
    ax.fill_between(x, revenue, cost, where=(revenue > cost), interpolate=True, color='green', alpha=0.1)
    ax.fill_between(x, revenue, cost, where=(revenue < cost), interpolate=True, color='red', alpha=0.1)

    ax.set_xlabel("Ποσότητα (kg)")
    ax.set_ylabel("Ευρώ (€)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    st.pyplot(fig)

    # --- Η ΑΥΤΟΜΑΤΗ ΕΠΕΞΗΓΗΣΗ (NOTE) ---
    st.info(f"""
    **📌 Τι μας λέει αυτό το γράφημα:**
    
    1.  **Η "Ζώνη Κινδύνου":** Ξεκινάς την ημέρα με **-{total_fixed_cost}€** (μισθοί). Μέχρι να πουλήσεις τα πρώτα **{int(be_boxes)} κιβώτια**, η κόκκινη γραμμή είναι πάνω από την πράσινη. Αυτό σημαίνει ότι "μπαίνεις μέσα".
    2.  **Το Σημείο Μηδέν:** Μόλις πουλήσεις το **{int(be_boxes) + 1}ο κιβώτιο**, έχεις καλύψει όλα τα έξοδα της ημέρας (Ψάρια, Υλικά, Ρεύμα, Προσωπικό).
    3.  **Η "Ζώνη Κέρδους":** Από εκεί και πέρα, κάθε κιβώτιο που φεύγει από το μαγαζί, σου αφήνει καθαρό κέρδος **{margin_per_box:.2f}€** στην τσέπη.
    """)

else:
    st.error("⛔ ΠΡΟΣΟΧΗ: Η τιμή πώλησης είναι μικρότερη από το κόστος παραγωγής! Κάθε κιλό που παράγεις αυξάνει τη ζημιά.")

# ==========================================
# 5. ΕΡΓΑΛΕΙΑ ΣΤΡΑΤΗΓΙΚΗΣ (TABS)
# ==========================================
st.markdown("---")
st.header("🛠️ Εργαλεία Στρατηγικής")

tab1, tab2 = st.tabs(["🚦 Πίνακας Σεναρίων (Matrix)", "🛒 Υπολογιστής Παραγγελίας"])

with tab1:
    st.write("**Πώς αλλάζει το Κέρδος (€/kg) αν αλλάξουν οι τιμές Αγοράς & Πώλησης;**")
    
    # Δημιουργία εύρους τιμών γύρω από τις τρέχουσες
    b_min, b_max = raw_material_price - 0.5, raw_material_price + 0.5
    s_min, s_max = selling_price - 0.5, selling_price + 0.5
    
    buy_prices = np.linspace(b_min, b_max, 5)
    sell_prices = np.linspace(s_min, s_max, 5)
    
    profit_matrix = []
    for buy in buy_prices:
        row = []
        # Γρήγορος υπολογισμός κόστους για το σενάριο
        t_cost = (buy / yield_raw / factor_ice) + packaging_cost + utility_cost
        for sell in sell_prices:
            row.append(sell - t_cost)
        profit_matrix.append(row)
    
    df_matrix = pd.DataFrame(profit_matrix, 
                             index=[f"Αγορά {p:.2f}€" for p in buy_prices], 
                             columns=[f"Πώληση {p:.2f}€" for p in sell_prices])
    
    # Χρωματισμός
    def color_scale(val):
        if val < 0: color = '#ffcccc' # Light Red
        elif val < 1: color = '#ffffcc' # Light Yellow
        else: color = '#ccffcc' # Light Green
        return f'background-color: {color}; color: black'

    st.dataframe(df_matrix.style.applymap(color_scale).format("{:.2f} €"))
    st.caption("Πράσινο = Καλό Κέρδος (>1€), Κίτρινο = Μικρό Κέρδος, Κόκκινο = Ζημιά")

with tab2:
    st.subheader("Αντίστροφος Υπολογισμός (Reverse)")
    col_in1, col_in2 = st.columns(2)
    target_boxes = col_in1.number_input("Πόσα κιβώτια (3kg) ζητάει ο πελάτης;", value=100)
    
    if yield_raw > 0:
        # Μαθηματικά
        target_final_kg = target_boxes * 3
        # Αφαιρούμε πάγο για να βρούμε καθαρό κρέας
        target_meat_only = target_final_kg * (1 - (ice_percentage/100))
        # Διαιρούμε με απόδοση για να βρούμε ακατέργαστο
        needed_raw = target_meat_only / yield_raw
        
        # Υπολογισμός Χρόνου (με βάση το benchmark των 5 ατόμων / 35 λεπτών)
        # Ρυθμός παραγωγής (kg ακατέργαστου ανά λεπτό)
        rate_per_min = input_kg / 35 
        minutes_needed = needed_raw / rate_per_min
        hours_needed = minutes_needed / 60
        
        st.success(f"Για να βγάλεις **{target_boxes} κιβώτια**:")
        st.write(f"🐟 Πρέπει να αγοράσεις: **{int(needed_raw)} κιλά** ακατέργαστο ψάρι.")
        st.write(f"⏱️ Η ομάδα των {workers} ατόμων θα χρειαστεί: **{hours_needed:.1f} ώρες**.")
        st.write(f"💰 Θα κοστίσει σε υλικά & εργατικά περίπου: **{(target_final_kg * total_variable_cost) + (hours_needed/8 * total_fixed_cost):.2f} €**")
