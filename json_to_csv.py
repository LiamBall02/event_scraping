import json
import pandas as pd
import logging
from typing import List, Dict, Any, Set
import argparse
import re

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

def main():
    logger.info("Starting JSON to CSV conversion")
    
    # Get input file
    parser = argparse.ArgumentParser(description='Convert JSON to CSV')
    parser.add_argument('input_file', nargs='?', default='test.json', help='Input JSON file path')
    parser.add_argument('output_file', nargs='?', default='output.csv', help='Output CSV file path')
    args = parser.parse_args()
    
    # Read the JSON file
    try:
        with open(args.input_file, 'r') as file:
            data = json.load(file)
            logger.info(f"Successfully loaded JSON file: {args.input_file}")
    except FileNotFoundError:
        logger.error(f"File not found: {args.input_file}")
        return
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in file: {args.input_file}")
        return
    except Exception as e:
        logger.error(f"Error reading JSON file: {e}")
        return
    
    # Smartly extract data into a DataFrame
    try:
        df = smart_restructure(data)
        
        if df.empty:
            logger.error("No data could be extracted from the JSON")
            return
            
        logger.info(f"Created DataFrame with {len(df)} rows and {len(df.columns)} columns")
        
        # Show available fields to the user
        print(f"Found {len(df.columns)} fields in the JSON data.")
        print("Available fields:")
        
        # Display fields in columns
        col_width = max(len(field) for field in df.columns) + 2
        columns_per_row = 3
        for i in range(0, len(df.columns), columns_per_row):
            row_fields = df.columns[i:i+columns_per_row]
            print("  " + "".join(field.ljust(col_width) for field in row_fields))
        
        print("\nEnter the fields you want to include in the CSV (comma-separated)")
        print("Press Enter to include all fields")
        
        user_input = input("> ").strip()
        selected_fields = [field.strip() for field in user_input.split(',')] if user_input else None
        
        # Filter columns if fields were specified
        if selected_fields:
            valid_fields = [f for f in selected_fields if f in df.columns]
            if len(valid_fields) < len(selected_fields):
                missing = set(selected_fields) - set(valid_fields)
                logger.warning(f"Ignoring {len(missing)} invalid fields: {', '.join(missing)}")
                
            if not valid_fields:
                logger.error("No valid fields selected")
                return
                
            df = df[valid_fields]
    
    except Exception as e:
        logger.error(f"Error processing JSON data: {e}")
        return
    
    # Export to CSV
    try:
        df.to_csv(args.output_file, index=False)
        logger.info(f"Successfully created CSV file: {args.output_file}")
    except Exception as e:
        logger.error(f"Error creating CSV file: {e}")
        return

if __name__ == "__main__":
    main() 