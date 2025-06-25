import streamlit as st
import pandas as pd
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
        # Replace with your actual project_id, dataset_id, and table_id
        query = """
            SELECT *
            FROM `cat-litter-recommender.test_01.test_table_01`
        """
        st.info("Querying data from Google BigQuery... this may take a moment.")
        query_job = client.query(query)
        df = query_job.to_dataframe()
        st.success("Data successfully loaded from BigQuery!")
        
        # --- Perform initial data cleaning and preparation ---
        # List of columns that should be treated as boolean (Yes/"")
        boolean_like_cols = [
            'Good_Smell', 'Odor_Blocking', 'Low_Dust', 'Good_Clumping', 
            'Low_Tracking', 'Cat_Acceptance', 'Safety', 'Ease_of_Cleaning'
        ]
        
        # Convert "Yes" to True and other values (like blanks or NA) to False
        for col in boolean_like_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.lower() == 'yes'

        # Ensure categorical columns are strings and handle potential NA values
        categorical_cols = ['Scent', 'Composition', 'Flushable', 'Health_Monitoring', 'Mfg_Location']
        for col in categorical_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).fillna('N/A')

        return df

    except Exception as e:
        st.error(f"An error occurred while connecting to BigQuery: {e}")
        st.info("Please ensure your `gcp_service_account` secret is correctly configured and the BigQuery table exists.")
        return pd.DataFrame()


# --- Main App Logic ---
df = load_data()

# Only build the rest of the app if the dataframe was loaded successfully
if not df.empty:
    st.sidebar.header('Filter Your Litter')

    # Create a list to hold the boolean filters from pandas
    active_filters = []

    # --- Dropdown multi-selects for categorical data with safety checks ---
    # Define the filter widgets
    filter_widgets = {
        'Scent': 'Filter by Scent:',
        'Composition': 'Filter by Composition:',
        'Flushable': 'Filter by Flushable:',
        'Health_Monitoring': 'Filter by Health Monitoring:',
        'Mfg_Location': 'Filter by Manufacturing Location:'
    }

    for col_name, label in filter_widgets.items():
        if col_name in df.columns:
            options = sorted(df[col_name].unique())
            selected_options = st.sidebar.multiselect(
                label,
                options=options,
                default=options  # Default to all selected
            )
            active_filters.append(df[col_name].isin(selected_options))
        else:
            st.sidebar.warning(f"Column '{col_name}' not found in the data.")


    # --- Multi-select for performance features ---
    performance_features_available = [
        'Good_Smell', 'Odor_Blocking', 'Low_Dust', 'Good_Clumping', 
        'Low_Tracking', 'Cat_Acceptance', 'Safety', 'Ease_of_Cleaning'
    ]
    
    # Filter list to only include columns that actually exist in the dataframe
    performance_features_in_data = [col for col in performance_features_available if col in df.columns]

    performance_options = st.sidebar.multiselect(
        'Select Performance Features:',
        options=performance_features_in_data
    )
    
    # --- Filtering Logic ---
    # Start with all rows being included
    combined_filter = pd.Series([True] * len(df)) 
    
    # Combine all active filters using a logical AND (&)
    for f in active_filters:
        combined_filter = combined_filter & f
    
    # Apply the combined filter to the dataframe
    filtered_df = df[combined_filter]

    # Handle the special performance filter (AND logic)
    # This ensures a product must have ALL selected performance features
    for feature in performance_options:
        if feature in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[feature] == True]


    # --- Main Page Display ---
    st.title("Cat Litter Recommendations 🐾")
    
    # --- Display Cat Images ---
    john_cute_url = "https://raw.githubusercontent.com/FredKarmelsWonderland/Litterguru/176ddfecd9034aec695e148c2840e207ef00b5b8/images/John%20cute.png"
    tien_sleep_url = "https://raw.githubusercontent.com/FredKarmelsWonderland/Litterguru/176ddfecd9034aec695e148c2840e207ef00b5b8/images/Tien%20sleeping.png"

    col1, col2 = st.columns(2)
    with col1:
        st.image(john_cute_url, width=100)
    with col2:
        st.image(tien_sleep_url, width=100)

    st.write("Use the filters on the left to narrow down your choices.")
    
    st.markdown(f"**Found {len(filtered_df)} matching products**")
    
    # --- Define the columns to display in the final table ---
    display_columns = ['Amazon_Product', 'review_count', 'AMZN_url']
    
    # Ensure all display columns exist before trying to show them
    existing_display_columns = [col for col in display_columns if col in filtered_df.columns]
    
    st.dataframe(
        filtered_df[existing_display_columns],
        hide_index=True,
        # Configure the URL column to be a clickable link
        column_config={
            "AMZN_url": st.column_config.LinkColumn(
                "Product Link",
                display_text="Go to Amazon"
            )
        }
    )
else:
    # This message will show if load_data() failed and returned an empty dataframe
    st.warning("Could not load data. Please check the error messages above.")

