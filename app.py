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
def cm_to_in(cm): return cm / 2.54
def in_to_cm(inch): return inch * 2.54
def kg_to_lb(kg): return kg * 2.20462
def lb_to_kg(lb): return lb / 2.20462

# --- Compact Form ---
with st.form("compact_form"):
    st.subheader("Supplier & Part Info")
    col1, col2, col3 = st.columns(3)
    with col1:
        supplier_name = st.text_input("Supplier Name")
        supplier_contact = st.text_input("Contact Person")
    with col2:
        supplier_code = st.text_input("Supplier Code")
        supplier_email = st.text_input("Email")
    with col3:
        supplier_phone = st.text_input("Phone")
    
    col4, col5, col6 = st.columns(3)
    with col4:
        part_name = st.text_input("Part Name")
    with col5:
        part_number = st.text_input("Part Number")
    with col6:
        part_group = st.text_input("Part Group")

    st.subheader("Packaging Info")
    unit_system = st.radio("Unit System", ["Metric (cm/kg)", "Imperial (in/lb)"], horizontal=True)
    length_unit = "cm" if unit_system.startswith("Metric") else "in"
    weight_unit = "kg" if unit_system.startswith("Metric") else "lb"

    col7, col8, col9 = st.columns(3)
    with col7:
        material = st.selectbox("Material", ["Corrugated", "Plastic", "Metal", "Other"])
        quantity_primary = st.number_input("Qty per Primary", min_value=1)
    with col8:
        primary_weight = st.number_input(f"Primary Weight ({weight_unit})", min_value=0.0)
    with col9:
        st.markdown("**Primary Box Dimensions**")
        dim1, dim2, dim3 = st.columns(3)
        with dim1:
            primary_L = st.number_input(f"Length ({length_unit})", min_value=0.0)
        with dim2:
            primary_W = st.number_input(f"Width ({length_unit})", min_value=0.0)
        with dim3:
            primary_D = st.number_input(f"Depth ({length_unit})", min_value=0.0)

    st.markdown("**Pallet Dimensions**")
    col10, col11, col12 = st.columns(3)
    with col10:
        secondary_L = st.number_input(f"Pallet Length ({length_unit})", min_value=0.0)
    with col11:
        secondary_W = st.number_input(f"Pallet Width ({length_unit})", min_value=0.0)
    with col12:
        secondary_D = st.number_input(f"Pallet Height ({length_unit})", min_value=0.0)

    submitted = st.form_submit_button("Submit")

# --- Calculations ---
if submitted:
    # Convert to metric for calculations
    if unit_system.startswith("Imperial"):
        primary_L_cm = in_to_cm(primary_L)
        primary_W_cm = in_to_cm(primary_W)
        primary_D_cm = in_to_cm(primary_D)
        secondary_L_cm = in_to_cm(secondary_L)
        secondary_W_cm = in_to_cm(secondary_W)
        secondary_D_cm = in_to_cm(secondary_D)
    else:
        primary_L_cm, primary_W_cm, primary_D_cm = primary_L, primary_W, primary_D
        secondary_L_cm, secondary_W_cm, secondary_D_cm = secondary_L, secondary_W, secondary_D

    # Pallet calculations
    if all(v > 0 for v in [primary_L_cm, primary_W_cm, primary_D_cm, secondary_L_cm, secondary_W_cm, secondary_D_cm]):
        boxes_per_layer = int(secondary_L_cm // primary_L_cm) * int(secondary_W_cm // primary_W_cm)
        layers = int(secondary_D_cm // primary_D_cm)
        total_boxes_per_pallet = boxes_per_layer * layers
        quantity_secondary = total_boxes_per_pallet * quantity_primary
    else:
        boxes_per_layer = layers = total_boxes_per_pallet = quantity_secondary = 0

    # Weight calculations
    pallet_weight_lb = 25
    pallet_weight_kg = pallet_weight_lb / 2.20462
    if total_boxes_per_pallet > 0 and primary_weight > 0:
        secondary_weight = (primary_weight * total_boxes_per_pallet) + (pallet_weight_lb if unit_system.startswith("Imperial") else pallet_weight_kg)
    else:
        secondary_weight = 0.0

    # Container analysis
    selected_container = st.selectbox("Container Type", ["40' Standard", "40' High Cube", "53' Trailer"])
    container_specs = {
        "40' Standard": {"L": 1200, "W": 235, "H": 239},
        "40' High Cube": {"L": 1200, "W": 235, "H": 270},
        "53' Trailer": {"L": 1600, "W": 260, "H": 279.4}
    }
    specs = container_specs[selected_container]
    container_volume = specs["L"] * specs["W"] * specs["H"]
    pallet_volume = secondary_L_cm * secondary_W_cm * secondary_D_cm

    rows = int(specs["L"] // secondary_L_cm) if secondary_L_cm > 0 else 0
    cols = int(specs["W"] // secondary_W_cm) if secondary_W_cm > 0 else 0
    stacks = int(specs["H"] // secondary_D_cm) if secondary_D_cm > 0 else 0
    pallets_per_container = rows * cols * stacks
    utilization = ((pallet_volume * pallets_per_container) / container_volume) * 100 if container_volume > 0 else 0

    # Display metrics
    st.subheader("📊 Calculated Metrics")
    st.metric("Boxes per Layer", boxes_per_layer)
    st.metric("Layers", layers)
    st.metric("Total Boxes per Pallet", total_boxes_per_pallet)
    st.metric("Qty per Secondary", quantity_secondary)
    st.metric("Secondary Weight", f"{secondary_weight:.2f} {weight_unit}")
    st.metric("Pallets per Container", pallets_per_container)
    st.metric("Container Utilization", f"{utilization:.2f}%")

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
        "Selected Container": selected_container,
        "Pallets per Container": pallets_per_container,
        "Utilization": utilization
    }
    st.session_state["submissions"].append(submission)
    st.success("Submission saved!")

# --- Dashboard ---
st.subheader("📦 Supplier Dashboard")
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
