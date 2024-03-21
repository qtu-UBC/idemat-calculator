import streamlit as st
import pandas as pd
import os


# Load the spreadsheet
@st.cache_data
def load_data(sheet_name):
    file_path = os.path.sep.join([os.getcwd(),'Idemat_2024-V1-2.xlsx'])
    data = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
    # Combine the text of the first three rows to create the new header
    new_header = data.iloc[0:3].apply(lambda x: '_'.join(x.dropna().astype(str)), axis=0)
    data.columns = new_header
    data.drop(index=[0,1,2], inplace=True)

    # data cleaning: 1) remove A-C columns and columns starts with 'Unnamed', 2) remove empty rows
    data.drop(data.columns[0:3], axis=1, inplace=True)
    # unnamed_col = [col for col in data.columns if col.startswith('Unnamed')]
    data.drop([col for col in data.columns if col.startswith('Unnamed')], axis=1, inplace=True)
    data.dropna(how='all', inplace=True)
    data.reset_index(drop=True, inplace=True)
    # print(data.columns)

    return data


# List of sheet names in the spreadsheet
sheet_names = ['Idemat2024', 'Idemat2024 midpoints']

# Streamlit app layout
st.title('Idemat Calculator')

# Dropdown for sheet selection
selected_sheet = st.selectbox('Select a sheet to view', sheet_names)

# Load the data from the selected sheet
data = load_data(selected_sheet)
# print(data['Category_._.'])

# Splitting the layout into three columns
col1, col2, col3 = st.columns(3)

# first column to show materials available for selection
with col1:
    st.header('Category')
    # [HARD-CODING] Assuming 'Category_._.' is the column of interest
    selected_category = st.selectbox('Select a cateogry', options=data['Category_._.'].unique())
    
# Initialize the session state for storing selections if it doesn't exist
if 'selected_items' not in st.session_state:
    st.session_state.selected_items = []

# second column to show corresponding processes available for a selected category
with col2:
    st.header('Select Process')
    if selected_category:
        category_data = data[data['Category_._.'].isin([selected_category])]
        processes = category_data['Process'].unique()
        selected_process = st.selectbox('Select a process', options=processes)

# third column to show the corresponding units available for a selected process
with col3:
    st.header('Select Unit')
    if selected_process:
        process_data = data[data['Process'].isin([selected_process])]
        units = process_data['unit'].unique()
        selected_unit = st.selectbox('Select a unit', options=units)

        # Button to add the selection to the session state
        if st.button('Add Selection'):
            st.session_state.selected_items.append({'Category': selected_category, 'Process': selected_process,
                'Unit': selected_unit})

# Display selections
st.header('Your Selections')


# Modify selections
if st.session_state.selected_items:
    for i, selection in enumerate(st.session_state.selected_items):
        # Check if 'Quantity' key exists for the selection, if not initialize it
        if 'Quantity' not in selection:
            selection['Quantity'] = '1'  # Initialize with a default value of '1'

        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.text(f"{selection['Process']}, {selection['Unit']}")
        with col2:
            # Define a unique key for the text input for quantity
            quantity_key = f"quantity_{i}"
            # Display the text input field with the current value from the session state
            # If the key doesn't exist, default to 1
            current_quantity = st.session_state.get(quantity_key, '1')
            # Update the session state with the new input from the user
            new_quantity = st.text_input('Quantity', value=current_quantity, key=quantity_key)
            # Update the session state only if the input is different
            if new_quantity != current_quantity:
                st.session_state[quantity_key] = new_quantity
            # update quantity of the selection
            selection['Quantity'] = new_quantity
        with col3:
            if st.button('Remove', key=f"remove_{i}"):
                # Remove the selection and the associated quantity
                st.session_state.selected_items.pop(i)
                if quantity_key in st.session_state:
                    del st.session_state[quantity_key]
                break
else:
    st.write('No selections made yet.')


# Calculation
# Sidebar for filters
st.sidebar.header('Impact Assessment Categories')
# Get all column headers from the DataFrame
column_headers = data.columns.tolist()
# User selects which columns (headers) filter by
selected_headers = st.sidebar.multiselect(
    'Select impact assessment categories', 
    options=column_headers, 
    default=column_headers[0]  # Optional: set default selected headers
)

# Filter data based on selection - Adjust this as necessary
final_headers = ['Category', 'Process'] + selected_headers 
filtered_data = data[[col for col in final_headers if col in data.columns]]

st.header('Calculate Impacts')

# Assuming data is structured with 'Process' as one column and each impact assessment category as other columns
# And st.session_state.selected_items is structured as a list of dicts with 'Category', 'Process', and 'Quantity'

# Function to perform the calculations
def calculate_total_impacts(selected_processes, selected_headers, data):
    # Convert selected materials to a DataFrame
    selected_processes_df = pd.DataFrame(selected_processes)
    
    # Ensure 'Quantity' is a numeric value
    selected_processes_df['Quantity'] = pd.to_numeric(selected_processes_df['Quantity'], errors='coerce').fillna(0)
    
    # Dictionary to hold the total results
    total_results = {category: 0 for category in selected_headers}
    
    # Iterate through each selected material and calculate the impacts
    for _, row in selected_processes_df.iterrows():
        for category in selected_headers:
            # Assuming each row in data has a 'Process' column and impact assessment values in other columns
            impact_value = data.loc[data['Process'] == row['Process'], category].values[0]
            total_results[category] += impact_value * row['Quantity']
    
    return total_results

# Button to trigger the calculation
if st.button('Calculate Total Impacts'):
    # Perform the calculation
    total_results = calculate_total_impacts(st.session_state.selected_items, selected_headers, filtered_data)
    
    # Convert the results to a DataFrame for display
    total_results_df = pd.DataFrame(list(total_results.items()), columns=['Impact Category', 'Total Impact'])
    
    # Display the results
    st.table(total_results_df)


# Additional features like exporting data can be added here
# Example: st.download_button('Export Data', data.to_csv().encode('utf-8'), 'data.csv', 'text/csv')

