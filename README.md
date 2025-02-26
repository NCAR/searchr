# Directory Search Tool

A Python script that searches files in a directory for specific terms and generates an HTML report of the results.

## Configuration

1. Copy the default configuration file:
   ```
   cp config.default.txt config.txt
   ```
   
2. Edit `config.txt` with your specific settings:
   - `DIRECTORY`: The directory path to search in
   - `SEARCH_TERMS`: A list of terms to search for, comma separated
   - `BASE_URL`: Base URL for file links in the generated report
   - `OUTPUT_FILE`: Filename for the HTML report

## Usage

Run the script:

```
python search.py
```

The script will:
1. Load configuration from `config.txt` and will stop if this file doesn't exist
2. Search through files in the specified directory - checking filenames and content of certain file types 
3. Generate an HTML report
4. Save the report to the configured output file