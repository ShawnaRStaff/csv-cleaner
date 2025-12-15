# csv-cleaner

A Python utility for cleaning and normalizing CSV files. Designed for preparing messy raw data (especially OutSystems exports) for analysis or database imports.

## Features

- Removes OutSystems N' prefix patterns
- Strips stray quotes and trailing semicolons
- Handles malformed rows with trailing delimiters
- Pads incomplete rows to maintain column alignment
- Supports batch processing of multiple CSV files
- Configurable input/output delimiters

## Installation

```bash
git clone https://github.com/ShawnaRStaff/csv-cleaner.git
cd csv-cleaner
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```bash
# Basic usage
python clean_csvs.py -i ./input_folder -o ./output_folder

# With custom delimiters
python clean_csvs.py -i ./input -o ./output --input-delimiter ";" --output-delimiter ","

# Verbose output
python clean_csvs.py -i ./input -o ./output -v

# Quiet mode (errors only)
python clean_csvs.py -i ./input -o ./output -q
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-i`, `--input` | Input folder containing CSV files | Required |
| `-o`, `--output` | Output folder for cleaned files | Required |
| `--input-delimiter` | Delimiter in input files | `;` |
| `--output-delimiter` | Delimiter in output files | `,` |
| `-e`, `--encoding` | File encoding | `utf-8` |
| `-v`, `--verbose` | Enable verbose output | Off |
| `-q`, `--quiet` | Suppress all output except errors | Off |

## Example

**Input** (`data.csv`):
```
"Name";"Age";"City";
"John";30;"New York";
N'Jane';25;  Los Angeles  ;
"Bob's Store";40;"Chicago";;
```

**Output** (`data.csv`):
```
Name,Age,City
John,30,New York
Jane,25,Los Angeles
Bobs Store,40,Chicago
```

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

## License

MIT
