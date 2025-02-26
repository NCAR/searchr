import os
import sys
import re
import html

# list of file exensions that will have contents searched
TEXT_EXTENSIONS = {"txt", "html", "shtml", "htm", "css", "js", "py", "java", "c", "cpp", "h", "php", "xml", "json", "md", "csv", "log", "sql", "sh", "bat", "ini", "conf", "yaml", "yml", "pl", "tt"}

# to highlight terms in results
def highlight_search_terms(text, search_terms):
    pattern = re.compile(r'(' + '|'.join(re.escape(term) for term in search_terms) + ')', re.IGNORECASE)
    return pattern.sub(r'<strong class="text-decoration-underline">\1</strong>', text)

# check if a file should have the contents searched
def is_searchable_file(file_path):
    # Get the file extension (lowercase)
    extension = file_path.split(".")[-1].lower() if "." in file_path else ""
    return extension in TEXT_EXTENSIONS

# checking filenames for strings
def is_string_in_filename(filename, search_string):
    return search_string.lower() in filename.lower()

# crawl a directory and search for words
def search_directory(directory, words):
    grouped_results = {}
    word_patterns = [re.compile(rf'\b{re.escape(word)}\b', re.IGNORECASE) for word in words]
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith('._'):
                continue

            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, directory)
            
            if relative_path not in grouped_results:
                grouped_results[relative_path] = {
                    'filename_matches': set(),
                    'content_matches': []
                }
            
            for word in words:
                if is_string_in_filename(file, word):
                    print(f"Match found: {file} contains {word}")
                    grouped_results[relative_path]['filename_matches'].add(word)
            
            # only check content of files with extensions in TEXT_EXTENSIONS
            if is_searchable_file(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        
                        for line_number, line in enumerate(lines, 1):
                            matches_this_line = []
                            for pattern in word_patterns:
                                if pattern.search(line):
                                    matches_this_line.append(pattern.pattern[2:-2])  # Remove \b from pattern
                            
                            if matches_this_line:
                                line_info = {
                                    'line_num': line_number,
                                    'content': html.escape(line.strip()),
                                    'words': matches_this_line
                                }
                                grouped_results[relative_path]['content_matches'].append(line_info)
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    # convert the grouped results to the final format
    results = []
    for file_path, match_data in grouped_results.items():
        if not match_data['filename_matches'] and not match_data['content_matches']:
            continue
            
        all_matched_words = set(match_data['filename_matches'])
        for match in match_data['content_matches']:
            all_matched_words.update(match['words'])
        
        match_details = []
        
        # add filename matches
        if match_data['filename_matches']:
            escaped_terms = html.escape(', '.join(match_data['filename_matches']))
            match_details.append(f"<strong>Found in filename:</strong> {escaped_terms}")
        
        # add content matches
        if match_data['content_matches']:
            match_details.append("<strong>Content matches:</strong>")
            for match in match_data['content_matches']:
                match_words = html.escape(", ".join(match['words']))
                
                # highlight the search terms
                highlighted_content = highlight_search_terms(match['content'], match['words'])

                # truncate content if it's over 200 characters
                if len(highlighted_content) > 200:
                    # Find the last complete word before 200 characters
                    truncated_content = highlighted_content[:200]
                    last_space = truncated_content.rfind(' ')
                    if last_space > 0:
                        truncated_content = truncated_content[:last_space]
                    truncated_content += "..."
                    highlighted_content = truncated_content
                
                match_details.append(
                    f"<div class='match-line'>Line {match['line_num']}: <span class='match-terms'>[{match_words}]</span> {highlighted_content}</div>"
                )
        
        # combine details into one excerpt and add
        match_excerpt = "<div class='match-details'>" + "</div><div class='match-details'>".join(match_details) + "</div>"
        results.append((file_path, ", ".join(all_matched_words), match_excerpt))
    
    return results

# make the HTML report
def generate_html(results, directory, words, base_url=None):
    sorted_extensions = sorted(list(TEXT_EXTENSIONS))
    
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Search Results</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            .match-details {
                margin-bottom: 10px;
            }
            .match-line {
                margin-left: 20px;
                margin-bottom: 5px;
                font-family: monospace;
                white-space: pre-wrap;
                word-break: break-all;
            }
            .match-terms {
                color: #d63384;
                font-weight: bold;
            }
            .file-path {
                font-weight: bold;
            }
        </style>
    </head>
    <body class="container mt-4">
        <h2>Search Information</h2>
        <div class="card mb-4">
            <div class="card-body">
                <h5 class="card-title">Search Parameters</h5>
                <p><strong>Directory searched:</strong> """ + html.escape(directory) + """</p>
                <p><strong>Website searched:</strong> <a href='""" + html.escape(base_url) + """'>""" + html.escape(base_url) + """</a></p>
                
                <p><strong>Search terms:</strong> """ + html.escape(", ".join(words)) + """</p>
                <div>
                    <p><strong>File extensions searched:</strong></p>
                    <div class="row">
    """
    
    # grid layout for extensions
    chunk_size = 6
    extension_chunks = [sorted_extensions[i:i + chunk_size] for i in range(0, len(sorted_extensions), chunk_size)]
    
    for chunk in extension_chunks:
        html_content += '<div class="col-md-2"><ul class="list-unstyled">'
        for ext in chunk:
            html_content += f'<li><code>.{html.escape(ext)}</code></li>'
        html_content += '</ul></div>'
    
    html_content += """
                    </div>
                </div>
            </div>
        </div>
        
        <h2>Search Results</h2>
        <p>Found matches in <strong>""" + str(len(results)) + """</strong> files.</p>
        <table class="table table-bordered table-striped">
            <thead class="table-dark">
                <tr>
                    <th width="25%">File Path</th>
                    <th width="15%">Matched Terms</th>
                    <th width="60%">Match Details</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for file_path, words, excerpt in results:
        if base_url:
            # Create a proper URL by handling trailing slashes correctly
            url = base_url.rstrip('/') + '/' + file_path.lstrip('/')
            path_cell = f'<a href="{html.escape(url)}" target="_blank" class="file-path">{html.escape(file_path)}</a>'
        else:
            path_cell = f'<span class="file-path">{html.escape(file_path)}</span>'
            
        html_content += f"""
        <tr>
            <td>{path_cell}</td>
            <td>{html.escape(words)}</td>
            <td>{excerpt}</td>
        </tr>
        """
    
    html_content += """
            </tbody>
        </table>
    </body>
    </html>
    """
    return html_content

# main stuff
if __name__ == "__main__":
    # config file
    config_file = "config.txt"
    
    if not os.path.exists(config_file):
        print(f"Error: Configuration file '{config_file}' not found, please create a config.txt file based on config.default.txt")
        sys.exit(1)
    
    print(f"Using configuration from {config_file}")

    # Initialize variables
    directory = None
    words = None
    base_url = None
    output_file = None
    
    # Read configuration
    with open(config_file, 'r', encoding='utf-8') as f:
        for line in f:
            # Skip comments and empty lines
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Parse key-value pairs
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                if key == 'DIRECTORY':
                    directory = value
                elif key == 'SEARCH_TERMS':
                    words = [term.strip() for term in value.split(',')]
                elif key == 'BASE_URL':
                    base_url = value
                elif key == 'OUTPUT_FILE':
                    output_file = value
    
    # Check if all required settings are present
    missing_settings = []
    if directory is None:
        missing_settings.append("DIRECTORY")
    if words is None:
        missing_settings.append("SEARCH_TERMS")
    if base_url is None:
        missing_settings.append("BASE_URL")
    if output_file is None:
        missing_settings.append("OUTPUT_FILE")
    
    if missing_settings:
        print(f"Error: Missing required settings in {config_file}:")
        for setting in missing_settings:
            print(f"  - {setting}")
        sys.exit(1)
    
    # get results
    results = search_directory(directory, words)
    
    # create HTML
    html_output = generate_html(results, directory, words, base_url)

    # save to file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_output)
    
    # msg output
    print(f"Results saved to {output_file}")
    print(f"- Directory searched: {directory}")
    print(f"- Terms searched: {', '.join(words)}")
    print(f"- Number of results: {len(results)}")

