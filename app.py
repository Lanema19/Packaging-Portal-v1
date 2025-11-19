import streamlit as st
import pandas as pd

# --- App Config ---
st.set_page_config(page_title="📦 Supplier Packaging Portal", layout="wide")
st.title("📦 Supplier Packaging Portal")
st.write("Compact view for supplier and packaging submission.")

# --- Session State ---
if "submissions" not in st.session_state:
    st.session_state["submissions"] = []

# --- Conversion Functions ---
def cm_to_in(cm): return round(cm / 2.54, 2)
def in_to_cm(inch): return round(inch * 2.54, 2)
def kg_to_lb(kg): return round(kg * 2.20462, 2)
def lb_to_kg(lb): return round(lb / 2.20462, 2)

# --- Compact Form ---
with st.form("compact_form"):
    st.subheader("Supplier & Part Info")
    col1, col2, col3 = st.columns(3)
    with col1:
        supplier_name = st.text_input("Supplier Name", key="supplier_name")
        supplier_contact = st.text_input("Contact Person", key="supplier_contact")
    with col2:
        supplier_code = st.text_input("Supplier Code", key="supplier_code")
        supplier_email = st.text_input("Email", key="supplier_email")
    with col3:
        supplier_phone = st.text_input("Phone", key="supplier_phone")
    
    col4, col5, col6 = st.columns(3)
    with col4:
        part_name = st.text_input("Part Name", key="part_name")
    with col5:
        part_number = st.text_input("Part Number", key="part_number")
    with col6:
        part_group = st.text_input("Part Group", key="part_group")

    st.subheader("Packaging Info")
    unit_system = st.radio("Unit System", ["Metric (cm/kg)", "Imperial (in/lb)"], horizontal=True, key="unit_system")
    is_metric = unit_system.startswith("Metric")
    length_unit = "cm" if is_metric else "in"
    weight_unit = "kg" if is_metric else "lb"

    col7, col8, col9 = st.columns(3)
    with col7:
        material = st.selectbox("Material", ["Corrugated", "Plastic", "Metal", "Other"], key="material")
        quantity_primary = st.number_input("Qty per Primary", min_value=1, key="quantity_primary")
    with col8:
        primary_weight_metric = st.number_input("Primary Weight (kg)", min_value=0.0, key="primary_weight_metric")

    # --- Primary Box Dimensions ---
    st.markdown(f"**Primary Box Dimensions ({length_unit})**")
    dim1, dim2, dim3 = st.columns(3)
    with dim1:
        primary_L_cm = st.number_input("Length", min_value=0.0, key="primary_L_cm")
    with dim2:
        primary_W_cm = st.number_input("Width", min_value=0.0, key="primary_W_cm")
    with dim3:
        primary_D_cm = st.number_input("Depth", min_value=0.0, key="primary_D_cm")

    # --- Pallet Dimensions ---
    st.markdown(f"**Pallet Dimensions ({length_unit})**")
    pdim1, pdim2, pdim3 = st.columns(3)
    with pdim1:
        secondary_L_cm = st.number_input("Length", min_value=0.0, key="secondary_L_cm")
    with pdim2:
        secondary_W_cm = st.number_input("Width", min_value=0.0, key="secondary_W_cm")
    with pdim3:
        secondary_D_cm = st.number_input("Height", min_value=0.0, key="secondary_D_cm")

    submitted = st.form_submit_button("Submit")

# --- Calculations ---
if submitted:
    # Convert to imperial for display if needed
    primary_weight = primary_weight_metric if is_metric else kg_to_lb(primary_weight_metric)
    primary_L = primary_L_cm if is_metric else cm_to_in(primary_L_cm)
    primary_W = primary_W_cm if is_metric else cm_to_in(primary_W_cm)
    primary_D = primary_D_cm if is_metric else cm_to_in(primary_D_cm)
    secondary_L = secondary_L_cm if is_metric else cm_to_in(secondary_L_cm)
    secondary_W = secondary_W_cm if is_metric else cm_to_in(secondary_W_cm)
    secondary_D = secondary_D_cm if is_metric else cm_to_in(secondary_D_cm)

    # Pallet calculations
    if all(v > 0 for v in [primary_L_cm, primary_W_cm, primary_D_cm, secondary_L_cm, secondary_W_cm, secondary_D_cm]):
        boxes_per_layer = int(secondary_L_cm // primary_L_cm) * int(secondary_W_cm // primary_W_cm)
        layers = int(secondary_D_cm // primary_D_cm)
        total_boxes_per_pallet = boxes_per_layer * layers
        quantity_secondary = total_boxes_per_pallet * quantity_primary
    else:
        boxes_per_layer = layers = total_boxes_per_pallet = quantity_secondary = 0

    # Weight calculations
    pallet_weight_kg = 25 / 2.20462
    secondary_weight_metric = (primary_weight_metric * total_boxes_per_pallet) + pallet_weight_kg if total_boxes_per_pallet > 0 else 0.0
    secondary_weight = secondary_weight_metric if is_metric else kg_to_lb(secondary_weight_metric)

    # Save submission
    submission = {
        "Supplier Name": supplier_name,
        "Supplier Code": supplier_code,
        "Contact": supplier_contact,
        "Email": supplier_email,
        "Phone": supplier_phone,
        "Part Name": part_name,
        "Part Number": part_number,
        "Part Group": part_group,
        "Material": material,
        "Dimensions": f"{primary_L}x{primary_W}x{primary_D} ({length_unit})",
        "Weight": f"{primary_weight} ({weight_unit})",
        "Quantity per Primary": quantity_primary,
        "Quantity per Secondary": quantity_secondary,
        "Secondary Weight": secondary_weight,
    }
    st.session_state["submissions"].append(submission)
    st.success("Submission saved!")

    # --- Container Analysis Toggle ---
    st.subheader("📦 Container Utilization Comparison")
    container_specs = {
        "40' Standard": {"L": 1200, "W": 235, "H": 239},
        "40' High Cube": {"L": 1200, "W": 235, "H": 270},
        "53' Trailer": {"L": 1600, "W": 260, "H": 279.4}
    }
    selected_container = st.selectbox("Select Container Type", list(container_specs.keys()), key="container_type")
    specs = container_specs[selected_container]
    container_volume = specs["L"] * specs["W"] * specs["H"]
    pallet_volume = secondary_L_cm * secondary_W_cm * secondary_D_cm

    rows = int(specs["L"] // secondary_L_cm) if secondary_L_cm > 0 else 0
    cols = int(specs["W"] // secondary_W_cm) if secondary_W_cm > 0 else 0
    stacks = int(specs["H"] // secondary_D_cm) if secondary_D_cm > 0 else 0
    pallets_per_container = rows * cols * stacks
    utilization = ((pallet_volume * pallets_per_container) / container_volume) * 100 if container_volume > 0 else 0

    st.metric("Boxes per Layer", boxes_per_layer)
    st.metric("Layers", layers)
    st.metric("Total Boxes per Pallet", total_boxes_per_pallet)
    st.metric("Qty per Secondary", quantity_secondary)
    st.metric("Secondary Weight", f"{secondary_weight:.2f} {weight_unit}")
    st.metric("Pallets per Container", pallets_per_container)
    st.metric("Container Utilization", f"{utilization:.2f}%")

# --- Dashboard ---
st.subheader("📊 Supplier Dashboard")
if st.session_state["submissions"]:
    df = pd.DataFrame(st.session_state["submissions"])
    st.metric("Total Submissions", len(df))
    st.metric("Unique Suppliers", df["Supplier Name"].nunique())
    st.metric("Avg Secondary Weight", f"{df['Secondary Weight'].mean():.2f}")
    sort_column = st.selectbox("Sort by Column", df.columns)
    sort_order = st.radio("Sort Order", ["Ascending", "Descending"])
    df = df.sort_values(by=sort_column, ascending=(sort_order == "Ascending"))
    st.dataframe(df)
else:
    st.info("No submissions yet.")
