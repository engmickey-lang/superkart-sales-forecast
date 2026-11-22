# SuperKart Sales Forecast - Streamlit frontend
import os

import pandas as pd
import requests
import streamlit as st

# Address of the Flask API. Inside the Docker network the API container is called "backend".
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:7860")

st.set_page_config(page_title="SuperKart Sales Forecast", layout="wide")
st.title("SuperKart Sales Forecast")
st.write(
    "Forecast the total sales revenue of a product in a SuperKart store. "
    "Use **Online prediction** for one product-store combination, or **Batch prediction** to score a CSV file."
)

tab_online, tab_batch = st.tabs(["Online prediction", "Batch prediction"])

# ------------------------------------------------------------------ online prediction
with tab_online:
    with st.form("online_form"):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Product")
            product_weight = st.number_input("Product weight", min_value=0.0, max_value=50.0, value=12.66, step=0.01)
            product_sugar = st.selectbox("Sugar content", ["Low Sugar", "Regular", "No Sugar"])
            product_area = st.number_input("Allocated display area (ratio of the store total)", min_value=0.0,
                                           max_value=1.0, value=0.027, step=0.001, format="%.3f")
            product_mrp = st.number_input("Maximum retail price (MRP)", min_value=0.0, max_value=1000.0, value=117.08, step=0.01)
            product_id_char = st.selectbox("Product family (Product ID prefix)", ["FD", "NC", "DR"],
                                           help="FD = food, NC = non-consumable, DR = drinks")
            product_category = st.selectbox("Product type category", ["Non Perishables", "Perishables"])
        with col2:
            st.subheader("Store")
            store_size = st.selectbox("Store size", ["Small", "Medium", "High"], index=1)
            store_city = st.selectbox("City tier", ["Tier 1", "Tier 2", "Tier 3"], index=1)
            store_type = st.selectbox("Store type", ["Supermarket Type1", "Supermarket Type2", "Departmental Store", "Food Mart"], index=1)
            store_age = st.number_input("Store age (years)", min_value=0, max_value=100, value=16, step=1)
            st.write("")
            result_slot = st.empty()  # the prediction appears here, beside the inputs, so it is visible without scrolling
        submitted = st.form_submit_button("Predict sales", type="primary")

    if submitted:
        payload = {
            "Product_Weight": product_weight,
            "Product_Sugar_Content": product_sugar,
            "Product_Allocated_Area": product_area,
            "Product_MRP": product_mrp,
            "Store_Size": store_size,
            "Store_Location_City_Type": store_city,
            "Store_Type": store_type,
            "Product_Id_char": product_id_char,
            "Store_Age_Years": int(store_age),
            "Product_Type_Category": product_category,
        }
        try:
            response = requests.post(f"{BACKEND_URL}/v1/predict", json=payload, timeout=30)
            if response.status_code == 200:
                prediction = response.json()["Predicted_Product_Store_Sales_Total"]
                result_slot.success(f"Predicted product-store sales total: {prediction:,.2f}")
                with st.expander("Request sent to the API"):
                    st.json(payload)
            else:
                result_slot.error(f"The API returned status {response.status_code}: {response.json().get('error', response.text)}")
        except requests.exceptions.RequestException as exc:
            result_slot.error(f"Could not reach the prediction API at {BACKEND_URL}: {exc}")

# ------------------------------------------------------------------ batch prediction
with tab_batch:
    st.write(
        "Upload a CSV file with these columns: Product_Weight, Product_Sugar_Content, Product_Allocated_Area, "
        "Product_MRP, Store_Size, Store_Location_City_Type, Store_Type, Product_Id_char, Store_Age_Years, "
        "Product_Type_Category."
    )
    uploaded = st.file_uploader("Batch CSV file", type=["csv"])
    if uploaded is not None:
        batch_df = pd.read_csv(uploaded)
        with st.expander(f"Preview of the uploaded file ({len(batch_df)} rows)"):
            st.dataframe(batch_df, use_container_width=True)

        if st.button("Predict batch", type="primary"):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/v1/predictbatch",
                    files={"file": (uploaded.name, uploaded.getvalue(), "text/csv")},
                    timeout=60,
                )
                if response.status_code == 200:
                    predictions = response.json()  # {"0": value, "1": value, ...}
                    result = batch_df.copy()
                    # put the prediction first so it is visible without scrolling the table sideways
                    result.insert(0, "Predicted_Product_Store_Sales_Total", [predictions[str(i)] for i in range(len(result))])
                    st.session_state["batch_result"] = result  # keep results across reruns (e.g. after download)
                else:
                    st.session_state.pop("batch_result", None)
                    st.error(f"The API returned status {response.status_code}: {response.json().get('error', response.text)}")
            except requests.exceptions.RequestException as exc:
                st.error(f"Could not reach the prediction API at {BACKEND_URL}: {exc}")

        if "batch_result" in st.session_state:
            result = st.session_state["batch_result"]
            total = result["Predicted_Product_Store_Sales_Total"].sum()
            st.success(f"Predicted {len(result)} rows. Total predicted revenue: {total:,.2f}")
            st.dataframe(result, use_container_width=True)
            st.download_button(
                "Download predictions as CSV",
                data=result.to_csv(index=False).encode("utf-8"),
                file_name="superkart_batch_predictions.csv",
                mime="text/csv",
            )
