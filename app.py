import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
from io import BytesIO

# --- App Config ---
st.set_page_config(page_title="📦 Supplier Packaging Portal", layout="wide")

# --- Mock Authentication ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["role"] = "Supplier"

if not st.session_state["authenticated"]:
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["Supplier", "Admin"])
    if st.button("Login"):
        if username and password:
            st.session_state["authenticated"] = True
            st.session_state["role"] = role
            st.success(f"Logged in as {role}")
        else:
            st.error("Please enter username and password")
    st.stop()

# --- Session State for Submissions ---
if "submissions" not in st.session_state:
    st.session_state["submissions"] = []

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Packaging Info", "Analytics", "Export", "API Simulation"])

# --- Conversion Functions ---
def cm_to_in(cm): return cm / 2.54
def in_to_cm(inch): return inch * 2.54
def kg_to_lb(kg): return kg * 2.20462
def lb_to_kg(lb): return lb / 2.20462

# --- Sustainability Score ---
def calculate_sustainability_score(indicators):
    score = len(indicators) * 33  # Each indicator adds 33 points
    return min(score, 100)

# --- Cost Estimation ---
def estimate_cost(material, weight):
    base_cost = {"Corrugated": 0.5, "Plastic": 0.8, "Metal": 1.2, "Other": 0.6}
    return round(base_cost.get(material, 0.6) * weight, 2)

# --- Page: Packaging Info ---
if page == "Packaging Info":
    st.title("📦 Packaging Information")

    unit_system = st.radio("Unit System", ["Metric (cm/kg)", "Imperial (in/lb)"])
    length_unit = "cm" if unit_system.startswith("Metric") else "in"
    weight_unit = "kg" if unit_system.startswith("Metric") else "lb"

    supplier_name = st.text_input("Supplier Name")
    material = st.selectbox("Material Type", ["Corrugated", "Plastic", "Metal", "Other"])
    sustainability = st.multiselect("Sustainability Indicators", ["Recyclable", "Reusable", "Biodegradable"])

    st.subheader("Primary Dimensions")
    primary_L = st.number_input(f"Length ({length_unit})", min_value=0.0)
    primary_W = st.number_input(f"Width ({length_unit})", min_value=0.0)
    primary_D = st.number_input(f"Depth ({length_unit})", min_value=0.0)

    st.subheader("Secondary (Pallet) Dimensions")
    secondary_L = st.number_input(f"Pallet Length ({length_unit})", min_value=0.0)
    secondary_W = st.number_input(f"Pallet Width ({length_unit})", min_value=0.0)
    secondary_D = st.number_input(f"Pallet Height ({length_unit})", min_value=0.0)

    quantity_primary = st.number_input("Quantity per Primary Container", min_value=1)
    primary_weight = st.number_input(f"Primary Loaded Weight ({weight_unit})", min_value=0.0)

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

    # Pallet calculation
    if primary_L_cm > 0 and primary_W_cm > 0 and primary_D_cm > 0 and secondary_L_cm > 0 and secondary_W_cm > 0 and secondary_D_cm > 0:
        boxes_per_layer = int(secondary_L_cm // primary_L_cm) * int(secondary_W_cm // primary_W_cm)
        layers = int(secondary_D_cm // primary_D_cm)
        total_boxes_per_pallet = boxes_per_layer * layers
        quantity_secondary = total_boxes_per_pallet * quantity_primary
        st.write(f"Boxes per layer: {boxes_per_layer}, Layers: {layers}, Total boxes per pallet: {total_boxes_per_pallet}")
    else:
        total_boxes_per_pallet = 0
        quantity_secondary = 0

    # Secondary weight calculation
    pallet_weight_lb = 25
    pallet_weight_kg = pallet_weight_lb / 2.20462
    secondary_weight = (primary_weight * total_boxes_per_pallet) + (pallet_weight_lb if unit_system.startswith("Imperial") else pallet_weight_kg)

    st.number_input(f"Secondary Loaded Weight ({weight_unit})", value=secondary_weight, disabled=True)

    # Sustainability score
    score = calculate_sustainability_score(sustainability)
    st.progress(score)
    st.write(f"Sustainability Score: {score}%")

    # Cost estimation
    estimated_cost = estimate_cost(material, primary_weight)
    st.write(f"Estimated Packaging Cost: ${estimated_cost}")

    # Image upload
    primary_img = st.file_uploader("Upload Primary Packaging Image", type=["jpg", "jpeg", "png"])
    if primary_img:
        st.image(primary_img, caption="Primary Packaging Preview", use_column_width=True)

    # Submit button
    if st.button("Submit Packaging Info"):
        if not supplier_name or primary_weight <= 0:
            st.error("Please fill all required fields")
        else:
            submission = {
                "Supplier Name": supplier_name,
                "Material": material,
                "Dimensions": f"{primary_L}x{primary_W}x{primary_D} ({length_unit})",
                "Weight": primary_weight,
                "Quantity per Primary": quantity_primary,
                "Quantity per Secondary": quantity_secondary,
                "Secondary Weight": secondary_weight,
                "Sustainability Score": score,
                "Estimated Cost": estimated_cost
            }
            st.session_state["submissions"].append(submission)
            st.success("Submission added!")

# --- Page: Analytics ---
if page == "Analytics":
    st.title("📊 Analytics")
    if st.session_state["submissions"]:
        df = pd.DataFrame(st.session_state["submissions"])
        st.dataframe(df)
        fig = px.bar(df, x="Supplier Name", y="Sustainability Score", title="Sustainability Scores")
        st.plotly_chart(fig)
    else:
        st.info("No submissions yet")

# --- Page: Export ---
if page == "Export":
    st.title("Export Data")
    if st.session_state["submissions"]:
        df = pd.DataFrame(st.session_state["submissions"])
        st.download_button("Download CSV", df.to_csv(index=False), "submissions.csv")
        to_excel = BytesIO()
        df.to_excel(to_excel, index=False)
        st.download_button("Download Excel", to_excel.getvalue(), "submissions.xlsx")
        st.download_button("Download JSON", json.dumps(st.session_state["submissions"]), "submissions.json")
    else:
        st.info("No data to export")

# --- Page: API Simulation ---
if page == "API Simulation":
    st.title("API Simulation")
    st.write("POST /api/submit-packaging")
    if st.button("Simulate API Call"):
        st.json(st.session_state["submissions"])
