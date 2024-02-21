import pandas as pd
import streamlit as st

df = pd.read_csv('C:/Users/sr0578/Downloads/part-00003-610c8f1e-7ecf-4a16-9334-fe7d183dab19-c000.csv')


#df = pd.read_csv('dispersiondata1.csv')



def main():
    st.title("Scheme Analysis Application")



    # Input for date range
    col1, col2 = st.columns(2)
    start_date = col1.date_input("Select Start Date:")
    end_date = col2.date_input("Select End Date:")



    # Convert start_date and end_date to Pandas datetime objects if a date is selected
    if start_date is not None:
        start_date = pd.to_datetime(start_date)
    if end_date is not None:
        end_date = pd.to_datetime(end_date)



    # Input for product_hier2_name and product_hier7_name
    col1, col2 = st.columns(2)
    selected_category = col1.selectbox("Select Category:", [''] + list(df['product_hier2_name'].unique()))
    available_products_7 = df[df['product_hier2_name'] == selected_category]['product_hier7_name'].unique()
    selected_product_7 = col2.selectbox("Select Brand (Level 2):", [''] + list(available_products_7))



    # Input for product_hier9_name (multi-select, third filter)
    available_products_9 = df[(df['product_hier2_name'] == selected_category) & (df['product_hier7_name'] == selected_product_7)]['product_hier9_name'].unique()
    selected_products_9 = st.multiselect("Select SKU (Grammage):", list(available_products_9))



    # Input for region (multi-select)
    available_regions = df['geo_hier5_name'].unique()
    selected_regions = st.multiselect("Select region(s) (optional, multi-select):", [''] + list(available_regions))
    
    # Input for retailer_sub_channel_name (multi-select, new filter)
    available_sub_channels = df['retailer_sub_channel_name'].unique()
    selected_sub_channels = st.multiselect("Select retailer sub channel(s) (optional, multi-select):", [''] + list(available_sub_channels))





    # Input for ASM and TSE
    col1, col2 = st.columns(2)
    if selected_regions:
        available_asms = df[df['geo_hier5_name'].isin(selected_regions)]['ASM'].unique()
    else:
        available_asms = df['ASM'].unique()



    selected_asms = col1.multiselect("Select ASM(s) (optional, multi-select):", [''] + list(available_asms))



    if selected_asms:
        available_tses = df[df['ASM'].isin(selected_asms)]['TSE'].unique()
    else:
        available_tses = df['TSE'].unique()



    selected_tses = col2.multiselect("Select TSE(s) (optional, multi-select):", [''] + list(available_tses))



    # Input for number of slabs
    num_slabs = st.number_input("Enter the number of slabs:", min_value=1, step=1)



    # Input for choosing between quantity and amount slabs
    slab_type = st.selectbox("Select Slab Type:", ["Quantity Slabs", "Amount Slabs"])



    # Input for slab ranges
    slab_ranges = []
    for i in range(num_slabs):
        slab_range = st.text_input(f"Enter the range for slab {i+1} (comma-separated):")
        if slab_range:
            slab_ranges.append(tuple(map(float, slab_range.replace('$', '').split(','))))
        else:
            # If input is empty, set a default range to cover all values
            slab_ranges.append((float('-inf'), float('inf')))



    # Automatically create the last slab based on the upper limit of the last defined slab
    if slab_ranges:
        upper_limit_last_slab = slab_ranges[-1][1]
        slab_ranges.append((upper_limit_last_slab, float('inf')))



    # Add a new input for forecasted volume
    forecasted_volume = st.number_input("Enter the forecasted volume:")



    # Button to trigger analysis
    if st.button("Run Analysis"):
        if slab_type == "Quantity Slabs":
            run_quantity_analysis(start_date, end_date, selected_category, selected_product_7, selected_products_9, selected_regions,selected_sub_channels,selected_asms, selected_tses, slab_ranges,forecasted_volume)
        elif slab_type == "Amount Slabs":
            run_amount_analysis(start_date, end_date, selected_category, selected_product_7, selected_products_9, selected_regions,selected_sub_channels,selected_asms, selected_tses, slab_ranges,forecasted_volume)



def categorize_quantity_slabs(quantity, slab_ranges):
    for i, slab in enumerate(slab_ranges):
        if slab[0] <= quantity <= slab[1]:
            return f"{slab[0]}-{slab[1]}" if slab[1] != float('inf') else f"Above {slab[0]}"
    return f"Above {slab_ranges[-1][1]}"



def run_quantity_analysis(start_date, end_date, selected_category, selected_product_7, selected_products_9,selected_regions,selected_sub_channels,selected_asms, selected_tses, slab_ranges,forecasted_volume):
    # Filter data based on user inputs
    filtered_data = df.copy()



    if selected_category:
        filtered_data = filtered_data[filtered_data['product_hier2_name'] == selected_category]



    if selected_product_7:
        filtered_data = filtered_data[filtered_data['product_hier7_name'] == selected_product_7]



    if selected_products_9:
        filtered_data = filtered_data[filtered_data['product_hier9_name'].isin(selected_products_9)]



    if selected_regions:
        filtered_data = filtered_data[filtered_data['geo_hier5_name'].isin(selected_regions)]
        
    if selected_sub_channels:
        filtered_data = filtered_data[filtered_data['retailer_sub_channel_name'].isin(selected_sub_channels)]



    if selected_asms:
        filtered_data = filtered_data[filtered_data['ASM'].isin(selected_asms)]



    if selected_tses:
        filtered_data = filtered_data[filtered_data['TSE'].isin(selected_tses)]



    # Convert 'invoice_date' to datetime format
    filtered_data['invoice_date'] = pd.to_datetime(filtered_data['invoice_date'])



    # Apply date range filter
    filtered_data = filtered_data[(filtered_data['invoice_date'] >= start_date) & (filtered_data['invoice_date'] <= end_date)]



    # Group by retailer and calculate aggregated values
    grouped_data = filtered_data.groupby('invoice_number').agg({
        'invoice_quantity_in_kg': 'sum',
        'gross_amount': 'sum',
        'SCHEME': 'sum'
    }).reset_index()



    # Categorize quantity into slabs
    grouped_data['quantity_slab'] = grouped_data['invoice_quantity_in_kg'].apply(lambda x: categorize_quantity_slabs(x, slab_ranges))



    # Calculate invoice count, total value, and total volume for each slab
    retailer_count = grouped_data.groupby('quantity_slab')['invoice_number'].nunique().reset_index()
    retailer_count.columns = ['quantity_slab', 'retailer_count']
    total_value = grouped_data.groupby('quantity_slab')['gross_amount'].sum().reset_index()
    total_volume = grouped_data.groupby('quantity_slab')['invoice_quantity_in_kg'].sum().reset_index()
    total_scheme_amount = grouped_data.groupby('quantity_slab')['SCHEME'].sum().reset_index()



    # Merge results into a final DataFrame
    final_result = pd.merge(retailer_count, total_value, on='quantity_slab', how='right')
    final_result = pd.merge(final_result, total_volume, on='quantity_slab', how='right')
    final_result = pd.merge(final_result, total_scheme_amount, on='quantity_slab', how='right')



    # Create the final result DataFrame
    test_result = pd.DataFrame()
    test_result['Slab_ranges'] = [f"{slab[0]}-{slab[1]}" if slab[1] != float('inf') else f"Above {slab[0]}" for slab in slab_ranges]
    test_result = pd.merge(test_result, final_result, how='left', left_on='Slab_ranges', right_on='quantity_slab')



    # Calculate percentages
    total_retailers = test_result['retailer_count'].sum()
    test_result['UIB'] = (
        test_result['retailer_count'].round(2).astype(str) +
        ' (' +
        (test_result['retailer_count'] / total_retailers * 100).round(2).astype(str) +
        '%)'
    )
    test_result['Value'] = (
        test_result['gross_amount'].round(2).astype(str) +
        ' (' +
        (test_result['gross_amount'] / test_result['gross_amount'].sum() * 100).round(2).astype(str) +
        '%)'
    )
    test_result['Volume'] = (
        test_result['invoice_quantity_in_kg'].round(2).astype(str) +
        ' (' +
        (test_result['invoice_quantity_in_kg'] / test_result['invoice_quantity_in_kg'].sum() * 100).round(2).astype(str) +
        '%)'
    )
    test_result['Scheme_Amount'] = (
        test_result['SCHEME'].round(2).astype(str) +
        ' (' +
        (test_result['SCHEME'] / test_result['SCHEME'].sum() * 100).round(2).astype(str) +
        '%)'
    )



    # Calculate forecasted volume for each slab
    if test_result['invoice_quantity_in_kg'].sum() != 0:
        test_result['Forecasted_Volume'] = test_result['invoice_quantity_in_kg'] / test_result['invoice_quantity_in_kg'].sum() * forecasted_volume
    else:
        test_result['Forecasted_Volume'] = 0



    # Fill NA values with 0 and format the 'Forecasted_Volume' column
    test_result['Forecasted_Volume'] = test_result['Forecasted_Volume'].fillna(0).round(0).astype(int)



    # Display the final result
    st.dataframe(test_result[['Slab_ranges', 'UIB', 'Value', 'Volume', 'Scheme_Amount','Forecasted_Volume']])



def categorize_amount_slabs(gross_amount, slab_ranges):
    for i, slab in enumerate(slab_ranges):
        if slab[0] <= gross_amount <= slab[1]:
            return f"${slab[0]}-${slab[1]}" if slab[1] != float('inf') else f"Above ${slab[0]}"
    return f"Above ${slab_ranges[-1][1]}"



def run_amount_analysis(start_date, end_date, selected_category, selected_product_7, selected_products_9, selected_regions,selected_sub_channels,selected_asms, selected_tses, slab_ranges,forecasted_volume):
    # Filter data based on user inputs
    filtered_data = df.copy()



    if selected_category:
        filtered_data = filtered_data[filtered_data['product_hier2_name'] == selected_category]



    if selected_product_7:
        filtered_data = filtered_data[filtered_data['product_hier7_name'] == selected_product_7]



    if selected_products_9:
        filtered_data = filtered_data[filtered_data['product_hier9_name'].isin(selected_products_9)]



    if selected_regions:
        filtered_data = filtered_data[filtered_data['geo_hier5_name'].isin(selected_regions)]
        
    if selected_sub_channels:
        filtered_data = filtered_data[filtered_data['retailer_sub_channel_name'].isin(selected_sub_channels)]



    if selected_asms:
        filtered_data = filtered_data[filtered_data['ASM'].isin(selected_asms)]



    if selected_tses:
        filtered_data = filtered_data[filtered_data['TSE'].isin(selected_tses)]



    # Convert 'invoice_date' to datetime format
    filtered_data['invoice_date'] = pd.to_datetime(filtered_data['invoice_date'])



    # Apply date range filter
    filtered_data = filtered_data[(filtered_data['invoice_date'] >= start_date) & (filtered_data['invoice_date'] <= end_date)]



    # Group by retailer and calculate aggregated values
    grouped_data = filtered_data.groupby('invoice_number').agg({
        'gross_amount': 'sum',
        'invoice_quantity_in_kg': 'sum',
        'SCHEME': 'sum'
    }).reset_index()



    # Categorize gross amount into slabs
    grouped_data['amount_slab'] = grouped_data['gross_amount'].apply(lambda x: categorize_amount_slabs(x, slab_ranges))



    # Calculate unique invoices, total value, and total volume for each slab
    unique_invoices = grouped_data.groupby('amount_slab')['invoice_number'].nunique().reset_index()
    unique_invoices.columns = ['amount_slab', 'unique_invoices']
    total_value = grouped_data.groupby('amount_slab')['gross_amount'].sum().reset_index()
    total_volume = grouped_data.groupby('amount_slab')['invoice_quantity_in_kg'].sum().reset_index()
    total_scheme_amount = grouped_data.groupby('amount_slab')['SCHEME'].sum().reset_index()



    # Merge results into a final DataFrame
    final_result = pd.merge(unique_invoices, total_value, on='amount_slab', how='right')
    final_result = pd.merge(final_result, total_volume, on='amount_slab', how='right')
    final_result = pd.merge(final_result, total_scheme_amount, on='amount_slab', how='right')



    # Create the final result DataFrame
    test_result = pd.DataFrame()
    test_result['Slab_ranges'] = [f"${slab[0]}-${slab[1]}" if slab[1] != float('inf') else f"Above ${slab[0]}" for slab in slab_ranges]
    test_result = pd.merge(test_result, final_result, how='left', left_on='Slab_ranges', right_on='amount_slab')



    # Calculate percentages
    total_invoices = test_result['unique_invoices'].sum()
    test_result['Unique_Invoices'] = (
        test_result['unique_invoices'].round(2).astype(str) +
        ' (' +
        (test_result['unique_invoices'] / total_invoices * 100).round(2).astype(str) +
        '%)'
    )
    test_result['Value'] = (
        test_result['gross_amount'].round(2).astype(str) +
        ' (' +
        (test_result['gross_amount'] / test_result['gross_amount'].sum() * 100).round(2).astype(str) +
        '%)'
    )
    test_result['Volume'] = (
        test_result['invoice_quantity_in_kg'].round(2).astype(str) +
        ' (' +
        (test_result['invoice_quantity_in_kg'] / test_result['invoice_quantity_in_kg'].sum() * 100).round(2).astype(str) +
        '%)'
    )
    test_result['Scheme_Amount'] = (
        test_result['SCHEME'].round(2).astype(str) +
        ' (' +
        (test_result['SCHEME'] / test_result['SCHEME'].sum() * 100).round(2).astype(str) +
        '%)'
    )



    # Calculate forecasted volume for each slab
    if test_result['invoice_quantity_in_kg'].sum() != 0:
        test_result['Forecasted_Volume'] = test_result['invoice_quantity_in_kg'] / test_result['invoice_quantity_in_kg'].sum() * forecasted_volume
    else:
        test_result['Forecasted_Volume'] = 0



    # Fill NA values with 0 and format the 'Forecasted_Volume' column
    test_result['Forecasted_Volume'] = test_result['Forecasted_Volume'].fillna(0).round(0).astype(int)





    # Display the final result
    st.dataframe(test_result[['Slab_ranges', 'Unique_Invoices', 'Value', 'Volume', 'Scheme_Amount', 'Forecasted_Volume']])

if __name__ == "__main__":
    main()
