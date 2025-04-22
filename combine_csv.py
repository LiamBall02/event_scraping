import pandas as pd
import glob

# Get all CSV files matching the pattern attendees[1-6].csv and sort in reverse
csv_files = sorted(glob.glob('attendees[1-6].csv'), reverse=True)

# Initialize an empty list to store DataFrames
dfs = []

# Read each CSV file and append to the list (will process from 6 to 1)
for csv_file in csv_files:
    df = pd.read_csv(csv_file)
    dfs.append(df)

# Combine all DataFrames into one (now in reverse order)
combined_df = pd.concat(dfs[::-1], ignore_index=True)

# Save the combined DataFrame to a new CSV file
combined_df.to_csv('attendees.csv', index=False)

print(f"Combined {len(csv_files)} CSV files into attendees.csv (starting with attendees1)")
