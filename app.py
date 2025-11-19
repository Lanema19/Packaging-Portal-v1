import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- App Config ---
st.set_page_config(page_title="📦 Packaging Portal", layout="wide")

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

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["Supplier Info", "Packaging Info", "Results"])

# --- Tab 1: Supplier Info ---
with tab1:
    st.header("Supplier Information")
    supplier_name = st.text_input("Supplier Name", key="supplier_name")
    supplier_code = st.text_input("Supplier Code", key="supplier_code")
    supplier_contact = st.text_input("Contact Person", key="supplier_contact")
    supplier_email = st.text_input("Email", key="supplier_email")
    supplier_phone = st.text_input("Phone", key="supplier_phone")

# --- Tab 2: Packaging Info ---
with tab2:
    st.header("Packaging Details")

    unit_system = st.radio("Unit System", ["Metric (cm/kg)", "Imperial (in/lb)"], key="unit_system")
    length_unit = "cm" if unit_system.startswith("Metric") else "in"
    weight_unit = "kg" if unit_system.startswith("Metric") else "lb"

    material = st.selectbox("Material Type", ["Corrugated", "Plastic", "Metal", "Other"], key="material")
    sustainability = st.multiselect("Sustainability Indicators", ["Recyclable", "Reusable", "Biodegradable"], key="sustainability")

    st.subheader("Primary Dimensions")
    primary_L = st.number_input(f"Length ({length_unit})", min_value=0.0, key="primary_L")
    primary_W = st.number_input(f"Width ({length_unit})", min_value=0.0, key="primary_W")
    primary_D = st.number_input(f"Depth ({length_unit})", min_value=0.0, key="primary_D")

    st.subheader("Secondary (Pallet) Dimensions")
    secondary_L = st.number_input(f"Pallet Length ({length_unit})", min_value=0.0, key="secondary_L")
    secondary_W = st.number_input(f"Pallet Width ({length_unit})", min_value=0.0, key="secondary_W")
    secondary_D = st.number_input(f"Pallet Height ({length_unit})", min_value=0.0, key="secondary_D")

    quantity_primary = st.number_input("Quantity per Primary Container", min_value=1, key="quantity_primary")
    quantity_secondary = st.number_input("Quantity per Secondary Container", min_value=1, key="quantity_secondary")

    st.subheader("Weights")
    primary_weight = st.number_input(f"Primary Loaded Weight ({weight_unit})", min_value=0.0, key="primary_weight")
    secondary_weight = st.number_input(f"Secondary Loaded Weight ({weight_unit})", min_value=0.0, key="secondary_weight")

    fragile = st.checkbox("Fragile?", key="fragile")

# --- Convert to metric for calculations ---
if unit_system.startswith("Imperial"):
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

# --- Tab 3: Results ---
with tab3:
    st.header("Calculated Results")

    pallet_volume = secondary_L_cm * secondary_W_cm * secondary_D_cm if secondary_L_cm > 0 and secondary_W_cm > 0 and secondary_D_cm > 0 else 0

    if primary_L_cm > 0 and primary_W_cm > 0 and primary_D_cm > 0 and pallet_volume > 0:
        boxes_per_layer = int(secondary_L_cm // primary_L_cm) * int(secondary_W_cm // primary_W_cm)
        layers = int(secondary_D_cm // primary_D_cm)
        total_boxes_per_pallet = boxes_per_layer * layers
        st.write(f"Boxes per layer: {boxes_per_layer}, Layers: {layers}, Total boxes per pallet: {total_boxes_per_pallet}")
    else:
        total_boxes_per_pallet = 0
        st.info("Enter all dimensions to calculate boxes per pallet.")

    container_specs = {
        "40' Standard": {"L": 1200, "W": 235, "H": 239, "MaxWeight": 28000},
        "40' High Cube": {"L": 1200, "W": 235, "H": 270, "MaxWeight": 28000},
        "53' Trailer": {"L": 1600, "W": 260, "H": 279.4, "MaxWeight": 30000}
    }

    if secondary_L_cm > 0 and secondary_W_cm > 0 and secondary_D_cm > 0:
        for name, specs in container_specs.items():
            st.subheader(f"{name}")
            container_volume = specs["L"] * specs["W"] * specs["H"]
            rows = int(specs["L"] // secondary_L_cm)
            cols = int(specs["W"] // secondary_W_cm)
            stacks = int(specs["H"] // secondary_D_cm)
            pallets_per_container = rows * cols * stacks
            parts_per_container = pallets_per_container * total_boxes_per_pallet
            utilization = ((pallet_volume * pallets_per_container) / container_volume) * 100 if container_volume > 0 else 0

            st.write(f"Pallets per container: {pallets_per_container}")
            st.write(f"Parts per container: {parts_per_container}")
            st.write(f"Cube Utilization (Container) (%): {utilization:.2f}")

            # --- Realistic 3D Visualization ---
            fig = go.Figure()

            # Container wireframe
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
                fig.add_trace(go.Scatter3d(
                    x=[edge[0][0], edge[1][0]],
                    y=[edge[0][1], edge[1][1]],
                    z=[edge[0][2], edge[1][2]],
                    mode='lines',
                    line=dict(color='gray', width=4),
                    showlegend=False
                ))

            # Pallets
            for r in range(rows):
                for c in range(cols):
                    for s in range(stacks):
                        x0 = r * secondary_L_cm
                        y0 = c * secondary_W_cm
                        z0 = s * secondary_D_cm
                        x1 = x0 + secondary_L_cm
                        y1 = y0 + secondary_W_cm
                        z1 = z0 + secondary_D_cm

                        vertices_x = [x0, x1, x1, x0, x0, x1, x1, x0]
                        vertices_y = [y0, y0, y1, y1, y0, y0, y1, y1]
                        vertices_z = [z0, z0, z0, z0, z1, z1, z1, z1]

                        faces_i = [0, 0, 4, 4, 0, 1, 2, 2, 0, 3, 1, 5]
                        faces_j = [1, 2, 5, 6, 1, 2, 6, 7, 3, 7, 5, 6]
                        faces_k = [2, 3, 6, 7, 4, 5, 7, 4, 7, 4, 6, 2]

                        fig.add_trace(go.Mesh3d(
                            x=vertices_x,
                            y=vertices_y,
                            z=vertices_z,
                            i=faces_i,
                            j=faces_j,
                            k=faces_k,
                            color='saddlebrown',
                            opacity=0.9,
                            flatshading=True,
                            showlegend=False
                        ))

            fig.update_layout(
                scene=dict(
                    xaxis_title='Length (cm)',
                    yaxis_title='Width (cm)',
                    zaxis_title='Height (cm)',
                    aspectmode='data',
                    camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
                ),
                margin=dict(l=0, r=0, t=30, b=0),
                title=f"{name} 3D Layout"
            )

            st.plotly_chart(fig, use_container_width=True)

# --- Submission Section ---
if st.button("Submit Packaging Info", key="submit_btn"):
    submission = {
        "Material": material,
        "Dimensions": f"{primary_L}x{primary_W}x{primary_D} ({length_unit})",
        "Weight": f"{primary_weight} ({weight_unit})",
        "Supplier Name": supplier_name,
        "Supplier Code": supplier_code,
        "Contact": supplier_contact,
        "Email": supplier_email,
        "Phone": supplier_phone,
        "Fragile": fragile
    }
    st.session_state["submissions"].append(submission)
    st.success("Submission added!")

st.write("Current Submissions:")
st.dataframe(pd.DataFrame(st.session_state["submissions"]))
