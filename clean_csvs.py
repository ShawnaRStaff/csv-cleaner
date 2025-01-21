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
    with open(file_path, 'r', encoding='utf-8') as infile:
        reader = csv.reader(infile, delimiter=';')
        # Read the header row and determine the correct number of columns
        header = next(reader)
        column_count = len(header)
        rows = []
        current_row = []  # To build rows dynamically
        multiline_cell = None  # To handle multiline notes

        for row in reader:
            temp_row = []
            for cell in row:
                # Check if the cell starts with N' and ends without a closing '
                if multiline_cell is not None:
                    multiline_cell += f" {cell}"  # Append to multiline cell
                    if cell.endswith("'"):  # End of multiline cell
                        temp_row.append(multiline_cell)
                        multiline_cell = None
                elif cell.startswith("N'") and not cell.endswith("'"):
                    multiline_cell = cell  # Start a new multiline cell
                else:
                    temp_row.append(cell)

            # Add the completed row (if all fields are resolved)
            current_row.extend(temp_row)
            if len(current_row) >= column_count:
                cleaned_row = [clean_line(cell) for cell in current_row[:column_count]]
                rows.append(cleaned_row)
                current_row = []  # Reset for the next row

        # Handle any remaining data in current_row
        if current_row:
            cleaned_row = [clean_line(cell) for cell in current_row]
            if len(cleaned_row) < column_count:
                cleaned_row.extend([''] * (column_count - len(cleaned_row)))  # Pad with empty strings
            rows.append(cleaned_row)

    # Write the header and cleaned rows to the output file
    with open(output_path, 'w', encoding='utf-8', newline='') as outfile:
        writer = csv.writer(outfile, delimiter=',')
        writer.writerow(header)  # Write the header row
        for row in rows:
            writer.writerow(row)

# Process all CSV files in the input folder
for file_name in os.listdir(input_folder):
    if file_name.endswith('.csv'):
        input_file = os.path.join(input_folder, file_name)
        output_file = os.path.join(output_folder, file_name)
        print(f"Cleaning file: {file_name}")
        clean_csv(input_file, output_file)

print("All files cleaned and saved to output folder.")

