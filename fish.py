import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- Ρυθμίσεις Σελίδας ---
st.set_page_config(page_title="Κοστολόγηση Ψαριών", layout="wide")

st.title("🐟 Κοστολόγηση Παραγωγής & Νεκρό Σημείο")
st.markdown("---")

# --- ΠΛΑΙΝΗ ΣΤΗΛΗ (ΔΕΔΟΜΕΝΑ) ---
st.sidebar.header("1. Εισαγωγή Δεδομένων")

# Επιλογές Χρήστη
product_name = st.sidebar.text_input("Όνομα Προϊόντος", "Γαύρος Ακέφαλος IQF")
selling_price = st.sidebar.number_input("Τιμή Πώλησης (€/kg)", value=4.80, step=0.10)
raw_material_price = st.sidebar.number_input("Τιμή Αγοράς Α' Ύλης (€/kg)", value=2.30, step=0.10)

st.sidebar.header("2. Παραγωγή (Test)")
input_kg = st.sidebar.number_input("Κιλά Εισόδου (Ακατέργαστο)", value=60.0)
output_kg = st.sidebar.number_input("Κιλά Εξόδου (Καθαρό)", value=42.7)
ice_percentage = st.sidebar.slider("Ποσοστό Επί Πάγου (%)", 0, 30, 15)

st.sidebar.header("3. Έξοδα")
workers = st.sidebar.number_input("Αριθμός Εργατών", value=5)
daily_wage = st.sidebar.number_input("Ημερομίσθιο ανά άτομο (€)", value=64.0)
packaging_cost = st.sidebar.number_input("Κόστος Συσκευασίας (€/kg)", value=0.18)
utility_cost = st.sidebar.number_input("Λειτουργικά (Ρεύμα/Νερό) (€/kg)", value=0.25)

# --- ΥΠΟΛΟΓΙΣΜΟΙ ---

# 1. Υπολογισμός Φύρας και Απόδοσης
if input_kg > 0:
    yield_percent = (output_kg / input_kg)  # Απόδοση καθαρίσματος
    real_cost_raw = raw_material_price / yield_percent # Κόστος καθαρού κρέατος
else:
    yield_percent = 0
    real_cost_raw = 0

# 2. Προσαρμογή με τον Πάγο
final_yield_with_ice = 1 / (1 - (ice_percentage / 100)) # Πόσο βάρος κερδίζουμε από τον πάγο
cost_raw_final = real_cost_raw / final_yield_with_ice # Το κόστος πέφτει λόγω πάγου

# 3. Εργατικά (Σταθερό Ημερήσιο Κόστος)
total_fixed_cost = workers * daily_wage

# 4. Μεταβλητό Κόστος ανά Κιλό Τελικού Προϊόντος
total_variable_cost = cost_raw_final + packaging_cost + utility_cost

# 5. Νεκρό Σημείο (Break Even)
margin_per_kg = selling_price - total_variable_cost

if margin_per_kg > 0:
    break_even_kg = total_fixed_cost / margin_per_kg
    break_even_boxes = break_even_kg / 3 # Υποθέτουμε 3κιλο κιβώτιο
else:
    break_even_kg = 0
    break_even_boxes = 0

# --- ΕΜΦΑΝΙΣΗ ΑΠΟΤΕΛΕΣΜΑΤΩΝ ---

col1, col2, col3, col4 = st.columns(4)
col1.metric("Κόστος Παραγωγής", f"{total_variable_cost:.2f} €/kg")
col2.metric("Κέρδος ανά Κιλό", f"{margin_per_kg:.2f} €", delta_color="normal")
col3.metric("Νεκρό Σημείο (kg)", f"{int(break_even_kg)} kg")
col4.metric("Νεκρό Σημείο (Κιβώτια)", f"{int(break_even_boxes)} box")

# --- ΓΡΑΦΗΜΑ ---
st.subheader("📊 Γράφημα Κερδοφορίας Ημέρας")

if margin_per_kg > 0:
    # Δημιουργία δεδομένων για το γράφημα (από 0 έως 800 κιλά)
    x = np.linspace(0, 800, 100)
    revenue = selling_price * x
    cost = total_fixed_cost + (total_variable_cost * x)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(x, revenue, label='Έσοδα (Τζίρος)', color='green', linewidth=2)
    ax.plot(x, cost, label='Συνολικά Έξοδα', color='red', linestyle='--', linewidth=2)
    
    # Ζωγραφίζουμε το Νεκρό Σημείο
    ax.scatter(break_even_kg, break_even_kg * selling_price, color='black', s=100, zorder=5)
    ax.annotate(f'Break-Even: {int(break_even_kg)}kg', 
                xy=(break_even_kg, break_even_kg * selling_price), 
                xytext=(break_even_kg+50, (break_even_kg * selling_price)-500),
                arrowprops=dict(facecolor='black', shrink=0.05))

    ax.fill_between(x, revenue, cost, where=(revenue > cost), interpolate=True, color='green', alpha=0.1)
    ax.fill_between(x, revenue, cost, where=(revenue < cost), interpolate=True, color='red', alpha=0.1)

    ax.set_xlabel("Ποσότητα Παραγωγής (kg)")
    ax.set_ylabel("Ευρώ (€)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    st.pyplot(fig)
else:
    st.error("ΠΡΟΣΟΧΗ: Η τιμή πώλησης είναι χαμηλότερη από το κόστος! Έχεις ζημιά σε κάθε κιλό.")