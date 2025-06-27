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
            FROM `cat-litter-recommender.test_01.final_01`
        """
        # st.info("Querying data from Google BigQuery... this may take a moment.")
        query_job = client.query(query)
        df = query_job.to_dataframe()
        # st.success("Data successfully loaded from BigQuery!")

         # --- Data Cleaning and Preparation ---
        # List of columns that should be treated as boolean-like (1/0)
        performance_cols = [
            'Good_Smell', 'Odor_Blocking', 'Low_Dust', 'Good_Clumping', 
            'Low_Tracking', 'Cat_Acceptance', 'Safety', 'Ease_of_Cleaning'
        ]

        for col in performance_cols:
            if col in df.columns:
                # Convert column to numeric, coercing errors to NaN, then fill NaN with 0, then cast to integer.
                # This ensures the column contains only 1s and 0s.
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        
        # Ensure categorical columns are strings and handle potential NA values
        categorical_cols = ['Scent', 'Flushable', 'Material Type', 'Mfg_Location']
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
 # --- Sort the dataframe by P_Odor_Blocking_T2_if_True by default ---
    if 'P_Odor_Blocking_T2_if_True' in df.columns:
        df = df.sort_values(by='P_Odor_Blocking_T2_if_True', ascending=False)

    st.sidebar.header('Filter Your Litter')
    
    # --- DEBUGGING: Display actual column names from BigQuery ---
    st.sidebar.subheader("Available Data Columns:")
    # ---

    # --- Dropdown multi-selects for categorical data with safety checks ---
    # Define the filter widgets
    filter_widgets = {
        'Scent': 'Filter by Scent:',
        # 'Composition': 'Filter by Composition:',
        'Flushable': 'Filter by Flushable:',
        "Material Type": 'Filter by Material Type',
        # 'Health_Monitoring': 'Filter by Health Monitoring:',
        'Mfg_Location': 'Filter by Product Origin:'
    }
    
    # CORRECTED LOGIC: Start with a copy of the original dataframe
    filtered_df = df.copy()

    for col_name, label in filter_widgets.items():
        if col_name in df.columns:
            # --- MODIFIED LOGIC FOR SORTING OPTIONS ---
            if col_name == 'Mfg_Location':
                # For Mfg_Location, sort options by frequency (most common first)
                options = df[col_name].value_counts().index.tolist()
            else:
                # For all other filters, sort alphabetically
                options = sorted(df[col_name].unique())
            
            # Set default=[] to have the dropdown empty initially
            selected_options = st.sidebar.multiselect(
                label,
                options=options,
                default=[] 
            )
            # Only apply this filter if the user has selected at least one option
            if selected_options:
                # CORRECTED LOGIC: Apply the filter to the already-filtered dataframe
                filtered_df = filtered_df[filtered_df[col_name].isin(selected_options)]
        else:
            st.sidebar.warning(f"Column '{col_name}' not found in the data.")


    # --- Multi-select for performance features ---
    performance_features_available = [
        'Odor_Blocking', 'Low_Dust', 'Good_Clumping', 
        'Low_Tracking', 'Cat_Acceptance', 'Ease_of_Cleaning'
    ]
    
    # Filter list to only include columns that actually exist in the dataframe
    performance_features_in_data = [col for col in performance_features_available if col in df.columns]

    performance_options = st.sidebar.multiselect(
        'Select Performance Features:',
        options=performance_features_in_data
        # The default is already an empty list when omitted, so no change needed here.
    )
    
    # --- Filtering Logic for Performance Features ---
    # This ensures a product must have ALL selected performance features
    for feature in performance_options:
        if feature in filtered_df.columns:
            # Check for rows where the value is 1
            filtered_df = filtered_df[filtered_df[feature] == 1]
    # --- Main Page Display ---
    st.title("Cat Litter Recommendations 🐾")
    st.subheader("We use AI to analyze >100,000 reviews, shortcutting you to the litter that meets your needs!")

    
    # Display Cat Images from GitHub
    john_cute_url = "https://raw.githubusercontent.com/FredKarmelsWonderland/Litterguru/176ddfecd9034aec695e148c2840e207ef00b5b8/images/John%20cute.png"
    both_sitting_url = "https://raw.githubusercontent.com/FredKarmelsWonderland/Litterguru/main/images/Both%20cats%20sitting.png"
    tien_sleep_url = "https://raw.githubusercontent.com/FredKarmelsWonderland/Litterguru/176ddfecd9034aec695e148c2840e207ef00b5b8/images/Tien%20sleeping.png"

    col1, col2, col3 = st.columns(3)
    with col1:
        st.image(john_cute_url, width = 100)
    with col2:
        st.image(both_sitting_url, width = 100)
    with col3:
        st.image(tien_sleep_url, width = 150)

    # st.write("Use the filters on the left to narrow down your choices.")
    
    st.markdown(f"**Found {len(filtered_df)} matching products.**")
    st.markdown(f"Attributes such as Odor, etc. presented as a rating score*.  Click column headers to sort!")
    
# --- Define the columns to display and their new, shorter names ---
    display_column_map = {
        'Amazon_Product': 'Product Name',
        'Amazon_url': 'Product Link',
        'Mean_Odor_Block_if_True': 'Odor Control',
        'Mean_Clumping_if_True': 'Clumping',
        'Mean_Tracking_if_True': 'Tracking',
        'Mean_Dust_if_True': 'Dustiness',
        'Mean_Cleaning_if_True': "Cleaning Ease"
    }
    
    # Get the list of original column names we want to display
    columns_to_show = list(display_column_map.keys())
    
    # Ensure all selected columns exist in the filtered dataframe before proceeding
    existing_display_columns = [col for col in columns_to_show if col in filtered_df.columns]
    
    # Create a new dataframe for display purposes, with only the existing columns
    display_df = filtered_df[existing_display_columns]
    
    # Rename the columns for the final display
    display_df = display_df.rename(columns=display_column_map)

    # Display the interactive dataframe, which allows sorting
    st.dataframe(
        display_df,
        hide_index=True,
        # Configure the URL column to be a clickable link, and format numeric columns
        column_config={
            "Product Link": st.column_config.LinkColumn(
                "Product Link",
                display_text="Go to Amazon"
            ),
            "Odor Block Rating": st.column_config.NumberColumn(format="%.1f"),
            "Clumping Rating": st.column_config.NumberColumn(format="%.1f"),
            "Tracking Rating": st.column_config.NumberColumn(format="%.1f"),
            "Dust Rating": st.column_config.NumberColumn(format="%.1f"),
            "Ease of Cleaning": st.column_config.NumberColumn(format="%.1f")
        }
    )

    

 # --- Add Feedback Email at the Bottom ---
    st.markdown("---")
    st.markdown("Average rating scores determined by AI sentiment analysis (Gemini 2.5 Pro) on thousands of online reviews")
    st.markdown("https://github.com/FredKarmelsWonderland")
else:
    # This message will show if load_data() failed and returned an empty dataframe
    st.warning("Could not load data. Please check the error messages above.")
