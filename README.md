# HTML to CSV Extractor Tool

A versatile, general-purpose tool for extracting structured data from HTML files and converting it to CSV format.

## Features

- Extract data from various HTML structures including:
  - Images with alt attributes
  - Text in divs, spans, and paragraphs
  - Text enclosed in quotes
  - Tables and lists
- Automatically detects patterns in HTML to extract data efficiently
- Handles different data arrangements:
  - Name from image alt attribute
  - Job title and company from quoted text
  - Nested elements with related information
- Provides helpful debugging output for problematic data

## Usage

```
python html_to_csv_extractor.py [input_file.html]
```

If no input file is specified, the script defaults to `input.html` in the current directory.

### Interactive Prompts

The script will ask you for:

1. **CSV filename** - Name for the output CSV file (without extension)
2. **Column names** - Comma-separated list of column names
3. **Sample values** - For each column, a sample value from the first row of data

### Example

For a page with speakers where:
- Names are in image alt attributes
- Job titles and companies are in quoted text

You would run:
```
python html_to_csv_extractor.py speakers.html
```

Then enter:
```
Enter the desired CSV filename (without extension): speakers_data

Please specify the column names for your CSV (comma-separated):
name, job title, company

For each column, please enter the value from the first row of data:
Sample value for 'name': John Smith
Sample value for 'job title': CEO
Sample value for 'company': Acme Corp
```

The script will:
1. Analyze the HTML structure
2. Find all matches of your sample patterns
3. Extract corresponding data for all entries
4. Save the data to `speakers_data.csv`
5. Create `speakers_html_manual_process.html` for any problematic data that needs manual review

## How It Works

1. **Pattern Detection**: The script analyzes your sample values to detect where they appear in the HTML
2. **Selector Generation**: It creates CSS selectors to match the identified patterns
3. **Data Extraction**: Using these selectors, it extracts all matching data
4. **Special Cases**: For elements like quoted text in the same div, it uses specialized extraction
5. **Second Pass**: For complex structures, it performs additional passes to extract missing values

## Requirements

- Python 3.6+
- BeautifulSoup4
- Standard Python libraries (os, csv, sys, re)

Install dependencies with:
```
pip install beautifulsoup4
```

## Troubleshooting

If the extraction doesn't work as expected:

1. Check that your sample values exactly match what appears in the HTML
2. For complex HTML, provide the most distinct column values as samples
3. Review the problematic rows HTML file for debugging information 