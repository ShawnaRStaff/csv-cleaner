#!/usr/bin/env python3
"""
CSV Cleaner - A utility for cleaning and normalizing CSV files.

This tool processes CSV files to remove common data quality issues:
- OutSystems-specific patterns (N' prefix)
- Stray quotes and trailing semicolons
- Multiline cell handling
- Row padding for consistent column counts

Usage:
    python clean_csvs.py --input ./raw_data --output ./cleaned_data
    python clean_csvs.py -i ./input -o ./output --delimiter ";"
"""

import argparse
import csv
import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


@dataclass
class ProcessingStats:
    """Statistics from processing CSV files."""
    files_processed: int = 0
    files_failed: int = 0
    total_rows: int = 0
    errors: List[str] = field(default_factory=lambda: [])


def clean_cell(cell: str, patterns: Optional[List[str]] = None) -> str:
    """
    Clean a single cell value by removing unwanted characters and patterns.

    Args:
        cell: The cell value to clean.
        patterns: Optional list of regex patterns to remove. Defaults to ["N'"].

    Returns:
        The cleaned cell value.

    Examples:
        >>> clean_cell("N'Hello World'")
        'Hello World'
        >>> clean_cell('"John Doe";')
        'John Doe'
    """
    if patterns is None:
        patterns = [r"N'"]

    # Remove specified patterns (e.g., OutSystems-specific N' prefix)
    for pattern in patterns:
        cell = re.sub(pattern, "", cell)

    # Remove stray single quotes
    cell = cell.replace("'", "")

    # Remove trailing semicolons
    cell = cell.rstrip(";")

    # Remove unnecessary surrounding double quotes
    cell = re.sub(r'^"(.*)"$', r"\1", cell)

    # Trim leading/trailing whitespace
    cell = cell.strip()

    return cell


def clean_csv(
    file_path: Path,
    output_path: Path,
    input_delimiter: str = ";",
    output_delimiter: str = ",",
    encoding: str = "utf-8"
) -> int:
    """
    Clean a CSV file by processing each cell and handling multiline values.

    Args:
        file_path: Path to the input CSV file.
        output_path: Path to write the cleaned CSV file.
        input_delimiter: Delimiter used in the input file. Defaults to ";".
        output_delimiter: Delimiter to use in the output file. Defaults to ",".
        encoding: File encoding. Defaults to "utf-8".

    Returns:
        Number of rows processed.

    Raises:
        FileNotFoundError: If the input file doesn't exist.
        PermissionError: If there's no permission to read/write files.
        csv.Error: If there's an issue parsing the CSV.
    """
    rows_processed = 0

    with open(file_path, "r", encoding=encoding) as infile:
        reader = csv.reader(infile, delimiter=input_delimiter)

        # Read header and determine column count
        # Strip trailing empty columns caused by trailing delimiters
        header = next(reader)
        while header and header[-1] == "":
            header.pop()
        column_count = len(header)
        rows: List[List[str]] = []
        current_row: List[str] = []
        multiline_cell: Optional[str] = None
        temp_row: List[str] = []

        for row in reader:
            temp_row = []

            for cell in row:
                # Handle multiline cells that start with N' and don't end with '
                if multiline_cell is not None:
                    multiline_cell += f" {cell}"
                    if cell.endswith("'"):
                        temp_row.append(multiline_cell)
                        multiline_cell = None
                elif cell.startswith("N'") and not cell.endswith("'"):
                    multiline_cell = cell
                else:
                    temp_row.append(cell)

            # Strip trailing empty cells caused by trailing delimiters
            while temp_row and temp_row[-1] == "":
                temp_row.pop()

            # Build row until we have enough columns
            current_row.extend(temp_row)

            if len(current_row) >= column_count:
                cleaned_row = [clean_cell(cell) for cell in current_row[:column_count]]
                rows.append(cleaned_row)
                current_row = current_row[column_count:]  # Keep overflow for next row
                rows_processed += 1

        # Handle remaining data
        if current_row:
            cleaned_row = [clean_cell(cell) for cell in current_row]
            # Pad with empty strings if needed
            if len(cleaned_row) < column_count:
                cleaned_row.extend([""] * (column_count - len(cleaned_row)))
            rows.append(cleaned_row)
            rows_processed += 1

    # Write cleaned data
    with open(output_path, "w", encoding=encoding, newline="") as outfile:
        writer = csv.writer(outfile, delimiter=output_delimiter)
        writer.writerow(header)
        writer.writerows(rows)

    return rows_processed


def process_folder(
    input_folder: Path,
    output_folder: Path,
    input_delimiter: str = ";",
    output_delimiter: str = ",",
    encoding: str = "utf-8"
) -> ProcessingStats:
    """
    Process all CSV files in a folder.

    Args:
        input_folder: Path to folder containing CSV files to clean.
        output_folder: Path to folder where cleaned files will be saved.
        input_delimiter: Delimiter used in input files.
        output_delimiter: Delimiter to use in output files.
        encoding: File encoding.

    Returns:
        ProcessingStats with processing statistics.

    Raises:
        FileNotFoundError: If input folder doesn't exist.
        PermissionError: If unable to create output folder or access files.
    """
    # Validate input folder
    if not input_folder.exists():
        raise FileNotFoundError(f"Input folder not found: {input_folder}")

    if not input_folder.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {input_folder}")

    # Create output folder
    output_folder.mkdir(parents=True, exist_ok=True)

    stats = ProcessingStats()

    # Find all CSV files
    csv_files = list(input_folder.glob("*.csv"))

    if not csv_files:
        logger.warning(f"No CSV files found in {input_folder}")
        return stats

    logger.info(f"Found {len(csv_files)} CSV file(s) to process")

    for file_path in csv_files:
        output_path = output_folder / file_path.name

        try:
            logger.info(f"Processing: {file_path.name}")
            rows = clean_csv(
                file_path,
                output_path,
                input_delimiter,
                output_delimiter,
                encoding
            )
            stats.files_processed += 1
            stats.total_rows += rows
            logger.info(f"  Cleaned {rows} rows -> {output_path.name}")

        except FileNotFoundError as e:
            stats.files_failed += 1
            stats.errors.append(f"{file_path.name}: {e}")
            logger.error(f"  File not found: {e}")

        except PermissionError as e:
            stats.files_failed += 1
            stats.errors.append(f"{file_path.name}: Permission denied")
            logger.error(f"  Permission denied: {e}")

        except csv.Error as e:
            stats.files_failed += 1
            stats.errors.append(f"{file_path.name}: CSV parsing error - {e}")
            logger.error(f"  CSV parsing error: {e}")

        except UnicodeDecodeError as e:
            stats.files_failed += 1
            stats.errors.append(f"{file_path.name}: Encoding error - try different encoding")
            logger.error(f"  Encoding error: {e}")

        except Exception as e:
            stats.files_failed += 1
            stats.errors.append(f"{file_path.name}: {e}")
            logger.error(f"  Unexpected error: {e}")

    return stats


def main() -> None:
    """Main entry point for the CSV cleaner CLI."""
    parser = argparse.ArgumentParser(
        description="Clean and normalize CSV files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python clean_csvs.py -i ./raw_data -o ./cleaned_data
  python clean_csvs.py --input ./data --output ./output --input-delimiter ";"
  python clean_csvs.py -i ./data -o ./output -v  # Verbose output
        """
    )

    parser.add_argument(
        "-i", "--input",
        type=Path,
        required=True,
        help="Input folder containing CSV files to clean"
    )

    parser.add_argument(
        "-o", "--output",
        type=Path,
        required=True,
        help="Output folder for cleaned CSV files"
    )

    parser.add_argument(
        "--input-delimiter",
        type=str,
        default=";",
        help="Delimiter used in input CSV files (default: ;)"
    )

    parser.add_argument(
        "--output-delimiter",
        type=str,
        default=",",
        help="Delimiter to use in output CSV files (default: ,)"
    )

    parser.add_argument(
        "-e", "--encoding",
        type=str,
        default="utf-8",
        help="File encoding (default: utf-8)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress all output except errors"
    )

    args = parser.parse_args()

    # Configure logging level
    if args.quiet:
        logger.setLevel(logging.ERROR)
    elif args.verbose:
        logger.setLevel(logging.DEBUG)

    try:
        logger.info(f"CSV Cleaner starting...")
        logger.info(f"Input:  {args.input}")
        logger.info(f"Output: {args.output}")
        logger.info(f"Delimiters: '{args.input_delimiter}' -> '{args.output_delimiter}'")

        stats = process_folder(
            args.input,
            args.output,
            args.input_delimiter,
            args.output_delimiter,
            args.encoding
        )

        # Print summary
        logger.info("-" * 40)
        logger.info("Processing complete!")
        logger.info(f"  Files processed: {stats.files_processed}")
        logger.info(f"  Files failed:    {stats.files_failed}")
        logger.info(f"  Total rows:      {stats.total_rows}")

        if stats.errors:
            logger.warning("Errors encountered:")
            for error in stats.errors:
                logger.warning(f"  - {error}")

        # Exit with error code if any files failed
        sys.exit(1 if stats.files_failed > 0 else 0)

    except FileNotFoundError as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

    except NotADirectoryError as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

    except PermissionError as e:
        logger.error(f"Permission error: {e}")
        sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        sys.exit(130)


if __name__ == "__main__":
    main()
