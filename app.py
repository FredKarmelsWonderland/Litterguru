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
            FROM `cat-litter-recommender.test_01.test_table_03`
        """
        # st.info("Querying data from Google BigQuery... this may take a moment.")
        query_job = client.query(query)
        df = query_job.to_dataframe()
        # st.success("Data successfully loaded from BigQuery!")
        
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
    st.sidebar.header("Pick what's important to you")

    # Create a list to hold the boolean filters from pandas
    active_filters = []

    # --- Dropdown multi-selects for categorical data with safety checks ---
    # Define the filter widgets
    filter_widgets = {
        'Scent': 'Filter by Scent:',
        'Flushable': 'Filter by Flushability:',
        'Composition': 'Filter by Composition:',
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
        'Odor_Blocking', 'Low_Dust','Low_Tracking', 
        'Good_Clumping', 'Ease_of_Cleaning']
    
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
            # CORRECTED LOGIC: Check for rows where the value is 1
            filtered_df = filtered_df[filtered_df[feature] == 1]


    # --- Main Page Display ---
    st.title("Cat Litter Recommendations 🐾")
    
    # Display Cat Images from GitHub
    john_cute_url = "https://raw.githubusercontent.com/FredKarmelsWonderland/Litterguru/176ddfecd9034aec695e148c2840e207ef00b5b8/images/John%20cute.png"
    tien_sleep_url = "https://raw.githubusercontent.com/FredKarmelsWonderland/Litterguru/176ddfecd9034aec695e148c2840e207ef00b5b8/images/Tien%20sleeping.png"

    col1, col2 = st.columns([0.5, 1, 1, 0.5])[1:3] # Use middle two columns
    with col1:
        st.image(john_cute_url, width = 150)
    with col2:
        st.image(tien_sleep_url, width = 200)

    st.write("Use the filters on the left to narrow down your choices.")
    
    st.markdown(f"**Found {len(filtered_df)} matching products**")
    
 # --- Define the columns to display and their new, shorter names with line breaks ---
    display_column_map = {
        'Amazon_Product': 'Product Name',
        'AMZN_url': 'Product Link',
        'Mean_Odor_Block_if_True': 'Odor\nBlock\nRating',
        'Mean_Clumping_if_True': 'Clumping\nRating',
        'Mean_Tracking_if_True': 'Tracking\nRating',
        'Mean_Dust_if_True': 'Dust\nRating',
        'Mean_Cleaning_if_True': "Ease of\nCleaning\nRating"
        # Add other 'Original_Column_Name': 'New_Display_Name' pairs here
    }
    
    # Get the list of original column names we want to display
    columns_to_show = list(display_column_map.keys())
    
    # Ensure all selected columns exist in the filtered dataframe before proceeding
    existing_display_columns = [col for col in columns_to_show if col in filtered_df.columns]
    
    # Create a new dataframe for display purposes, with only the existing columns
    display_df = filtered_df[existing_display_columns]
    
    # Rename the columns for the final display
    display_df = display_df.rename(columns=display_column_map)

    st.dataframe(
        display_df, # CORRECTED: Use the new, renamed dataframe for display
        hide_index=True,
        # Configure the URL column to be a clickable link, using its NEW name
        column_config={
            "Product Link": st.column_config.LinkColumn(
                "Product Link",
                display_text="Go to Amazon"
            )
        }
    )

 # --- Add Feedback Email at the Bottom ---
    st.markdown("---")
    st.markdown("For questions or feedback, please contact: [maxyen123@gmail.com](mailto:maxyen123@gmail.com)")

else:
    # This message will show if load_data() failed and returned an empty dataframe
    st.warning("Could not load data. Please check the error messages above.")





