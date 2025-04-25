import pandas as pd
import glob
import os

# Get all CSV files in the directory
all_csv_files = sorted([f for f in os.listdir('.') if f.endswith('.csv')])

# Print available CSV files
print("Available CSV files:")
for idx, file in enumerate(all_csv_files, 1):
    print(f"{idx}. {file}")

# Get user input for range
try:
    start_idx = int(input("\nEnter start file number (1-{}): ".format(len(all_csv_files)))) - 1
    end_idx = int(input("Enter end file number (1-{}): ".format(len(all_csv_files)))) - 1
    
    # Validate input
    if not (0 <= start_idx < len(all_csv_files) and 0 <= end_idx < len(all_csv_files)):
        raise ValueError("Invalid file numbers")
    
    # Get selected files
    selected_files = all_csv_files[start_idx:end_idx + 1]
    
    # Initialize an empty list to store DataFrames
    dfs = []

    # Read each CSV file and append to the list
    for csv_file in selected_files:
        df = pd.read_csv(csv_file)
        dfs.append(df)

    # Combine all DataFrames into one
    combined_df = pd.concat(dfs, ignore_index=True)

    # Save the combined DataFrame to a new CSV file
    output_file = 'combined_output.csv'
    combined_df.to_csv(output_file, index=False)

    print(f"\nSuccessfully combined {len(selected_files)} CSV files into {output_file}")
    print("Combined files:", ", ".join(selected_files))

except ValueError as e:
    print("Error: Please enter valid numbers within the range")
except Exception as e:
    print(f"An error occurred: {str(e)}")
