import streamlit as st
import pandas as pd
import numpy as np # Import numpy for the cleaning step
from google.cloud import bigquery
from google.oauth2 import service_account

# --- Page Configuration ---
# Must be the first Streamlit command in your script
st.set_page_config(
    page_title="Cat Litter Recommender",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Data Loading Function (from BigQuery) ---
# Caching the data loading function for performance
@st.cache_data
def load_data():
    """Loads data from Google BigQuery and prepares it for the app."""
    try:
        # Use st.secrets to get the credentials from your secrets.toml file
        creds = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
        client = bigquery.Client(credentials=creds, project=creds.project_id)

        # Define your query here
        # Using the final table name from your provided code
        query = """
            SELECT *
            FROM `cat-litter-recommender.test_01.final_02`
        """
        query_job = client.query(query)
        df = query_job.to_dataframe()
        
        # --- Data Cleaning and Preparation ---
        # List of columns that should be treated as boolean-like (1/0)
        performance_cols = [
            'Good_Smell', 'Odor_Blocking', 'Low_Dust', 
            'Low_Tracking', 'Cat_Acceptance', 'Safety', 'Ease_of_Cleaning'
        ]

        for col in performance_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        
        # Ensure categorical columns are strings and handle potential NA values
        categorical_cols = ['Scent', 'Flushable', 'Material Type', 'Mfg_Location', 'Health_Monitoring', 'Eco_friendly', 'Clumping', 'Qty']
        for col in categorical_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).fillna('N/A')
        
        # Ensure numeric columns are numeric
        numeric_cols = ['Size', 'Current_Price']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')


        return df

    except Exception as e:
        st.error(f"An error occurred while connecting to BigQuery: {e}")
        st.info("Please ensure your `gcp_service_account` secret is correctly configured and the BigQuery table exists.")
        return pd.DataFrame()


# --- Main App Logic ---
df = load_data()

# Only build the rest of the app if the dataframe was loaded successfully
if not df.empty:
    # --- Sort the dataframe by default ---
    if 'Mean_Performance' in df.columns:
        df = df.sort_values(by='Mean_Performance', ascending=False)

    st.sidebar.header('Litter Type')
    
    # Start with a copy of the original dataframe
    filtered_df = df.copy()

    # --- Create a single toggleable expander for all filters ---
    with st.sidebar.expander("Apply Filters", expanded=False):
        
        # --- Nested expander for Attributes ---
        with st.expander("Attributes", expanded=False):
            is_flushable = st.checkbox("Flushable", key="flush_yes")
            is_not_flushable = st.checkbox("Not Flushable", key="flush_no")
            is_scented = st.checkbox("Scented", key="scent_yes")
            is_unscented = st.checkbox("Unscented", key="scent_no")
            is_clumping = st.checkbox("Clumping", key = "clumping_yes")
            is_non_clumping = st.checkbox("Non-Clumping", key = "clumping_no")
            is_eco_friendly = st.checkbox("Eco-friendly", key="eco_yes")
            is_health_monitoring = st.checkbox("Health Monitoring", key="health_yes")

        # --- Nested expander for Material Type ---
        with st.expander("Material Type", expanded=False):
            selected_mat_options = []
            if 'Material Type' in df.columns:
                mat_options = sorted(df['Material Type'].unique())
                for option in mat_options:
                    if st.checkbox(option, key=f"mat_{option}"):
                        selected_mat_options.append(option)
            else:
                st.write("No 'Material Type' data available.")
        
        # --- Nested expander for Product Origin ---
        with st.expander("Product Origin", expanded=False):
            selected_loc_options = []
            if 'Mfg_Location' in df.columns:
                loc_options = df['Mfg_Location'].value_counts().index.tolist()
                for option in loc_options:
                    if st.checkbox(option, key=f"loc_{option}"):
                        selected_loc_options.append(option)
            else:
                st.write("No 'Product Origin' data available.")

        # --- Nested expander for Quantity ---
        with st.expander("Piece Count in Product", expanded=False):
            selected_qty_options = []
            if 'Qty' in df.columns:
                qty_options = sorted(pd.to_numeric(df['Qty'], errors='coerce').dropna().unique())
                for option in qty_options:
                    if st.checkbox(str(int(option)), key=f"qty_{option}"):
                        selected_qty_options.append(str(int(option)))
            else:
                st.write("No 'Quantity' data available.")

        # --- Sliders for Numeric Columns ---
        with st.expander("Size & Price", expanded=False):
            if 'Size' in df.columns:
                min_size = float(df['Size'].dropna().min())
                max_size = float(df['Size'].dropna().max())
                selected_size_range = st.slider(
                    'Filter by Size (lbs):',
                    min_value=min_size,
                    max_value=max_size,
                    value=(min_size, max_size)
                )
            else:
                selected_size_range = (0, 0)

            if 'Current_Price' in df.columns:
                min_price = float(df['Current_Price'].dropna().min())
                max_price = float(df['Current_Price'].dropna().max())
                selected_price_range = st.slider(
                    'Filter by Price ($):',
                    min_value=min_price,
                    max_value=max_price,
                    value=(min_price, max_price)
                )
            else:
                selected_price_range = (0, 0)


    # --- Filtering Logic ---
    # Apply attribute filters
    flushable_selections = [val for check, val in [(is_flushable, 'Flushable'), (is_not_flushable, 'Not Flushable')] if check]
    if flushable_selections: filtered_df = filtered_df[filtered_df['Flushable'].isin(flushable_selections)]
    
    scent_selections = [val for check, val in [(is_scented, 'Scented'), (is_unscented, 'Unscented')] if check]
    if scent_selections: filtered_df = filtered_df[filtered_df['Scent'].isin(scent_selections)]

    clumping_selections = [val for check, val in [(is_clumping, 'Clumping'), (is_non_clumping, 'Non-Clumping')] if check]
    if clumping_selections: filtered_df = filtered_df[filtered_df['Clumping'].isin(clumping_selections)]

    if is_eco_friendly: filtered_df = filtered_df[filtered_df['Eco_friendly'] == 'Eco-friendly']
    if is_health_monitoring: filtered_df = filtered_df[filtered_df['Health_Monitoring'] == 'Yes']

    # Apply other filters
    if selected_mat_options: filtered_df = filtered_df[filtered_df['Material Type'].isin(selected_mat_options)]
    if selected_loc_options: filtered_df = filtered_df[filtered_df['Mfg_Location'].isin(selected_loc_options)]
    if selected_qty_options: filtered_df = filtered_df[filtered_df['Qty'].isin(selected_qty_options)]
    
    if 'Size' in filtered_df.columns:
        if selected_size_range[0] > min_size or selected_size_range[1] < max_size:
            filtered_df = filtered_df[filtered_df['Size'].between(selected_size_range[0], selected_size_range[1])]
            
    if 'Current_Price' in filtered_df.columns:
        if selected_price_range[0] > min_price or selected_price_range[1] < max_price:
            filtered_df = filtered_df[filtered_df['Current_Price'].between(selected_price_range[0], selected_price_range[1])]


    # --- Main Page Display ---
    st.title("Cat Litter Recommender 🐾")
    st.subheader("We use AI to analyze product reviews, helping you find the right litter!")
    
    # Display Cat Images from GitHub
    john_cute_url = "https://raw.githubusercontent.com/FredKarmelsWonderland/Litterguru/176ddfecd9034aec695e148c2840e207ef00b5b8/images/John%20cute.png"
    both_sitting_url = "https://raw.githubusercontent.com/FredKarmelsWonderland/Litterguru/main/images/Both%20cats%20sitting.png"
    tien_sleep_url = "https://raw.githubusercontent.com/FredKarmelsWonderland/Litterguru/176ddfecd9034aec695e148c2840e207ef00b5b8/images/Tien%20sleeping.png"
    Lia_url = "https://raw.githubusercontent.com/FredKarmelsWonderland/Litterguru/main/images//Lia.png"

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.image(john_cute_url, width=100)
    with col2:
        st.image(both_sitting_url, width=100)
    with col3:
        st.image(tien_sleep_url, width=150)
    with col4:
        st.image(Lia_url, width=100)
    
    st.markdown(f"**Found {len(filtered_df)} matching products.**")
    
    # --- Define the columns to display and their new, shorter names ---
    display_column_map = {
        'Amazon_Product': 'Product Name',
        'Composition': 'Composition',
        'Size': 'Size (lbs)',
        'Qty': 'Quantity',
        'Current_Price': 'Price ($)',
        'Affiliate_url': 'Buy on Amazon',
        'P_Odor_Blocking_T2_if_True': 'Odor Control',
        'P_Tracking_T2_if_True': 'Tracking',
        'P_Dust_T2_if_True': 'Dustiness',
        'P_Cleaning_T2_if_True': "Cleaning Ease",
    }
    
    # --- Prepare Data for Display ---
    performance_rating_cols = [
        'P_Odor_Blocking_T2_if_True', 'P_Tracking_T2_if_True',
        'P_Dust_T2_if_True', 'P_Cleaning_T2_if_True'
    ]
    display_df_intermediate = filtered_df.copy()
    for col in performance_rating_cols:
        if col in display_df_intermediate.columns:
            display_df_intermediate[col] = pd.to_numeric(display_df_intermediate[col], errors='coerce').fillna(0) * 100

    columns_to_show = list(display_column_map.keys())
    existing_display_columns = [col for col in columns_to_show if col in display_df_intermediate.columns]
    
    if not existing_display_columns:
        st.warning("No data to display based on the selected columns.")
    else:
        display_df = display_df_intermediate[existing_display_columns]
        display_df = display_df.rename(columns=display_column_map)

        st.markdown("<p style='text-align: right; color: grey; padding-right: 8%;'>AI Sentiment Analysis, % Positive Reviews*</p>", unsafe_allow_html=True)

        st.dataframe(
            display_df,
            hide_index=True,
            column_config={
                "Buy on Amazon": st.column_config.LinkColumn("Buy on Amazon", display_text="Link"),
                "Product Name": st.column_config.TextColumn(width="large"),
                "Price ($)": st.column_config.NumberColumn(format="$%.2f"),
                "Odor Control": st.column_config.NumberColumn(format="%d%%"),
                "Tracking": st.column_config.NumberColumn(format="%d%%"),
                "Dustiness": st.column_config.NumberColumn(format="%d%%"),
                "Cleaning Ease": st.column_config.NumberColumn(format="%d%%")
            }
        )

    # --- Add Feedback Email at the Bottom ---
    st.markdown("---")
    st.markdown("*Percent positivity determined by AI sentiment analysis (Gemini 2.5 Pro) on thousands of online reviews*")
    st.markdown("*Top performers = At least 75% of ratings for this attribute are determined to be 4 or 5 on a 5-point scale*")
    st.markdown("https://github.com/FredKarmelsWonderland")
else:
    st.warning("Could not load data. Please check the error messages above.")


