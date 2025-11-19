import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image

# --- App Config ---
st.set_page_config(page_title="Packaging Portal", layout="wide")

st.title("📦 Packaging Portal")
st.write("Manage packaging details, validate container fit, and calculate utilization.")

# --- Session State ---
if "submissions" not in st.session_state:
    st.session_state["submissions"] = []

# --- Conversion Functions ---
def cm_to_in(cm): return cm / 2.54
def in_to_cm(inch): return inch * 2.54
def kg_to_lb(kg): return kg * 2.20462
def lb_to_kg(lb): return lb / 2.20462

# --- Expanders for Sections ---
with st.expander("Packaging Details"):
    material = st.selectbox("Material Type", ["Corrugated", "Plastic", "Metal", "Other"], key="material")
    sustainability = st.multiselect("Sustainability Indicators", ["Recyclable", "Reusable", "Biodegradable"], key="sustainability")

    unit_system = st.radio("Unit System", ["Metric (cm/kg)", "Imperial (in/lb)"], key="unit_system")

    st.subheader("Primary Dimensions")
    primary_L = st.number_input("Length", min_value=0.0, key="primary_L")
    primary_W = st.number_input("Width", min_value=0.0, key="primary_W")
    primary_D = st.number_input("Depth", min_value=0.0, key="primary_D")

    st.subheader("Secondary (Pallet) Dimensions")
    secondary_L = st.number_input("Length", min_value=0.0, key="secondary_L")
    secondary_W = st.number_input("Width", min_value=0.0, key="secondary_W")
    secondary_D = st.number_input("Height", min_value=0.0, key="secondary_D")

    quantity_primary = st.number_input("Quantity per Primary Container", min_value=1, key="quantity_primary")
    quantity_secondary = st.number_input("Quantity per Secondary Container", min_value=1, key="quantity_secondary")

    st.subheader("Weights")
    primary_weight = st.number_input("Primary Loaded Weight", min_value=0.0, key="primary_weight")
    secondary_weight = st.number_input("Secondary Loaded Weight", min_value=0.0, key="secondary_weight")

# --- Convert to metric for calculations ---
if unit_system == "Imperial (in/lb)":
    primary_L_cm = in_to_cm(primary_L)
    primary_W_cm = in_to_cm(primary_W)
    primary_D_cm = in_to_cm(primary_D)
    secondary_L_cm = in_to_cm(secondary_L)
    secondary_W_cm = in_to_cm(secondary_W)
    secondary_D_cm = in_to_cm(secondary_D)
    primary_weight_kg = lb_to_kg(primary_weight)
    secondary_weight_kg = lb_to_kg(secondary_weight)
else:
    primary_L_cm, primary_W_cm, primary_D_cm = primary_L, primary_W, primary_D
    secondary_L_cm, secondary_W_cm, secondary_D_cm = secondary_L, secondary_W, secondary_D
    primary_weight_kg, secondary_weight_kg = primary_weight, secondary_weight

# --- Calculations ---
st.header("Calculated Results")

# Pallet volume
if secondary_L_cm > 0 and secondary_W_cm > 0 and secondary_D_cm > 0:
    pallet_volume = secondary_L_cm * secondary_W_cm * secondary_D_cm
else:
    pallet_volume = 0

# Primary boxes per pallet
if primary_L_cm > 0 and primary_W_cm > 0 and primary_D_cm > 0 and pallet_volume > 0:
    boxes_per_layer = int(secondary_L_cm // primary_L_cm) * int(secondary_W_cm // primary_W_cm)
    layers = int(secondary_D_cm // primary_D_cm)
    total_boxes_per_pallet = boxes_per_layer * layers
    st.write(f"Boxes per layer: {boxes_per_layer}, Layers: {layers}, Total boxes per pallet: {total_boxes_per_pallet}")
else:
    total_boxes_per_pallet = 0
    st.info("Enter all dimensions to calculate boxes per pallet.")

# Container specs with updated trailer height (110 inches = 279.4 cm)
container_specs = {
    "40' Standard": {"L": 1200, "W": 235, "H": 239, "MaxWeight": 28000},
    "40' High Cube": {"L": 1200, "W": 235, "H": 270, "MaxWeight": 28000},
    "53' Trailer": {"L": 1600, "W": 260, "H": 279.4, "MaxWeight": 30000}  # Updated height
}

if secondary_L_cm > 0 and secondary_W_cm > 0 and secondary_D_cm > 0:
    for name, specs in container_specs.items():
        st.subheader(f"{name}")
        container_volume = specs["L"] * specs["W"] * specs["H"]
        rows = int(specs["L"] // secondary_L_cm)
        cols = int(specs["W"] // secondary_W_cm)
        pallets_per_container = rows * cols
        parts_per_container = pallets_per_container * total_boxes_per_pallet
        utilization = ((pallet_volume * pallets_per_container) / container_volume) * 100 if container_volume > 0 else 0

        st.write(f"Pallets per container: {pallets_per_container}")
        st.write(f"Parts per container: {parts_per_container}")
        st.write(f"Cube Utilization (Container) (%): {utilization:.2f}")

        # Visualization
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.set_title(f"{name} Layout")
        ax.set_xlim(0, specs["L"])
        ax.set_ylim(0, specs["W"])
        ax.set_xlabel("Length (cm)")
        ax.set_ylabel("Width (cm)")

        # Draw container outline
        ax.add_patch(plt.Rectangle((0, 0), specs["L"], specs["W"], fill=None, edgecolor='black', linewidth=2))

        # Draw pallets
        for r in range(rows):
            for c in range(cols):
                x = r * secondary_L_cm
                y = c * secondary_W_cm
                ax.add_patch(plt.Rectangle((x, y), secondary_L_cm, secondary_W_cm, color='skyblue', alpha=0.6))

        st.pyplot(fig)
else:
    st.info("Enter pallet dimensions to calculate container fit and visualization.")

# --- Submission Section ---
if st.button("Submit Packaging Info", key="submit_btn"):
    submission = {
        "Material": material,
        "Dimensions": f"{primary_L}x{primary_W}x{primary_D} ({unit_system})",
        "Weight": f"{primary_weight} ({unit_system})",
        "Supplier": supplier_name if 'supplier_name' in locals() else '',
        "Fragile": fragile if 'fragile' in locals() else False
    }
    st.session_state["submissions"].append(submission)
    st.success("Submission added!")

st.write("Current Submissions:")
st.dataframe(pd.DataFrame(st.session_state["submissions"]))
