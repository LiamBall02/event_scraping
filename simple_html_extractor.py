#!/usr/bin/env python3
import os
import csv
from bs4 import BeautifulSoup

def get_user_input(soup):
    """Get column names and first row values from user."""
    print("Enter column names (comma-separated):")
    column_names = [name.strip() for name in input().split(",")]
    
    # Check if these column names exist as class names
    first_values = {}
    found_classes = True
    for col in column_names:
        elem = soup.find(class_=col)  # Check any tag with this class
        if elem:
            first_values[col] = elem.get_text(strip=True)
        else:
            found_classes = False
            break
    
    # If we found all matching classes, ask user if this is correct
    if found_classes and first_values:
        print("\nFound elements with matching class names. First values are:")
        for col, value in first_values.items():
            print(f"{col}: {value}")
        
        print("\nIs this the correct mapping? (Y/N)")
        if input().strip().upper() == 'Y':
            return column_names, list(first_values.values()), True
    
    # If no matches or user said no, proceed with manual input
    print("\nFor each column, enter the value from the first row:")
    sample_values = []
    for col in column_names:
        value = input(f"{col}: ").strip()
        sample_values.append(value)
    
    return column_names, sample_values, False

def extract_data_by_class(soup, column_names):
    """Extract data using class names as column names."""
    data = []
    
    # Find all instances of the first column to determine number of rows
    first_col = column_names[0]
    first_elements = soup.find_all(class_=first_col)
    
    # For each first column element
    for first_elem in first_elements:
        row = {}
        has_data = False
        
        # Find the common parent that contains all columns
        parent = first_elem.parent
        while parent and parent.name != 'body':
            # Check if this parent contains elements for all columns
            found_all = True
            for col in column_names:
                if not parent.find(class_=col):
                    found_all = False
                    break
            if found_all:
                break
            parent = parent.parent
        
        if parent:
            # Extract values for each column from this parent
            for col in column_names:
                elem = parent.find(class_=col)
                if elem:
                    value = elem.get_text(strip=True)
                    if value:
                        row[col] = value
                        has_data = True
                else:
                    row[col] = ''
            
            if has_data:
                data.append(row)
    
    return data

def find_pattern(soup, value):
    """Find how to extract a value from HTML."""
    # Try exact text match first
    elem = soup.find(string=lambda x: x and value in x)
    if elem:
        # Get the parent element
        parent = elem.parent
        # Get the full text to see if it contains line breaks
        full_text = parent.get_text(separator='<br>', strip=True)
        parts = full_text.split('<br>')
        
        if len(parts) > 1:
            # If text has line breaks, find which part contains our value
            try:
                index = next(i for i, part in enumerate(parts) if value in part)
                return ('text_with_breaks', parent.name, index)
            except StopIteration:
                pass
        
        # Simple text content
        return ('text', parent.name, None)
    
    # Try alt attributes
    img = soup.find('img', alt=lambda x: x and value in x)
    if img:
        return ('alt', 'img', None)
    
    return (None, None, None)

def get_value(elem, method, index=None):
    """Extract value from element based on pattern."""
    if not elem:
        return ''
        
    if method == 'alt':
        return elem.get('alt', '').strip()
    elif method == 'text_with_breaks':
        parts = elem.get_text(separator='<br>', strip=True).split('<br>')
        if index is not None and index < len(parts):
            return parts[index].strip()
    elif method == 'text':
        return elem.get_text(strip=True)
    return ''

def extract_data_by_pattern(soup, patterns, column_names):
    """Extract data using discovered patterns."""
    data = []
    
    # Find all potential containers
    containers = soup.find_all()
    
    # Process each container
    for container in containers:
        row = {}
        has_data = False
        
        # Try to extract each column's value
        for col, (method, tag, index) in patterns.items():
            if not method:
                continue
            
            value = None
            
            # First try to find the value in this container
            if method == 'alt':
                img = container.find('img', alt=True)
                if img:
                    value = get_value(img, method, index)
            elif method in ['text', 'text_with_breaks']:
                # Find all matching tags in this container
                elems = container.find_all(tag)
                for elem in elems:
                    test_value = get_value(elem, method, index)
                    # Only use this value if it's not already in our row
                    if test_value and test_value not in row.values():
                        value = test_value
                        break
            
            if value:
                row[col] = value
                has_data = True
        
        # Add row if we found any data
        if has_data:
            # Fill in any missing columns
            for col in column_names:
                if col not in row:
                    row[col] = ''
            data.append(row)
    
    # Remove duplicate rows
    unique_data = []
    seen = set()
    for row in data:
        # Convert row to tuple for hashability
        row_tuple = tuple(row[col] for col in column_names)
        if row_tuple not in seen and any(row_tuple):
            seen.add(row_tuple)
            unique_data.append(row)
    
    return unique_data

def main():
    # Get input file
    input_file = "input.html"
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found")
        return
    
    # Load HTML
    with open(input_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    # Get user input and check if using class-based extraction
    column_names, sample_values, use_classes = get_user_input(soup)
    
    # Extract data
    print("\nExtracting data...")
    if use_classes:
        data = extract_data_by_class(soup, column_names)
    else:
        # Find patterns for each column
        print("\nAnalyzing patterns...")
        patterns = {}
        for col, value in zip(column_names, sample_values):
            method, tag, index = find_pattern(soup, value)
            if method:
                print(f"Found pattern for '{col}': {method} using {tag}" + (f" index {index}" if index is not None else ""))
                patterns[col] = (method, tag, index)
            else:
                print(f"Warning: Could not find pattern for '{col}'")
                patterns[col] = (None, None, None)
        data = extract_data_by_pattern(soup, patterns, column_names)
    
    # Save to CSV
    output_file = "output.csv"
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=column_names)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"\nExtracted {len(data)} rows to {output_file}")

if __name__ == "__main__":
    main() 