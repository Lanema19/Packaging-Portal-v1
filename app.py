import streamlit as st
import pandas as pd
from PIL import Image

# --- App Config ---
st.set_page_config(page_title="Packaging Portal", layout="wide")

# --- Sidebar ---
st.sidebar.title("Packaging Portal")
st.sidebar.info("Temporary portal for packaging submissions")

# --- Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Packaging Details", "Part Details", "General Info", "Calculations", "Submission Status"])

# --- Session State ---
if "submissions" not in st.session_state:
    st.session_state["submissions"] = []

# --- Conversion Functions ---
def cm_to_in(cm): return cm / 2.54
def in_to_cm(inch): return inch * 2.54
def kg_to_lb(kg): return kg * 2.20462
def lb_to_kg(lb): return lb / 2.20462

# --- Packaging Details ---
with tab1:
    st.header("Packaging Details")
    material = st.selectbox("Material Type", ["Corrugated", "Plastic", "Metal", "Other"])
    sustainability = st.multiselect("Sustainability Indicators", ["Recyclable", "Reusable", "Biodegradable"])
    
    st.subheader("Dimensions")
    unit_system = st.radio("Unit System", ["Metric (cm/kg)", "Imperial (in/lb)"])
    
    # Primary dimensions
    primary_L = st.number_input("Primary Length", min_value=0.0)
    primary_W = st.number_input("Primary Width", min_value=0.0)
    primary_D = st.number_input("Primary Depth", min_value=0.0)
    
    # Secondary dimensions
    secondary_L = st.number_input("Secondary Length", min_value=0.0)
    secondary_W = st.number_input("Secondary Width", min_value=0.0)
    secondary_D = st.number_input("Secondary Depth", min_value=0.0)
    
    quantity_primary = st.number_input("Quantity per Primary Container", min_value=1)
    quantity_secondary = st.number_input("Quantity per Secondary Container", min_value=1)
    
    st.subheader("Weights")
    primary_weight = st.number_input("Primary Loaded Weight", min_value=0.0)
    secondary_weight = st.number_input("Secondary Loaded Weight", min_value=0.0)

# --- Part Details ---
with tab2:
    st.header("Part Details")
    part_length = st.number_input("Part Length", min_value=0.0)
    part_width = st.number_input("Part Width", min_value=0.0)
    part_depth = st.number_input("Part Depth", min_value=0.0)
    part_weight = st.number_input("Part Weight", min_value=0.0)
    fragile = st.checkbox("Fragile?")
    hazard_code = st.text_input("Hazard Classification (UN/DG Code)")

# --- General Info ---
with tab3:
    st.header("General Info")
    supplier_name = st.text_input("Supplier Name")
    supplier_location = st.text_input("Supplier Location")
    supplier_contact = st.text_input("Supplier Contact")
    
    st.subheader("Upload Packaging Images")
    uploaded_images = st.file_uploader("Select Images", accept_multiple_files=True, type=["jpg", "jpeg", "png"])
    if uploaded_images:
        st.write("Preview of Uploaded Images:")
        cols = st.columns(len(uploaded_images))
        for idx, img_file in enumerate(uploaded_images):
            img = Image.open(img_file)
            cols[idx].image(img, caption=f"Image {idx+1}", use_column_width=True)
    
    st.subheader("Upload Compliance Documents")
    uploaded_docs = st.file_uploader("Select Documents", accept_multiple_files=True, type=["pdf", "docx"])
    if uploaded_docs:
        st.write("Uploaded Documents:")
        for doc in uploaded_docs:
            st.write(f"- {doc.name}")

# --- Calculations ---
with tab4:
    st.header("Calculations")
    
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
    
    # Stacking validation
    st.subheader("Stacking Validation")
    max_stack_height = st.number_input("Max Allowed Stack Height (cm)", min_value=0.0)
    max_stack_weight = st.number_input("Max Allowed Stack Weight (kg)", min_value=0.0)
    
    if max_stack_height > 0 and max_stack_weight > 0:
        total_stack_height = primary_D_cm * quantity_secondary
        total_stack_weight = secondary_weight_kg * quantity_secondary
        
        height_ok = total_stack_height <= max_stack_height
        weight_ok = total_stack_weight <= max_stack_weight
        
        st.write(f"Total Stack Height: {total_stack_height:.2f} cm")
        st.write(f"Total Stack Weight: {total_stack_weight:.2f} kg")
        
        if height_ok and weight_ok:
            st.success("✅ Stacking within limits.")
        else:
            st.error("❌ Stacking exceeds limits!")
            if not height_ok:
                st.warning("Height exceeds maximum allowed.")
            if not weight_ok:
                st.warning("Weight exceeds maximum allowed.")
    else:
        st.info("Enter max stack height and weight to validate stacking.")
    
    # Pallet/Container Fit Validation
    st.subheader("Container Fit Validation")
    container_sizes = {
        "40' Standard": (1200, 2350),  # cm approx
        "40' High Cube": (1200, 2700),
        "53' Trailer": (1600, 2600)
    }
    
    if secondary_L_cm > 0 and secondary_W_cm > 0:
        for container, (max_width, max_height) in container_sizes.items():
            fits = secondary_W_cm <= max_width and secondary_D_cm <= max_height
            if fits:
                st.success(f"✅ Fits in {container}")
            else:
                st.error(f"❌ Does NOT fit in {container}")
    else:
        st.info("Enter pallet dimensions to validate container fit.")

# --- Submission Status ---
with tab5:
    st.header("Submission Status")
    if st.button("Submit Packaging Info"):
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