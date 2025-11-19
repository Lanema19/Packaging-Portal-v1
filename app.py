import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- App Config ---
st.set_page_config(page_title="📦 Supplier Packaging Portal", layout="wide")

st.title("📦 Supplier Packaging Portal")
st.write("Manage packaging details, validate container fit, and calculate utilization.")

# --- Session State ---
if "submissions" not in st.session_state:
    st.session_state["submissions"] = []

# --- Conversion Functions ---
def cm_to_in(cm): return cm / 2.54
def in_to_cm(inch): return inch * 2.54
def kg_to_lb(kg): return kg * 2.20462
def lb_to_kg(lb): return lb / 2.20462

# --- Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Supplier Info", "Packaging Info", "Upload & Images", "Supplier Dashboard", "Search & Filter"])

# --- Tab 1: Supplier Info ---
with tab1:
    st.header("Supplier Information")
    supplier_name = st.text_input("Supplier Name", key="supplier_name")
    supplier_code = st.text_input("Supplier Code", key="supplier_code")
    supplier_contact = st.text_input("Contact Person", key="supplier_contact")
    supplier_email = st.text_input("Email", key="supplier_email")
    supplier_phone = st.text_input("Phone", key="supplier_phone")

    st.subheader("Part Details")
    part_name = st.text_input("Part Name", key="part_name")
    part_number = st.text_input("Part Number", key="part_number")
    part_group = st.text_input("Part Group", key="part_group")

# --- Tab 2: Packaging Info ---
with tab2:
    st.header("Packaging Details")

    unit_system = st.radio("Unit System", ["Metric (cm/kg)", "Imperial (in/lb)"], key="unit_system")
    length_unit = "cm" if unit_system.startswith("Metric") else "in"
    weight_unit = "kg" if unit_system.startswith("Metric") else "lb"

    material = st.selectbox("Material Type", ["Corrugated", "Plastic", "Metal", "Other"], key="material")

    st.subheader("Primary Dimensions")
    primary_L = st.number_input(f"Length ({length_unit})", min_value=0.0, key="primary_L")
    primary_W = st.number_input(f"Width ({length_unit})", min_value=0.0, key="primary_W")
    primary_D = st.number_input(f"Depth ({length_unit})", min_value=0.0, key="primary_D")

    st.subheader("Secondary (Pallet) Dimensions")
    secondary_L = st.number_input(f"Pallet Length ({length_unit})", min_value=0.0, key="secondary_L")
    secondary_W = st.number_input(f"Pallet Width ({length_unit})", min_value=0.0, key="secondary_W")
    secondary_D = st.number_input(f"Pallet Height ({length_unit})", min_value=0.0, key="secondary_D")

    quantity_primary = st.number_input("Quantity per Primary Container", min_value=1, key="quantity_primary")

    st.subheader("Weights")
    primary_weight = st.number_input(f"Primary Loaded Weight ({weight_unit})", min_value=0.0, key="primary_weight")

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

    # --- Calculated Results ---
    st.subheader("Calculated Pallet Results")
    if primary_L_cm > 0 and primary_W_cm > 0 and primary_D_cm > 0 and secondary_L_cm > 0 and secondary_W_cm > 0 and secondary_D_cm > 0:
        boxes_per_layer = int(secondary_L_cm // primary_L_cm) * int(secondary_W_cm // primary_W_cm)
        layers = int(secondary_D_cm // primary_D_cm)
        total_boxes_per_pallet = boxes_per_layer * layers
        st.write(f"**Boxes per layer:** {boxes_per_layer}")
        st.write(f"**Layers:** {layers}")
        st.write(f"**Total boxes per pallet:** {total_boxes_per_pallet}")

        # Auto-calculate quantity per secondary container
        quantity_secondary = total_boxes_per_pallet * quantity_primary
        st.write(f"**Auto-calculated Quantity per Secondary Container:** {quantity_secondary}")
    else:
        total_boxes_per_pallet = 0
        quantity_secondary = 0
        st.info("Enter all dimensions to calculate pallet results.")

    # Auto-calculate secondary weight
    pallet_weight_lb = 25
    pallet_weight_kg = pallet_weight_lb / 2.20462
    if total_boxes_per_pallet > 0 and primary_weight > 0:
        secondary_weight = (primary_weight * total_boxes_per_pallet) + (pallet_weight_lb if unit_system.startswith("Imperial") else pallet_weight_kg)
    else:
        secondary_weight = 0.0

    # Display secondary weight as disabled input
    st.number_input(f"Secondary Loaded Weight ({weight_unit})", value=secondary_weight, disabled=True, key="secondary_weight")

    # --- Container Analysis ---
    st.subheader("Container Analysis")
    container_specs = {
        "40' Standard": {"L": 1200, "W": 235, "H": 239},
        "40' High Cube": {"L": 1200, "W": 235, "H": 270},
        "53' Trailer": {"L": 1600, "W": 260, "H": 279.4}
    }
    selected_container = st.selectbox("Select Container Type", list(container_specs.keys()))

    if secondary_L_cm > 0 and secondary_W_cm > 0 and secondary_D_cm > 0 and total_boxes_per_pallet > 0:
        specs = container_specs[selected_container]
        container_volume = specs["L"] * specs["W"] * specs["H"]
        pallet_volume = secondary_L_cm * secondary_W_cm * secondary_D_cm
        rows = int(specs["L"] // secondary_L_cm)
        cols = int(specs["W"] // secondary_W_cm)
        stacks = int(specs["H"] // secondary_D_cm)
        pallets_per_container = rows * cols * stacks
        utilization = ((pallet_volume * pallets_per_container) / container_volume) * 100 if container_volume > 0 else 0

        st.write(f"**Cube Utilization for {selected_container}:** {utilization:.2f}%")

        # 3D Visualization
        fig = go.Figure()
        container_edges = [
            [(0, 0, 0), (specs["L"], 0, 0)],
            [(0, specs["W"], 0), (specs["L"], specs["W"], 0)],
            [(0, 0, specs["H"]), (specs["L"], 0, specs["H"])],
            [(0, specs["W"], specs["H"]), (specs["L"], specs["W"], specs["H"])],
            [(0, 0, 0), (0, specs["W"], 0)],
            [(specs["L"], 0, 0), (specs["L"], specs["W"], 0)],
            [(0, 0, specs["H"]), (0, specs["W"], specs["H"])],
            [(specs["L"], 0, specs["H"]), (specs["L"], specs["W"], specs["H"])],
            [(0, 0, 0), (0, 0, specs["H"])],
            [(specs["L"], 0, 0), (specs["L"], 0, specs["H"])],
            [(0, specs["W"], 0), (0, specs["W"], specs["H"])],
            [(specs["L"], specs["W"], 0), (specs["L"], specs["W"], specs["H"])]
        ]
        for edge in container_edges:
            fig.add_trace(go.Scatter3d(x=[edge[0][0], edge[1][0]], y=[edge[0][1], edge[1][1]], z=[edge[0][2], edge[1][2]], mode='lines', line=dict(color='gray', width=4), showlegend=False))

        st.plotly_chart(fig, use_container_width=True)

# --- Tab 3: Upload & Images ---
with tab3:
    st.header("Upload Testing & Images")
    uploaded_files = st.file_uploader("Upload ISTA / UN Testing Reports", type=["pdf", "xlsx", "csv"], accept_multiple_files=True)
    primary_img = st.file_uploader("Primary Packaging Image", type=["jpg", "jpeg", "png"], key="primary_img")
    secondary_img = st.file_uploader("Secondary Packaging Image", type=["jpg", "jpeg", "png"], key="secondary_img")
    unit_load_img = st.file_uploader("Full Unit Load Image", type=["jpg", "jpeg", "png"], key="unit_load_img")

    if primary_img: st.image(primary_img, caption="Primary Packaging", use_column_width=True)
    if secondary_img: st.image(secondary_img, caption="Secondary Packaging", use_column_width=True)
    if unit_load_img: st.image(unit_load_img, caption="Full Unit Load", use_column_width=True)

    if st.button("Submit Packaging Info", key="submit_btn"):
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
            "Uploaded Files": [file.name for file in uploaded_files] if uploaded_files else [],
            "Primary Image": primary_img.name if primary_img else "",
            "Secondary Image": secondary_img.name if secondary_img else "",
            "Unit Load Image": unit_load_img.name if unit_load_img else ""
        }
        st.session_state["submissions"].append(submission)
        st.success("Submission added!")

# --- Tab 4: Supplier Dashboard ---
with tab4:
    st.header("Supplier Dashboard")
    if st.session_state["submissions"]:
        df = pd.DataFrame(st.session_state["submissions"])
        st.subheader("Summary Metrics")
        st.metric("Total Submissions", len(df))
        st.metric("Unique Suppliers", df["Supplier Name"].nunique())
        if "Secondary Weight" in df.columns:
            st.metric("Avg Secondary Weight", f"{df['Secondary Weight'].mean():.2f}")
        sort_column = st.selectbox("Sort by Column", df.columns)
        sort_order = st.radio("Sort Order", ["Ascending", "Descending"])
        df = df.sort_values(by=sort_column, ascending=(sort_order == "Ascending"))
        st.dataframe(df)
    else:
        st.info("No submissions yet.")

# --- Tab 5: Search & Filter ---
with tab5:
    st.header("Search & Filter")
    if st.session_state["submissions"]:
        df = pd.DataFrame(st.session_state["submissions"])
        supplier_filter = st.text_input("Filter by Supplier Name or Code")
        part_name_filter = st.text_input("Filter by Part Name")
        part_number_filter = st.text_input("Filter by Part Number")
        part_group_filter = st.text_input("Filter by Part Group")

        if supplier_filter:
            df = df[df["Supplier Name"].str.contains(supplier_filter, case=False) | df["Supplier Code"].str.contains(supplier_filter, case=False)]
        if part_name_filter:
            df = df[df["Part Name"].str.contains(part_name_filter, case=False)]
        if part_number_filter:
            df = df[df["Part Number"].str.contains(part_number_filter, case=False)]
        if part_group_filter:
            df = df[df["Part Group"].str.contains(part_group_filter, case=False)]

        st.dataframe(df)
    else:
        st.info("No submissions yet.")


