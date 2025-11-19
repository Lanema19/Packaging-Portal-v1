import streamlit as st
import pandas as pd
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

with st.expander("Part Details"):
    part_length = st.number_input("Part Length", min_value=0.0, key="part_length")
    part_width = st.number_input("Part Width", min_value=0.0, key="part_width")
    part_depth = st.number_input("Part Depth", min_value=0.0, key="part_depth")
    part_weight = st.number_input("Part Weight", min_value=0.0, key="part_weight")
    fragile = st.checkbox("Fragile?", key="fragile")
    hazard_code = st.text_input("Hazard Classification (UN/DG Code)", key="hazard_code")

with st.expander("General Info"):
    supplier_name = st.text_input("Supplier Name", key="supplier_name")
    supplier_location = st.text_input("Supplier Location", key="supplier_location")
    supplier_contact = st.text_input("Supplier Contact", key="supplier_contact")

with st.expander("Uploads"):
    uploaded_images = st.file_uploader("Upload Packaging Images", accept_multiple_files=True, type=["jpg", "jpeg", "png"], key="images_uploader")
    if uploaded_images:
        st.write("Preview of Uploaded Images:")
        cols = st.columns(len(uploaded_images))
        for idx, img_file in enumerate(uploaded_images):
            img = Image.open(img_file)
            cols[idx].image(img, caption=f"Image {idx+1}", use_column_width=True, key=f"image_{idx}")

    uploaded_docs = st.file_uploader("Upload Compliance Documents", accept_multiple_files=True, type=["pdf", "docx"], key="docs_uploader")
    if uploaded_docs:
        st.write("Uploaded Documents:")
        for doc in uploaded_docs:
            st.write(f"- {doc.name}")

# --- Calculations Section ---
st.header("Calculated Results")

# Convert all values to metric for calculations
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

# Cube utilization
if secondary_L_cm > 0 and secondary_W_cm > 0 and secondary_D_cm > 0:
    pallet_volume = secondary_L_cm * secondary_W_cm * secondary_D_cm
    package_volume = primary_L_cm * primary_W_cm * primary_D_cm * quantity_primary
    cube_utilization = (package_volume / pallet_volume) * 100 if pallet_volume > 0 else 0
    st.metric("Cube Utilization (%)", f"{cube_utilization:.2f}")
else:
    st.warning("Enter pallet dimensions to calculate cube utilization.")

# Container-based stacking validation
st.subheader("Container Fit & Stacking Validation")
container_specs = {
    "40' Standard": {"L": 1200, "W": 235, "H": 239, "MaxWeight": 28000},
    "40' High Cube": {"L": 1200, "W": 235, "H": 270, "MaxWeight": 28000},
    "53' Trailer": {"L": 1600, "W": 260, "H": 260, "MaxWeight": 30000}
}

if secondary_L_cm > 0 and secondary_W_cm > 0 and secondary_D_cm > 0:
    for name, specs in container_specs.items():
        fits = secondary_L_cm <= specs["L"] and secondary_W_cm <= specs["W"]
        max_stack_height = specs["H"]
        max_stack_weight = specs["MaxWeight"]

        # Calculate stacking
        total_stack_height = secondary_D_cm * quantity_secondary
        total_stack_weight = secondary_weight_kg * quantity_secondary

        st.write(f"**{name}**")
        if fits:
            if total_stack_height <= max_stack_height and total_stack_weight <= max_stack_weight:
                st.success(f"✅ Fits and stacking within limits (Height: {total_stack_height:.2f} cm, Weight: {total_stack_weight:.2f} kg)")
            else:
                st.error(f"❌ Fits but stacking exceeds limits! Height: {total_stack_height:.2f} cm, Weight: {total_stack_weight:.2f} kg")
        else:
            st.error("❌ Pallet does NOT fit in this container.")
else:
    st.info("Enter pallet dimensions to validate container fit and stacking.")

# --- Submission Section ---
if st.button("Submit Packaging Info", key="submit_btn"):
    submission = {
        "Material": material,
        "Dimensions": f"{primary_L}x{primary_W}x{primary_D} ({unit_system})",
        "Weight": f"{primary_weight} ({unit_system})",
        "Supplier": supplier_name,
        "Fragile": fragile
    }
    st.session_state["submissions"].append(submission)
    st.success("Submission added!")

st.write("Current Submissions:")
st.dataframe(pd.DataFrame(st.session_state["submissions"]))
