"""Tests for the CSV cleaner module."""

import csv
from pathlib import Path

import pytest

from clean_csvs import ProcessingStats, clean_cell, clean_csv, process_folder


class TestCleanCell:
    """Tests for the clean_cell function."""

    def test_removes_outsystems_n_prefix(self) -> None:
        """Should remove N' prefix from OutSystems data."""
        assert clean_cell("N'Hello World'") == "Hello World"
        assert clean_cell("N'Test'") == "Test"

    def test_removes_stray_single_quotes(self) -> None:
        """Should remove stray single quotes."""
        assert clean_cell("It's a test") == "Its a test"
        assert clean_cell("'quoted'") == "quoted"

    def test_removes_trailing_semicolons(self) -> None:
        """Should remove all trailing semicolons."""
        assert clean_cell("value;") == "value"
        assert clean_cell("test;;") == "test"  # Removes all trailing semicolons

    def test_removes_surrounding_double_quotes(self) -> None:
        """Should remove unnecessary surrounding double quotes."""
        assert clean_cell('"John Doe"') == "John Doe"
        assert clean_cell('"Test Value"') == "Test Value"

    def test_preserves_internal_double_quotes(self) -> None:
        """Should preserve double quotes that aren't surrounding."""
        assert clean_cell('Say "Hello"') == 'Say "Hello"'

    def test_trims_whitespace(self) -> None:
        """Should trim leading and trailing whitespace."""
        assert clean_cell("  hello  ") == "hello"
        assert clean_cell("\ttest\n") == "test"

    def test_handles_empty_string(self) -> None:
        """Should handle empty strings."""
        assert clean_cell("") == ""

    def test_handles_whitespace_only(self) -> None:
        """Should handle whitespace-only strings."""
        assert clean_cell("   ") == ""
        assert clean_cell("\t\n") == ""

    def test_combined_cleaning(self) -> None:
        """Should handle multiple cleaning operations."""
        assert clean_cell("N'  Hello World  ';") == "Hello World"
        assert clean_cell('"N\'Test Value\'";') == "Test Value"

    def test_custom_patterns(self) -> None:
        """Should support custom regex patterns."""
        assert clean_cell("PREFIX_value", patterns=[r"PREFIX_"]) == "value"
        assert clean_cell("XXXtest", patterns=[r"XXX"]) == "test"


class TestCleanCsv:
    """Tests for the clean_csv function."""

    def test_basic_csv_cleaning(self, tmp_path: Path) -> None:
        """Should clean a basic CSV file."""
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"

        # Create input file (no trailing semicolon on data row)
        input_file.write_text('Name;Age;City\n"John";30;"New York"\n', encoding="utf-8")

        rows = clean_csv(input_file, output_file)

        assert rows == 1
        assert output_file.exists()

        # Verify output
        content = output_file.read_text(encoding="utf-8")
        assert "John,30,New York" in content

    def test_handles_empty_cells(self, tmp_path: Path) -> None:
        """Should handle empty cells."""
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"

        input_file.write_text("A;B;C\n1;;3\n", encoding="utf-8")

        rows = clean_csv(input_file, output_file)

        assert rows == 1
        content = output_file.read_text(encoding="utf-8")
        assert "1,,3" in content

    def test_pads_incomplete_rows(self, tmp_path: Path) -> None:
        """Should pad incomplete rows with empty strings."""
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"

        input_file.write_text("A;B;C\n1\n", encoding="utf-8")

        clean_csv(input_file, output_file)

        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            row = next(reader)
            assert len(row) == 3  # Should be padded to 3 columns

    def test_custom_delimiters(self, tmp_path: Path) -> None:
        """Should support custom input and output delimiters."""
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"

        input_file.write_text("A|B|C\n1|2|3\n", encoding="utf-8")

        clean_csv(input_file, output_file, input_delimiter="|", output_delimiter="\t")

        content = output_file.read_text(encoding="utf-8")
        assert "1\t2\t3" in content

    def test_file_not_found(self, tmp_path: Path) -> None:
        """Should raise FileNotFoundError for missing input."""
        input_file = tmp_path / "nonexistent.csv"
        output_file = tmp_path / "output.csv"

        with pytest.raises(FileNotFoundError):
            clean_csv(input_file, output_file)

    def test_preserves_header(self, tmp_path: Path) -> None:
        """Should preserve the header row."""
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"

        input_file.write_text("Name;Age;City\nJohn;30;NYC\n", encoding="utf-8")

        clean_csv(input_file, output_file)

        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            assert header == ["Name", "Age", "City"]


class TestProcessFolder:
    """Tests for the process_folder function."""

    def test_processes_multiple_files(self, tmp_path: Path) -> None:
        """Should process all CSV files in a folder."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()

        # Create test files
        (input_dir / "file1.csv").write_text("A;B\n1;2\n", encoding="utf-8")
        (input_dir / "file2.csv").write_text("X;Y\n3;4\n", encoding="utf-8")

        stats = process_folder(input_dir, output_dir)

        assert stats.files_processed == 2
        assert stats.files_failed == 0
        assert (output_dir / "file1.csv").exists()
        assert (output_dir / "file2.csv").exists()

    def test_ignores_non_csv_files(self, tmp_path: Path) -> None:
        """Should ignore non-CSV files."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()

        (input_dir / "data.csv").write_text("A;B\n1;2\n", encoding="utf-8")
        (input_dir / "readme.txt").write_text("Not a CSV", encoding="utf-8")

        stats = process_folder(input_dir, output_dir)

        assert stats.files_processed == 1
        assert not (output_dir / "readme.txt").exists()

    def test_creates_output_folder(self, tmp_path: Path) -> None:
        """Should create output folder if it doesn't exist."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "nested" / "output"
        input_dir.mkdir()

        (input_dir / "test.csv").write_text("A;B\n1;2\n", encoding="utf-8")

        process_folder(input_dir, output_dir)

        assert output_dir.exists()

    def test_input_folder_not_found(self, tmp_path: Path) -> None:
        """Should raise error for missing input folder."""
        input_dir = tmp_path / "nonexistent"
        output_dir = tmp_path / "output"

        with pytest.raises(FileNotFoundError):
            process_folder(input_dir, output_dir)

    def test_handles_empty_folder(self, tmp_path: Path) -> None:
        """Should handle folder with no CSV files."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()

        stats = process_folder(input_dir, output_dir)

        assert stats.files_processed == 0

    def test_returns_statistics(self, tmp_path: Path) -> None:
        """Should return processing statistics."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()

        (input_dir / "test.csv").write_text("A;B;C\n1;2;3\n4;5;6\n", encoding="utf-8")

        stats = process_folder(input_dir, output_dir)

        assert isinstance(stats, ProcessingStats)
        assert stats.files_processed == 1
        assert stats.files_failed == 0
        assert stats.total_rows == 2
        assert isinstance(stats.errors, list)


class TestMultilineCells:
    """Tests for multiline cell handling."""

    def test_handles_multiline_outsystems_cell(self, tmp_path: Path) -> None:
        """Should handle OutSystems multiline cells that span rows."""
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"

        # Simulate a multiline cell that starts with N' and ends with '
        content = "A;B;C\nN'Line1\nLine2';Value2;Value3\n"
        input_file.write_text(content, encoding="utf-8")

        clean_csv(input_file, output_file)

        assert output_file.exists()


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_handles_trailing_delimiters(self, tmp_path: Path) -> None:
        """Should handle trailing semicolons without column misalignment."""
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"

        # Trailing semicolons create empty columns that should be stripped
        input_file.write_text("A;B;C;\n1;2;3;\n4;5;6;;\n", encoding="utf-8")

        clean_csv(input_file, output_file)

        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            row1 = next(reader)
            row2 = next(reader)
            assert header == ["A", "B", "C"]
            assert row1 == ["1", "2", "3"]
            assert row2 == ["4", "5", "6"]

    def test_handles_unicode(self, tmp_path: Path) -> None:
        """Should handle Unicode characters."""
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"

        input_file.write_text("Name;City\nJosé;São Paulo\n", encoding="utf-8")

        clean_csv(input_file, output_file)

        content = output_file.read_text(encoding="utf-8")
        assert "José" in content
        assert "São Paulo" in content

    def test_handles_large_file(self, tmp_path: Path) -> None:
        """Should handle larger files efficiently."""
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"

        # Create a file with 1000 rows
        lines = ["A;B;C"] + [f"Row{i};Value{i};Data{i}" for i in range(1000)]
        input_file.write_text("\n".join(lines), encoding="utf-8")

        rows = clean_csv(input_file, output_file)

        assert rows == 1000


class TestProcessingStats:
    """Tests for the ProcessingStats dataclass."""

    def test_default_values(self) -> None:
        """Should initialize with default values."""
        stats = ProcessingStats()
        assert stats.files_processed == 0
        assert stats.files_failed == 0
        assert stats.total_rows == 0
        assert stats.errors == []

    def test_can_modify_values(self) -> None:
        """Should allow modifying values."""
        stats = ProcessingStats()
        stats.files_processed = 5
        stats.total_rows = 100
        stats.errors.append("test error")

        assert stats.files_processed == 5
        assert stats.total_rows == 100
        assert len(stats.errors) == 1
