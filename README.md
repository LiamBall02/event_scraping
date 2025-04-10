# HTML to CSV Extractor

This Python script extracts data from an HTML file containing a table or list of company data and converts it to a CSV file.

## Features

- Extracts data from structured HTML tables or lists
- Automatically identifies patterns in your HTML
- Supports extraction from text content AND attributes (alt, title, name, etc.)
- Isolates problematic rows for manual review
- Outputs clean CSV data with your specified column names

## Requirements

- Python 3.6 or higher
- BeautifulSoup4 library

Install the required dependencies:

```
pip install beautifulsoup4
```

## How to Use

1. Place your HTML file in the same directory as the script and name it `input.html`.

2. Run the script:

```
python html_to_csv_extractor.py
```

3. Follow the prompts:
   - Enter the desired CSV filename (without extension)
   - Specify the column names (comma-separated)
   - For each column, enter a sample value from the first row of data

4. The script will:
   - Analyze the HTML structure
   - Extract data based on your sample values
   - Save the extracted data to your specified CSV file
   - Save any problematic rows to `manuallyprocess.html` for manual review

## Example

For a list of companies where company names are stored in image alt attributes:

```
Enter the desired CSV filename (without extension): companies

Please specify the column names for your CSV (comma-separated):
Company Name

For each column, please enter a sample value from the first row of data:
Sample value for 'Company Name': 3C Ventures
```

## How It Works

The script:
1. Searches for your sample values in both text content AND attributes (alt, title, etc.)
2. Creates CSS selectors to target the specific data you need
3. Finds common patterns in the HTML to identify rows
4. Extracts data based on the identified selectors
5. Handles inconsistent or missing data by separating problematic rows

## Troubleshooting

- If the extraction doesn't work well, try providing more distinct sample values
- For HTML where values are in attributes (like image alt text), provide the exact attribute value
- The script works with both well-structured tables and lists/grids of items
- For complex HTML, you may need to review and process the problematic rows manually 