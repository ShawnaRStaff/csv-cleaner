﻿# csv-cleaner 🧹📊

## Description

A Python application designed to clean, normalize, and format CSV files. Perfect for preparing messy 
raw data for analysis or database imports! ✨ This tool removes unnecessary characters, handles 
formatting issues, and ensures clean and structured output.


## Features  🚀

- 🧽 Cleans cells by removing unnecessary characters like stray quotes and semicolons.
- 🛠️ Handles malformed rows, ensuring proper alignment across columns.
- 📁 Supports batch processing of multiple CSV files in a folder.
- ✅ Keeps the original delimiter consistent (e.g., semicolon ;).
- ⚡ Lightweight and easy to use with minimal dependencies.


## Installation 🖥️

1. Clone the repository:
    - `git clone https://github.com/ShawnaRStaff/csv-cleaner.git`
    - cd csv-cleaner
2. Create and activate a virtual environment:
    - python -m venv venv
    - `source venv/bin/activate`  # On Windows: `.\venv\Scripts\activate`


## Usage 🛠️

1. Place your input CSV files in the specified input folder.
2. Run the script:
    - `python clean_csv.py`
3. Cleaned CSV files will be saved to the output folder.


## Configuration ⚙️

Update the input_folder and output_folder variables in clean_csv.py to specify the paths for your files:
- `input_folder = "C:/path/to/input_folder"`
- `output_folder = "C:/path/to/output_folder"`


## How It Works 🔍

1. Input Parsing: Reads each CSV file from the input folder.
2. Cleaning Logic: Applies transformations like:
    - 🗑️ Removing stray quotes and semicolons.
    - ✂️ Trimming whitespace and handling malformed rows.
3. Output: Writes cleaned data to the output folder, maintaining the original structure.


### Example 📋

**Input**:
"Name";"Age";"City";
"John";30;"New York";
"Jane";; "Los Angeles";
"Mike";25;"Chicago";

**Output**
Name;Age;City
John;30;New York
Jane;;Los Angeles
Mike;25;Chicago
