import streamlit as st
import pandas as pd
import os

# --- Page Configuration ---
# Must be the first Streamlit command in your script
st.set_page_config(
    page_title="Cat Litter Recommender",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --- Data Loading ---
# Caching the data loading function for performance
@st.cache_data
def load_data(file_path):
    """Loads the CSV data from the given file path."""
    if not os.path.exists(file_path):
        st.error(f"File not found: {file_path}. Please make sure the CSV is in the same folder as app.py.")
        return pd.DataFrame() # Return empty dataframe if file doesn't exist
    try:
        data = pd.read_csv(file_path)
        # Data cleaning/preparation can be done here if needed
        # For example, ensuring binary columns are consistent
        data['Flushable'] = data['Flushable'].astype(str).str.strip().str.capitalize()
        data['Scented'] = data['Scented'].astype(str).str.strip().str.capitalize()
        return data
    except Exception as e:
        st.error(f"An error occurred while loading the data: {e}")
        return pd.DataFrame()

def create_sample_csv():
    """Creates a sample CSV file for demonstration if one doesn't exist."""
    sample_data = {
        'Product Name': [f'Litter Brand {chr(65+i)}' for i in range(12)],
        'Flushable': ['Yes', 'No', 'Yes', 'No', 'Yes', 'No', 'Yes', 'No', 'Yes', 'No', 'Yes', 'No'],
        'Material': ['Corn', 'Clay', 'Walnut', 'Silica', 'Corn', 'Clay', 'Walnut', 'Silica', 'Corn', 'Clay', 'Walnut', 'Silica'],
        'Mfg Location': ['USA', 'China', 'Canada', 'USA', 'China', 'Canada', 'USA', 'China', 'Canada', 'USA', 'China', 'Canada'],
        'Scented': ['No', 'Yes', 'No', 'Yes', 'No', 'Yes', 'No', 'Yes', 'No', 'Yes', 'No', 'Yes'],
        'Mean_Scraped_Rating': [4.5, 3.2, 4.8, 2.5, 4.6, 3.9, 4.9, 3.1, 4.2, 2.8, 4.7, 3.5],
        'Good Clumping': [True, True, False, False, True, True, True, False, True, True, False, False],
        'Good Odor Blocking': [True, False, True, True, True, False, True, True, False, False, True, True]
    }
    df = pd.DataFrame(sample_data)
    df.to_csv('my_data.csv', index=False)
    st.info("Sample 'my_data.csv' created. Please refresh the page.")


# --- Main App ---
# Check for CSV file and create a sample if it doesn't exist
if not os.path.exists('my_data.csv'):
    st.title("Welcome to the Cat Litter Recommender! 🐾")
    st.write("It looks like you don't have a `my_data.csv` file yet.")
    st.write("Click the button below to create a sample CSV to get started. You can replace this with your own data later.")
    if st.button("Create Sample `my_data.csv`"):
        create_sample_csv()
else:
    # Load the data
    df = load_data('my_data.csv')

    if not df.empty:
        # --- Sidebar Filters ---
        st.sidebar.header('Filter and Sort Options')

        # Dropdown multi-selects for categorical data
        flushable_options = st.sidebar.multiselect(
            'Is it Flushable?',
            options=df['Flushable'].unique(),
            default=df['Flushable'].unique() # Default to all selected
        )

        material_options = st.sidebar.multiselect(
            'Litter Material:',
            options=df['Material'].unique(),
            default=df['Material'].unique()
        )

        location_options = st.sidebar.multiselect(
            'Manufacturing Location:',
            options=df['Mfg Location'].unique(),
            default=df['Mfg Location'].unique()
        )

        scented_options = st.sidebar.multiselect(
            'Is it Scented?',
            options=df['Scented'].unique(),
            default=df['Scented'].unique()
        )

        # Slider for the numeric rating
        rating_range = st.sidebar.slider(
            'Average Scraped Rating:',
            min_value=float(df['Mean_Scraped_Rating'].min()),
            max_value=float(df['Mean_Scraped_Rating'].max()),
            value=(float(df['Mean_Scraped_Rating'].min()), float(df['Mean_Scraped_Rating'].max())) # A tuple for range
        )

        # Multi-select for performance features (maps to boolean columns)
        performance_options = st.sidebar.multiselect(
            'Performance Features:',
            options=['Good Clumping', 'Good Odor Blocking']
        )

        # --- Filtering Logic ---
        # Start with the original dataframe and apply filters sequentially
        filtered_df = df[
            (df['Flushable'].isin(flushable_options)) &
            (df['Material'].isin(material_options)) &
            (df['Mfg Location'].isin(location_options)) &
            (df['Scented'].isin(scented_options)) &
            (df['Mean_Scraped_Rating'].between(rating_range[0], rating_range[1]))
        ]

        # Handle the special performance filter
        # This logic shows products that have ALL selected performance features (AND logic)
        # To change to OR logic (has AT LEAST ONE), you would need a more complex filter.
        if 'Good Clumping' in performance_options:
            filtered_df = filtered_df[filtered_df['Good Clumping'] == True]
        
        if 'Good Odor Blocking' in performance_options:
            filtered_df = filtered_df[filtered_df['Good Odor Blocking'] == True]


        # --- Main Page Display ---
        st.title("Cat Litter Recommendations")
        st.write("Use the filters on the left to narrow down your choices.")
        
        # Display the number of results found
        st.markdown(f"**Found {len(filtered_df)} matching products**")
        st.dataframe(
            filtered_df,
            # Hide the index column from the displayed dataframe
            hide_index=True,
            # You can also set column widths or other configurations here
            # column_config={ ... }
        )


