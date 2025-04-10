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

def find_extraction_patterns(soup, value):
    """Find how to extract a value from HTML - returns (method, selector, index)."""
    # Try finding in alt attributes
    img = soup.find('img', alt=value)
    if img:
        return 'alt', 'img[alt]', None
    
    # Try finding in text content
    text_elem = soup.find(string=lambda text: text and value in text)
    if text_elem:
        parent = text_elem.parent
        if parent.name == 'div' and 'info' in parent.get('class', []):
            # This is likely a job title or company - find which part
            text = parent.get_text(separator='<br>', strip=True)
            parts = text.split('<br>')
            if len(parts) > 1:
                try:
                    index = next(i for i, part in enumerate(parts) if value in part)
                    return 'info', 'div.info', index
                except StopIteration:
                    pass
        
        if 'class' in parent.attrs:
            return 'text', f'{parent.name}.{parent["class"][0]}', None
        return 'text', parent.name, None
    
    return None, None, None

def extract_value(element, method, index=None):
    """Extract value from element based on method."""
    if method == 'alt':
        return element.get('alt', '')
    elif method == 'info':
        # Split text by <br> and get the specified part
        text = element.get_text(separator='<br>', strip=True)
        parts = text.split('<br>')
        if index is not None and index < len(parts):
            return parts[index].strip()
        return ''
    elif method == 'text':
        return element.get_text(strip=True)
    return ''

def extract_data(soup, patterns):
    """Extract all matching data using the patterns."""
    data = []
    
    # Find all speaker wrappers
    containers = soup.find_all('div', class_='speaker-wrapper')
    
    for container in containers:
        row = {}
        for col_name, (method, selector, index) in patterns.items():
            if not selector:
                continue
            
            # Find element in current container
            element = container.select_one(selector)
            if element:
                value = extract_value(element, method, index)
                if value:
                    row[col_name] = value
        
        if row and any(row.values()):
            # Clean up any merged values
            for key in row:
                if row[key].count('<br>') > 0:
                    row[key] = row[key].split('<br>')[0].strip()
            data.append(row)
    
    return data

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
        method, selector, index = find_extraction_patterns(soup, value)
        if method:
            print(f"Found pattern for '{col}': {method} using {selector}" + (f" index {index}" if index is not None else ""))
            patterns[col] = (method, selector, index)
        else:
            print(f"Warning: Could not find pattern for '{col}'")
            patterns[col] = (None, None, None)
    
    # Extract data
    print("\nExtracting data...")
    data = extract_data(soup, patterns)
    
    # Save to CSV
    output_file = "output.csv"
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=column_names)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"\nExtracted {len(data)} rows to {output_file}")

if __name__ == "__main__":
    main() 