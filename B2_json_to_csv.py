import json
import pandas as pd
import logging
from typing import List, Dict, Any, Set
import argparse
import re
import glob
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def extract_field_name(full_path: str) -> str:
    """
    Extract a user-friendly field name from a full JSON path
    
    Args:
        full_path: The full path to the field in dot notation
        
    Returns:
        A simplified field name
    """
    # Try to extract the actual field name from the path
    # First check if it's an array index pattern
    array_pattern = r'\.(\w+)\[\d+\]\.(\w+)$'
    match = re.search(array_pattern, full_path)
    if match:
        collection, field = match.groups()
        return f"{collection}_{field}"
    
    # Otherwise just get the last part after the dot
    parts = full_path.split('.')
    if len(parts) > 0:
        return parts[-1]
    
    return full_path

def flatten_json(nested_json: Any, prefix: str = '') -> Dict:
    """
    Flatten a nested JSON structure into a single-level dictionary.
    
    Args:
        nested_json: The nested JSON structure to flatten
        prefix: Optional prefix for flattened keys
        
    Returns:
        A flattened dictionary with dot-notation keys
    """
    flattened = {}
    
    # Handle different types of data
    if isinstance(nested_json, dict):
        for key, value in nested_json.items():
            new_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, (dict, list)):
                flattened.update(flatten_json(value, new_key))
            else:
                flattened[new_key] = value
                
    elif isinstance(nested_json, list):
        for i, item in enumerate(nested_json):
            new_key = f"{prefix}[{i}]"
            if isinstance(item, (dict, list)):
                flattened.update(flatten_json(item, new_key))
            else:
                flattened[new_key] = item
    else:
        flattened[prefix] = nested_json
        
    return flattened

def find_array_fields(data: Any) -> List[str]:
    """
    Find arrays in the JSON structure that might contain rows of data
    
    Args:
        data: The JSON data structure
        
    Returns:
        List of field paths to arrays that contain dictionaries
    """
    array_fields = []
    
    def search_arrays(obj, prefix=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_prefix = f"{prefix}.{key}" if prefix else key
                if isinstance(value, list) and value and isinstance(value[0], dict):
                    array_fields.append(new_prefix)
                search_arrays(value, new_prefix)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                search_arrays(item, f"{prefix}[{i}]")
    
    search_arrays(data)
    return array_fields

def extract_common_fields(data: Any) -> Dict[str, Set[str]]:
    """
    Find common field names in arrays of objects
    
    Args:
        data: The JSON data structure
        
    Returns:
        Dict mapping array paths to sets of field names
    """
    array_paths = find_array_fields(data)
    common_fields = {}
    
    for path in array_paths:
        # Navigate to the array
        array = data
        for part in path.split('.'):
            if '[' in part:
                key, idx = part.split('[')
                idx = int(idx.rstrip(']'))
                array = array[key][idx]
            else:
                array = array[part]
        
        # Skip if not a list
        if not isinstance(array, list):
            continue
            
        # Extract field names from each object in the array
        field_names = set()
        for item in array:
            if isinstance(item, dict):
                for key in item:
                    field_names.add(key)
        
        common_fields[path] = field_names
    
    return common_fields

def restructure_array_to_rows(data: Any, array_path: str, field_names: Set[str]) -> List[Dict]:
    """
    Convert an array of objects into a list of row dictionaries
    
    Args:
        data: The full JSON data structure
        array_path: Path to the array to extract
        field_names: Set of field names to extract
        
    Returns:
        List of dictionaries representing rows for the CSV
    """
    rows = []
    
    # Navigate to the array
    array = data
    path_parts = array_path.split('.')
    for part in path_parts:
        if '[' in part:
            key, idx = part.split('[')
            idx = int(idx.rstrip(']'))
            array = array[key][idx]
        else:
            array = array[part]
    
    # Extract values for each item in the array
    for item in array:
        if isinstance(item, dict):
            row = {}
            for field in field_names:
                row[field] = item.get(field, None)
            rows.append(row)
    
    return rows

def smart_restructure(data: Any) -> pd.DataFrame:
    """
    Intelligently restructure the JSON data into a DataFrame,
    detecting arrays of objects and converting them to rows
    
    Args:
        data: The JSON data structure
        
    Returns:
        Pandas DataFrame with restructured data
    """
    # First, find arrays that might contain rows of data
    common_fields = extract_common_fields(data)
    
    # If we found arrays with common fields, use the one with the most fields
    if common_fields:
        best_array = max(common_fields.items(), key=lambda x: len(x[1]))
        array_path, fields = best_array
        
        logger.info(f"Using array at path '{array_path}' with {len(fields)} fields")
        rows = restructure_array_to_rows(data, array_path, fields)
        
        return pd.DataFrame(rows)
    
    # If no suitable arrays found, just flatten the entire structure
    logger.info("No suitable arrays found, flattening entire structure")
    flat_data = flatten_json(data)
    return pd.DataFrame([flat_data])

def get_json_files_in_current_dir() -> List[str]:
    """
    Get all JSON files in the current directory
    
    Returns:
        List of JSON file paths
    """
    json_files = [f for f in os.listdir('.') if f.endswith('.json')]
    return json_files

def prompt_for_files(available_files: List[str]) -> List[str]:
    """
    Prompt user to select JSON files from the current directory
    
    Args:
        available_files: List of available JSON files
        
    Returns:
        List of selected file paths
    """
    if not available_files:
        print("No JSON files found in the current directory.")
        return []
        
    print("Available JSON files in current directory:")
    for i, file in enumerate(available_files):
        print(f"  {i+1}. {file}")
    
    print("\nEnter file numbers to process (comma-separated)")
    print("Example: 1,3,5 or 1-3 for a range")
    print("Press Enter to select all files")
    
    user_input = input("> ").strip()
    
    if not user_input:
        return available_files
    
    selected_files = []
    parts = user_input.split(',')
    
    for part in parts:
        if '-' in part:
            # Handle range (e.g., 1-3)
            try:
                start, end = map(int, part.split('-'))
                if 1 <= start <= len(available_files) and 1 <= end <= len(available_files):
                    for i in range(start, end + 1):
                        selected_files.append(available_files[i-1])
                else:
                    print(f"Invalid range: {part}. Skipping.")
            except ValueError:
                print(f"Invalid range format: {part}. Skipping.")
        else:
            # Handle single number
            try:
                index = int(part)
                if 1 <= index <= len(available_files):
                    selected_files.append(available_files[index-1])
                else:
                    print(f"File number {index} out of range. Skipping.")
            except ValueError:
                print(f"Invalid input: {part}. Skipping.")
    
    return selected_files

def load_json_files(file_paths: List[str]) -> List[Dict]:
    """
    Load multiple JSON files
    
    Args:
        file_paths: List of file paths
        
    Returns:
        List of loaded JSON data
    """
    all_data = []
    
    for file_path in file_paths:
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                all_data.append(data)
                logger.info(f"Successfully loaded JSON file: {file_path}")
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in file: {file_path}")
        except Exception as e:
            logger.error(f"Error reading JSON file {file_path}: {e}")
    
    return all_data

def combine_dataframes(dfs: List[pd.DataFrame]) -> pd.DataFrame:
    """
    Combine multiple DataFrames, aligning columns
    
    Args:
        dfs: List of DataFrames to combine
        
    Returns:
        Combined DataFrame
    """
    if not dfs:
        return pd.DataFrame()
        
    # Get the union of all columns
    all_columns = set()
    for df in dfs:
        all_columns.update(df.columns)
    
    # Add missing columns to each DataFrame
    aligned_dfs = []
    for df in dfs:
        missing_cols = all_columns - set(df.columns)
        for col in missing_cols:
            df[col] = None
        aligned_dfs.append(df)
    
    # Combine all DataFrames
    return pd.concat(aligned_dfs, ignore_index=True)

def prompt_for_output_file() -> str:
    """
    Prompt user for output CSV file name
    
    Returns:
        Output file path
    """
    print("\nEnter the name for the output CSV file")
    print("Press Enter to use default 'output.csv'")
    
    user_input = input("> ").strip()
    
    if not user_input:
        return 'output.csv'
    
    # Add .csv extension if not provided
    if not user_input.endswith('.csv'):
        user_input += '.csv'
    
    return user_input

def main():
    logger.info("Starting JSON to CSV conversion")
    
    # Get JSON files in current directory
    available_files = get_json_files_in_current_dir()
    
    if not available_files:
        logger.error("No JSON files found in the current directory")
        return
    
    # Prompt user to select files
    selected_files = prompt_for_files(available_files)
    
    if not selected_files:
        logger.error("No files selected for processing")
        return
    
    # Load selected JSON files
    all_data = load_json_files(selected_files)
    
    if not all_data:
        logger.error("No valid JSON data loaded from any files")
        return
        
    logger.info(f"Successfully loaded {len(all_data)} JSON files")
    
    # Process each JSON file into a DataFrame
    all_dfs = []
    for i, data in enumerate(all_data):
        try:
            df = smart_restructure(data)
            if not df.empty:
                all_dfs.append(df)
                logger.info(f"Processed file {i+1}/{len(all_data)} into DataFrame with {len(df)} rows and {len(df.columns)} columns")
            else:
                logger.warning(f"No data could be extracted from file {i+1}/{len(all_data)}")
        except Exception as e:
            logger.error(f"Error processing file {i+1}/{len(all_data)}: {e}")
    
    if not all_dfs:
        logger.error("No data could be extracted from any of the JSON files")
        return
        
    # Combine all DataFrames
    combined_df = combine_dataframes(all_dfs)
    logger.info(f"Combined into DataFrame with {len(combined_df)} rows and {len(combined_df.columns)} columns")
    
    # Show available fields to the user
    print(f"Found {len(combined_df.columns)} unique fields across all JSON files:")
    print("Available fields:")
    
    # Display fields in columns
    col_width = max(len(field) for field in combined_df.columns) + 2
    columns_per_row = 3
    for i in range(0, len(combined_df.columns), columns_per_row):
        row_fields = combined_df.columns[i:i+columns_per_row]
        print("  " + "".join(field.ljust(col_width) for field in row_fields))
    
    print("\nEnter the fields you want to include in the CSV (comma-separated)")
    print("Press Enter to include all fields")
    
    user_input = input("> ").strip()
    selected_fields = [field.strip() for field in user_input.split(',')] if user_input else None
    
    # Filter columns if fields were specified
    if selected_fields:
        valid_fields = [f for f in selected_fields if f in combined_df.columns]
        if len(valid_fields) < len(selected_fields):
            missing = set(selected_fields) - set(valid_fields)
            logger.warning(f"Ignoring {len(missing)} invalid fields: {', '.join(missing)}")
            
        if not valid_fields:
            logger.error("No valid fields selected")
            return
            
        combined_df = combined_df[valid_fields]
    
    # Prompt for output file
    output_file = prompt_for_output_file()
    
    # Export to CSV
    try:
        combined_df.to_csv(output_file, index=False)
        logger.info(f"Successfully created CSV file with {len(combined_df)} rows: {output_file}")
    except Exception as e:
        logger.error(f"Error creating CSV file: {e}")
        return

if __name__ == "__main__":
    main() 