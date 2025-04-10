#!/usr/bin/env python3
import os
import csv
import sys
from bs4 import BeautifulSoup
import re

def get_user_input():
    """Collect initial configuration from the user."""
    # Ask for output CSV filename
    csv_filename = input("Enter the desired CSV filename (without extension): ").strip() + ".csv"
    
    # Get column names
    print("\nPlease specify the column names for your CSV (comma-separated):")
    column_names = [name.strip() for name in input().split(",")]
    
    # Get sample values for the first row
    print("\nFor each column, please enter the value from the first row of data:")
    sample_values = []
    for col in column_names:
        value = input(f"Sample value for '{col}': ").strip()
        sample_values.append(value)
    
    return csv_filename, column_names, sample_values

def load_html(filename):
    """Load and parse HTML file."""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            html_content = file.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup, html_content
    except Exception as e:
        print(f"Error loading HTML file: {e}")
        sys.exit(1)

def find_selectors(soup, sample_values):
    """Find CSS selectors for each column based on sample values."""
    selectors = []
    attributes_to_check = ['alt', 'title', 'name', 'value', 'id', 'data-name', 'data-value', 'content']
    
    for value in sample_values:
        found = False
        
        # First check for exact attribute matches as they're more reliable
        for attr in attributes_to_check:
            # Find elements with the attribute exactly matching our value
            elements = soup.find_all(lambda tag: tag.has_attr(attr) and tag[attr] == value)
            
            if elements:
                element = elements[0]
                print(f"Found '{value}' in {attr} attribute of {element.name} tag")
                
                # For img tags with alt attributes, create a more specific selector
                if element.name == 'img' and attr == 'alt':
                    # Try to find a more specific selector using parent classes
                    if element.parent and 'class' in element.parent.attrs:
                        parent_class = element.parent['class'][0]
                        selector = f"img[alt='{value}']"
                        print(f"Using selector: {selector}")
                    else:
                        selector = f"img[alt='{value}']"
                else:
                    # Create selector based on tag and attribute for exact match
                    selector = f"{element.name}[{attr}='{value}']"
                
                selectors.append(selector)
                found = True
                break
        
        # If not found with exact match, try contains
        if not found:
            for attr in attributes_to_check:
                # Find elements with the attribute containing our value
                elements = soup.find_all(lambda tag: tag.has_attr(attr) and value in tag[attr])
                
                if elements:
                    element = elements[0]
                    print(f"Found '{value}' in {attr} attribute of {element.name} tag (partial match)")
                    
                    # Create selector based on tag and attribute
                    if element.name == 'img' and attr == 'alt':
                        # For images, use a more general selector
                        selector = f"img[{attr}*='{value}']"
                    else:
                        selector = f"{element.name}[{attr}*='{value}']"
                    
                    selectors.append(selector)
                    found = True
                    break
        
        # As a last resort, try text content
        if not found:
            elements = soup.find_all(string=re.compile(re.escape(value)))
            
            if elements:
                element = elements[0].parent
                print(f"Found '{value}' in text content of {element.name} tag")
                
                # Create selector based on tag and classes
                if 'class' in element.attrs:
                    class_name = element['class'][0]
                    selector = f"{element.name}.{class_name}"
                else:
                    selector = element.name
                
                selectors.append(selector)
                found = True
        
        # Special handling for images
        if not found:
            # Look for any img tag with alt attribute containing our value
            all_imgs = soup.find_all('img')
            for img in all_imgs:
                if img.has_attr('alt') and value.lower() in img['alt'].lower():
                    print(f"Found '{value}' in alt attribute using fuzzy search")
                    selector = f"img[alt*='{value}']"
                    selectors.append(selector)
                    found = True
                    break
        
        # Try additional fuzzy matching for common patterns
        if not found:
            # Try case-insensitive search in text
            elements = soup.find_all(string=lambda text: value.lower() in text.lower() if text else False)
            if elements:
                element = elements[0].parent
                print(f"Found '{value}' in text content using case-insensitive search")
                selector = element.name
                selectors.append(selector)
                found = True
        
        if not found:
            print(f"Warning: Could not determine selector for value: '{value}'")
            # Add a generic selector that will be handled by our more robust extraction
            if any(val.lower() in value.lower() for val in ["name", "title", "company", "organization"]):
                selector = "img[alt]"  # Common pattern for names/organizations
                print(f"Using generic img alt selector as fallback for '{value}'")
                selectors.append(selector)
            else:
                selectors.append(None)
    
    return selectors

def extract_data(soup, selectors, column_names):
    """Extract data from HTML using the identified selectors."""
    data = []
    problematic_rows = []
    
    # First, try to identify the pattern based on the selectors
    selector_types = []
    for selector in selectors:
        if selector and 'img[alt' in selector:
            selector_types.append('img_alt')
        elif selector and any(attr in selector for attr in ['[title', '[name', '[value', '[id']):
            selector_types.append('attr')
        elif selector and selector.split('[')[0] in ['div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'td']:
            selector_types.append('text')
        else:
            selector_types.append('unknown')
    
    # For img alt attributes, we need a more general approach
    if 'img_alt' in selector_types:
        print("Detected image alt attribute pattern")
        
        # Find all images with alt attributes
        all_images = soup.find_all('img', alt=True)
        print(f"Found {len(all_images)} images with alt attributes")
        
        # For each image, extract data
        for img in all_images:
            row_data = {col: "" for col in column_names}
            
            # Match column to attribute based on selector pattern
            for col_idx, (column, selector) in enumerate(zip(column_names, selectors)):
                if not selector:
                    continue
                    
                if 'img[alt' in selector:
                    # Extract from alt attribute
                    alt_text = img.get('alt', '')
                    if alt_text:
                        row_data[column] = alt_text
                elif 'img[title' in selector:
                    # Extract from title attribute
                    title_text = img.get('title', '')
                    if title_text:
                        row_data[column] = title_text
                # Add more attribute extractions as needed
            
            # If we have data, add to our dataset
            if any(row_data.values()):
                data.append(row_data)
    
    # For speaker data with img alt for name and div.info for job title and company
    elif selectors and any('img[alt' in s for s in selectors if s) and any(selector_types.count('img_alt') > 0 for selector in selectors if selector):
        print("Detected speaker data extraction pattern")
        
        # Find all speaker containers - try various common patterns
        speaker_wrappers = []
        for container_class in ['speaker-wrapper', 'speaker', 'profile', 'card', 'item']:
            wrappers = soup.find_all('div', class_=container_class)
            if wrappers:
                speaker_wrappers.extend(wrappers)
        
        # If no predefined classes found, look for divs containing images with alt attributes
        if not speaker_wrappers:
            for img in soup.find_all('img', alt=True):
                if img.parent and img.parent.name == 'div':
                    speaker_wrappers.append(img.parent)
                elif img.parent and img.parent.parent and img.parent.parent.name == 'div':
                    speaker_wrappers.append(img.parent.parent)
        
        print(f"Found {len(speaker_wrappers)} potential data entries")
        
        # Process each container
        for wrapper in speaker_wrappers:
            row_data = {col: "" for col in column_names}
            
            # Extract name from img alt
            img = wrapper.find('img', alt=True)
            if img and len(column_names) > 0:
                row_data[column_names[0]] = img['alt']
            
            # Extract additional data from info div if exists
            info_div = wrapper.find(['div', 'span', 'p'], class_=['info', 'details', 'description'])
            if info_div and len(column_names) > 1:
                # The text typically has job title and company separated by <br>
                # Get the text and split by newlines
                info_text = info_div.get_text(separator='\n', strip=True)
                info_parts = info_text.split('\n')
                
                # Assign secondary information if available
                if len(info_parts) > 0 and len(column_names) > 1:
                    row_data[column_names[1]] = info_parts[0].strip()
                
                # Assign tertiary information if available
                if len(info_parts) > 1 and len(column_names) > 2:
                    row_data[column_names[2]] = info_parts[1].strip()
            
            # Add the row to our data if it has any non-empty values
            if any(row_data.values()):
                data.append(row_data)
    
    # For text-based tables or lists
    elif selectors and any('text' in selector_types):
        print("Detected text-based pattern")
        
        # Find common parent elements that might contain rows
        potential_row_containers = []
        
        # First try to identify potential row containers based on repeating patterns
        for tag in ['div', 'tr', 'li', 'section', 'article']:
            containers = soup.find_all(tag, class_=True)
            # Group by class to find repeating structures
            class_counts = {}
            for container in containers:
                class_str = ' '.join(container.get('class', []))
                if class_str:
                    class_counts[class_str] = class_counts.get(class_str, 0) + 1
            
            # Classes with multiple instances could be row containers
            repeating_classes = [cls for cls, count in class_counts.items() if count > 1]
            for cls in repeating_classes:
                potential_row_containers.extend(soup.find_all(tag, class_=cls.split()))
        
        print(f"Found {len(potential_row_containers)} potential row containers")
        
        # For each potential container, try to extract structured data
        if potential_row_containers:
            # Sample the first container to analyze structure
            sample = potential_row_containers[0]
            
            # Try to match structure to columns
            column_selectors = []
            for i, col_name in enumerate(column_names):
                # Look for text nodes, spans, divs, quotes, etc.
                potential_col_elements = sample.find_all(['span', 'div', 'p', 'h1', 'h2', 'h3', 'h4', 'td'])
                if i < len(potential_col_elements):
                    # Create a selector based on the element type and position
                    elem = potential_col_elements[i]
                    if 'class' in elem.attrs:
                        class_name = elem['class'][0]
                        selector = f"{elem.name}.{class_name}"
                    else:
                        selector = elem.name
                    column_selectors.append(selector)
                else:
                    column_selectors.append(None)
            
            # Extract using the identified column selectors
            for container in potential_row_containers:
                row_data = {col: "" for col in column_names}
                row_is_valid = False
                
                for i, (col_name, selector) in enumerate(zip(column_names, column_selectors)):
                    if not selector:
                        continue
                    
                    elements = container.select(selector)
                    if elements:
                        # Extract text, handling quotes if present
                        text = elements[0].get_text(strip=True)
                        # Remove surrounding quotes if they exist
                        if text.startswith('"') and text.endswith('"'):
                            text = text[1:-1]
                        
                        row_data[col_name] = text
                        row_is_valid = True
                    else:
                        # Try direct text content if no elements match selector
                        text_nodes = [node for node in container.contents if isinstance(node, str) and node.strip()]
                        if i < len(text_nodes):
                            text = text_nodes[i].strip()
                            if text:
                                row_data[col_name] = text
                                row_is_valid = True
                
                if row_is_valid and any(row_data.values()):
                    data.append(row_data)
                elif any(row_data.values()):
                    problematic_rows.append((row_data, str(container)))
    
    # Generic approach - extract based on selectors
    else:
        print("Using generic extraction approach")
        
        # Extract directly using selectors
        images_with_alt = {}
        
        # First collect all candidates 
        for selector_idx, selector in enumerate(selectors):
            if not selector:
                continue
                
            elements = soup.select(selector)
            print(f"Found {len(elements)} elements matching selector: {selector}")
            
            if not elements:
                continue
                
            # If selector is for img alt, handle specially
            if 'img[alt' in selector:
                # Get all images with alt attributes
                all_images = soup.find_all('img', alt=True)
                for img in all_images:
                    alt_text = img.get('alt', '')
                    if alt_text:
                        if alt_text not in images_with_alt:
                            images_with_alt[alt_text] = {column_names[selector_idx]: alt_text}
                        else:
                            images_with_alt[alt_text][column_names[selector_idx]] = alt_text
        
        # Add all the img alt data
        for alt_text, row_data in images_with_alt.items():
            if any(row_data.values()):
                data.append(row_data)
                
        # If we didn't get any data, fall back to basic selector-based extraction
        if not data:
            # Get max possible rows
            max_rows = max([len(soup.select(sel)) for sel in selectors if sel and soup.select(sel)] or [0])
            
            if max_rows > 0:
                print(f"Extracting {max_rows} rows using basic selector approach")
                
                for row_idx in range(max_rows):
                    row_data = {col: "" for col in column_names}
                    row_has_data = False
                    
                    for col_idx, (column, selector) in enumerate(zip(column_names, selectors)):
                        if not selector:
                            continue
                        
                        elements = soup.select(selector)
                        if row_idx < len(elements):
                            element = elements[row_idx]
                            
                            # Check if we're looking for an attribute value
                            if any(attr in selector for attr in ['alt', 'title', 'name', 'value', 'id']):
                                attr = next((a for a in ['alt', 'title', 'name', 'value', 'id'] if a in selector), None)
                                if attr and element.has_attr(attr):
                                    row_data[column] = element[attr]
                                    row_has_data = True
                                else:
                                    row_data[column] = element.get_text(strip=True)
                                    if row_data[column]:
                                        row_has_data = True
                            else:
                                row_data[column] = element.get_text(strip=True)
                                if row_data[column]:
                                    row_has_data = True
                    
                    if row_has_data:
                        data.append(row_data)
    
    return data, problematic_rows

def save_to_csv(data, filename, column_names):
    """Save extracted data to CSV file."""
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=column_names)
            writer.writeheader()
            writer.writerows(data)
        print(f"\nSuccessfully saved {len(data)} rows to {filename}")
    except Exception as e:
        print(f"Error saving CSV file: {e}")

def save_problematic_rows(problematic_rows, column_names, html_content):
    """Save problematic rows to a separate HTML file for manual review."""
    if not problematic_rows:
        return
    
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Data for Manual Processing</title>
    <style>
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .source-html { margin-top: 20px; border: 1px solid #ddd; padding: 10px; }
        pre { white-space: pre-wrap; font-family: monospace; font-size: 12px; }
    </style>
</head>
<body>
    <h1>Rows that need manual processing</h1>
    <p>The following rows had missing or inconsistent data. Please review and update them manually.</p>
    
    <table>
        <thead>
            <tr>"""
    
    for column in column_names:
        html += f"\n                <th>{column}</th>"
    
    html += """
            </tr>
        </thead>
        <tbody>"""
    
    for row_data, row_html in problematic_rows:
        html += "\n            <tr>"
        for column in column_names:
            html += f"\n                <td>{row_data.get(column, '')}</td>"
        html += "\n            </tr>"
    
    html += """
        </tbody>
    </table>
    
    <h2>Original HTML for Problematic Rows</h2>
    <div class="source-html">"""
    
    for i, (row_data, row_html) in enumerate(problematic_rows):
        html += f"<h3>Row {i+1}</h3><pre>"
        # Escape HTML to display as code
        import html as html_module
        html += html_module.escape(row_html)
        html += "</pre>"
    
    html += """
    </div>
    
    <h2>Complete Original HTML</h2>
    <div class="source-html">
        <pre>"""
    
    # Add the complete original HTML content with HTML entities escaped
    import html as html_module
    html += html_module.escape(html_content)
    
    html += """</pre>
    </div>
</body>
</html>"""
    
    with open("manuallyprocess.html", 'w', encoding='utf-8') as file:
        file.write(html)
    
    print(f"\nSaved {len(problematic_rows)} problematic rows to manuallyprocess.html for manual review")

def main():
    print("HTML to CSV Extractor Tool")
    print("==========================\n")
    
    input_file = "input.html"
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found. Please ensure the file exists in the current directory.")
        sys.exit(1)
    
    # Get user input
    csv_filename, column_names, sample_values = get_user_input()
    
    # Load HTML
    print(f"\nLoading {input_file}...")
    soup, html_content = load_html(input_file)
    
    # Find selectors
    print("Analyzing HTML structure...")
    selectors = find_selectors(soup, sample_values)
    
    # Extract data
    print("Extracting data...")
    data, problematic_rows = extract_data(soup, selectors, column_names)
    
    # Save to CSV
    save_to_csv(data, csv_filename, column_names)
    
    # Save problematic rows
    save_problematic_rows(problematic_rows, column_names, html_content)
    
    print("\nExtraction complete!")

if __name__ == "__main__":
    main() 