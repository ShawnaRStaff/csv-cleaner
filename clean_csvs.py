import os
import re
import csv

input_folder = "path-to-input-directory"
output_folder = "path-to-output-directory"

os.makedirs(output_folder, exist_ok=True)

def clean_line(cell: str) -> str:
    # Remove OutSystems-specific patterns like N'
    cell = re.sub(r"N'", "", cell)
    
    # Remove stray single quotes
    cell = cell.replace("'", "")
    
    # Remove trailing semicolons, unless it's a delimiter
    cell = cell.rstrip(';')
    
    # Remove unnecessary surrounding double quotes
    cell = re.sub(r'^"(.*)"$', r'\1', cell)
    
    # Trim leading/trailing whitespace
    cell = cell.strip()
    
    return cell

def clean_csv(file_path: str, output_path: str):
    with open(file_path, 'r', encoding='utf-8') as infile, open(output_path, 'w', encoding='utf-8', newline='') as outfile:
        # Assuming semicolon-separated values
        reader = csv.reader(infile, delimiter=';')
        writer = csv.writer(outfile, delimiter=',')  # Write as comma-separated for easier Excel compatibility
        
        for row in reader:
            # Check if the row has valid data and process it
            if any(cell.strip() for cell in row):  # Skip completely empty rows
                # Clean each cell in the row
                cleaned_row = [clean_line(cell) for cell in row]
                writer.writerow(cleaned_row)

for file_name in os.listdir(input_folder):
    if file_name.endswith('.csv'):
        input_file = os.path.join(input_folder, file_name)
        output_file = os.path.join(output_folder, file_name)
        print(f"Cleaning file: {file_name}")
        clean_csv(input_file, output_file)

print("All files cleaned and saved to output folder.")
