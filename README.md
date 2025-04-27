# HTML to CSV Converter Instructions (A. Web Scraping)

1. Open the website with the target list to extract. 
2. Right click the first entry and click inspect - the full HTML code will appear in the right side under elements.
3. Move your mouse upwards from the selected entry, hovering over each value until you find one that highlights the full list (this is the "container element")
4. Right click that line. then click Copy -> Copy Element. This will copy the entire table. 
5. Open input.html, make sure the file is empty, then paste, save, and close the file. 
6. Go to html_to_csv.py and run the file. the first time you will need to run:
   ```bash
   pip3 install beautifulsoup
   # or
   pip install beautifulsoup
   ```
7. It will ask you for column names. these are the values you want to extract for each row. You have two options:

   a. **(Recommended)** If each value you want has a class label in the html, write the class labels as the column names. The script will automatically pick up the columns.
   
   Example:
   ```html
   <span class="artist-title">Simon Sinek</span>
   <span class="artist-description">Simon Sinek Inc Founder, Ethnographer, Bestselling Author & TED Speaker</span>
   ```

   b. If no common class label exists, or there is multiple values per class label, enter your own column names and then you will be prompted to enter the first value for each of these columns. Look at the first entry in the code and copy it verbatim.
   
   > Make sure to copy the first entry exactly as it's displayed in the HTML, there may be double spaces, etc. Only exception is convert "&amp;amp;" to &

8. It should map all the values to output.csv in the correct columns. You might need to use excel formulas if the information is merged. 
9. If information is not mapping correctly, use Operator. If list is an image, use Operator. If the list is divided into loads of pages, try copying all page elements into the input.html before running the script. If this doesn't work, use Operator. 

# JSON to CSV Converter Instructions (B. Mobile Scraping)

1. Export the JSON data from your mobile app. It can be saved from multiple JSON files.
2. If they're from CharlesProxy, they'll be .txt files, so run jsonify_files script to convert all .txt files in the directory to json.
   ```bash
   python3 B1_jsonify_files.py
   ```
3. Run the json_to_csv.py script:
   ```bash
   python3 B2_json_to_csv.py
   ```
4. The script will:
   - Automatically detect the structure of all your JSON files
   - Flatten nested JSON objects if present
   - List all keys, and prompt you to select which to create columns for. 
   - Create a .csv file with the mapped data.

