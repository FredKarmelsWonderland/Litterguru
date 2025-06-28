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
        # Using the final table name from your provided code
        query = """
            SELECT *
            FROM `cat-litter-recommender.test_01.final_01`
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
    # --- Sort the dataframe by default ---
    if 'P_Odor_Blocking_T2_if_True' in df.columns:
        df = df.sort_values(by='P_Odor_Blocking_T2_if_True', ascending=False)

    st.sidebar.header('Filter Your Litter')
    
    # --- Define the filter widgets using expanders and checkboxes ---
    filter_widgets = {
        'Scent': 'Filter by Scent',
        'Flushable': 'Filter by Flushable',
        "Material Type": 'Filter by Material Type',
        'Mfg_Location': 'Filter by Product Origin'
    }
    
    # Start with a copy of the original dataframe
    filtered_df = df.copy()

    for col_name, label in filter_widgets.items():
        if col_name in df.columns:
            with st.sidebar.expander(label, expanded=False): # Set expanded=False to start collapsed
                # --- Sorting logic for options ---
                if col_name == 'Mfg_Location':
                    options = df[col_name].value_counts().index.tolist()
                else:
                    options = sorted(df[col_name].unique())
                
                selected_options = []
                for option in options:
                    # Create a unique key for each checkbox
                    if st.checkbox(option, key=f"{col_name}_{option}"):
                        selected_options.append(option)
                
            # Only apply this filter if the user has selected at least one option
            if selected_options:
                filtered_df = filtered_df[filtered_df[col_name].isin(selected_options)]
        else:
            st.sidebar.warning(f"Column '{col_name}' not found in the data.")


    # --- Multi-select for performance features (with user-friendly names) ---
    st.sidebar.markdown("AI-Analyzed Performance Attributes*")
    performance_feature_map = {
        'Good_Smell': 'Good Smell',
        'Odor_Blocking': 'Odor Blocking',
        'Low_Dust': 'Dust',
        'Low_Tracking': 'Tracking',
        'Ease_of_Cleaning': 'Easy to Clean'
    }

    # Filter the map to only include features that actually exist in the dataframe
    available_features_map = {
        raw_name: display_name 
        for raw_name, display_name in performance_feature_map.items() 
        if raw_name in df.columns
    }
    
    # The options for the dropdown are the user-friendly display names
    performance_display_options = list(available_features_map.values())

    selected_display_names = st.sidebar.multiselect(
        'Select Top Performers In:',
        options=performance_display_options,
        label_visibility="collapsed" # Hides the label to use the subheader above
    )
    
    # --- Filtering Logic for Performance Features ---
    # Create a reverse map to get the raw column name from the selected display name
    reverse_performance_map = {display_name: raw_name for raw_name, display_name in available_features_map.items()}
    
    # This ensures a product must have ALL selected performance features
    for selected_name in selected_display_names:
        raw_column_name = reverse_performance_map.get(selected_name)
        if raw_column_name and raw_column_name in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[raw_column_name] == 1]

    # --- Main Page Display ---
    st.title("Cat Litter Recommender 🐾")
    st.subheader("We use AI to analyze product reviews, helping you find the right litter!")
    
    # Display Cat Images from GitHub
    john_cute_url = "https://raw.githubusercontent.com/FredKarmelsWonderland/Litterguru/176ddfecd9034aec695e148c2840e207ef00b5b8/images/John%20cute.png"
    both_sitting_url = "https://raw.githubusercontent.com/FredKarmelsWonderland/Litterguru/main/images/Both%20cats%20sitting.png"
    tien_sleep_url = "https://raw.githubusercontent.com/FredKarmelsWonderland/Litterguru/176ddfecd9034aec695e148c2840e207ef00b5b8/images/Tien%20sleeping.png"

    col1, col2, col3 = st.columns(3)
    with col1:
        st.image(john_cute_url, width=100)
    with col2:
        st.image(both_sitting_url, width=100)
    with col3:
        st.image(tien_sleep_url, width=150)
    
    st.markdown(f"**Found {len(filtered_df)} matching products.**")
    st.markdown(f"Attributes such as Odor, etc. presented as a rating score*. Click column headers to sort!")
    
    # --- Define the columns to display and their new, shorter names ---
    display_column_map = {
        'Amazon_Product': 'Product Name',
        'Composition': 'Composition',
        'Amazon_url': 'Product Link',
        'Mean_Odor_Block_if_True': 'Odor Control',
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

    # --- Reverting to st.dataframe for interactivity ---
    st.dataframe(
        display_df,
        hide_index=True,
        column_config={
            "Product Link": st.column_config.LinkColumn(
                "Product Link",
                display_text="Go to Amazon"
            ),
            # Add number formatting for rating columns
            "Odor Control": st.column_config.NumberColumn(format="%.1f ⭐"),
            "Tracking": st.column_config.NumberColumn(format="%.1f ⭐"),
            "Dustiness": st.column_config.NumberColumn(format="%.1f ⭐"),
            "Cleaning Ease": st.column_config.NumberColumn(format="%.1f ⭐")
        }
    )

    # --- Add Feedback Email at the Bottom ---
    st.markdown("---")
    st.markdown("*Average rating scores determined by AI sentiment analysis (Gemini 2.5 Pro) on thousands of online reviews*")
    st.markdown("*Top performers = At least 75% of ratings for this attribute are determined to be 4 or 5 on a 5-point scale*")
    st.markdown("https://github.com/FredKarmelsWonderland")
else:
    # This message will show if load_data() failed and returned an empty dataframe
    st.warning("Could not load data. Please check the error messages above.")
