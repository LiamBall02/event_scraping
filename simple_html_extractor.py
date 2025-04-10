#!/usr/bin/env python3
import os
import csv
from bs4 import BeautifulSoup

def get_user_input():
    """Get column names and first row values from user."""
    print("Enter column names (comma-separated):")
    column_names = [name.strip() for name in input().split(",")]
    
    print("\nFor each column, enter the value from the first row:")
    sample_values = []
    for col in column_names:
        value = input(f"{col}: ").strip()
        sample_values.append(value)
    
    return column_names, sample_values

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

def extract_data(soup, patterns, column_names):
    """Extract data using discovered patterns."""
    data = []
    
    # Find all speaker wrappers (they contain all the data we want)
    containers = soup.find_all('div', class_='speaker-wrapper')
    if not containers:
        # If no speaker wrappers found, use all divs as potential containers
        containers = soup.find_all('div')
    
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
    
    # Get user input
    column_names, sample_values = get_user_input()
    
    # Load HTML
    with open(input_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
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
    
    # Extract data
    print("\nExtracting data...")
    data = extract_data(soup, patterns, column_names)
    
    # Save to CSV
    output_file = "output.csv"
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=column_names)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"\nExtracted {len(data)} rows to {output_file}")

if __name__ == "__main__":
    main() 