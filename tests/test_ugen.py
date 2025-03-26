import unittest
import sys
import os
from io import StringIO
from unittest.mock import patch, mock_open, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ugen import (
    parse_arguments,
    create_login_name,
    read_input_files,
    write_output_file,
    main
)

class TestParseArguments(unittest.TestCase):
    """Tests parse_arguments() function, which uses argparse."""

    @patch('sys.argv', ['ugen.py', '-o', 'output.txt', 'input1.txt', 'input2.txt'])
    def test_correct_args(self):
        args = parse_arguments()
        self.assertEqual(args.output, 'output.txt')
        self.assertEqual(args.input_files, ['input1.txt', 'input2.txt'])

    @patch('sys.argv', ['ugen.py', '-o', 'out.txt'])
    def test_missing_input_files(self):
        """
        No input files given => argparse should raise SystemExit,
        because input_files requires at least 1 argument.
        """
        with self.assertRaises(SystemExit):
            parse_arguments()

    @patch('sys.argv', ['ugen.py', 'input1.txt'])
    def test_missing_output_arg(self):
        """Missing -o => SystemExit."""
        with self.assertRaises(SystemExit):
            parse_arguments()

    @patch('sys.argv', ['ugen.py'])
    def test_no_args_at_all(self):
        """No arguments at all => SystemExit."""
        with self.assertRaises(SystemExit):
            parse_arguments()

    @patch('sys.argv', ['ugen.py', '-h'])
    def test_help_argument(self):
        """
        If user provides -h or --help, argparse will print help and raise SystemExit.
        This ensures that path is covered.
        """
        with self.assertRaises(SystemExit):
            parse_arguments()

    # Optional: test unknown argument if you want to see how argparse handles it
    @patch('sys.argv', ['ugen.py', '--xyz'])
    def test_unknown_argument(self):
        """Argparse should raise an error for unknown args => SystemExit."""
        with self.assertRaises(SystemExit):
            parse_arguments()


class TestCreateLoginName(unittest.TestCase):
    """Tests create_login_name() logic."""

    def test_basic_case(self):
        existing = set()
        username = create_login_name("Jozef", "Miloslav", "Hurban", existing)
        self.assertEqual(username, "jmhurban")
        self.assertIn(username, existing)

    def test_no_middle_name(self):
        existing = set()
        username = create_login_name("Milan", "", "Stefanik", existing)
        # 'M' + 'Stefanik' => 'mstefanik' truncated => 'mstefani'
        self.assertTrue(username.startswith("ms"))
        self.assertIn(username, existing)

    def test_collision(self):
        existing = {"jmhurban"}
        username = create_login_name("Jozef", "Miloslav", "Hurban", existing)
        self.assertTrue(username.startswith("jmhurban"))
        # Must not be exactly 'jmhurban' because it already exists
        self.assertNotEqual(username, "jmhurban")
        self.assertIn(username, existing)

    def test_truncation(self):
        existing = set()
        username = create_login_name("Pista", "", "HufnagelXtraLong", existing)
        # e.g. 'phufnage'
        self.assertEqual(len(username), 8)
        self.assertIn(username, existing)


class TestReadInputFiles(unittest.TestCase):
    """Tests read_input_files() thoroughly."""

    @patch("builtins.open", new_callable=mock_open, read_data="""\
1234:Jozef:Miloslav:Hurban:Legal
4567:Milan:Rastislav:Stefanik:Defence
4563:Jozef::Murgas:Development
""")
    def test_basic_input(self, mock_file):
        existing = set()
        results = read_input_files(["some_file.txt"], existing)
        self.assertEqual(len(results), 3)

    @patch("builtins.open", new_callable=mock_open, read_data="999:John:Doe\n")
    def test_exactly_3_parts(self, mock_file):
        """Line with 3 parts (ID:forename:surname) is skipped as len(parts) <4."""
        existing = set()
        results = read_input_files(["three_parts.txt"], existing)
        self.assertEqual(len(results), 0)

    @patch("builtins.open", new_callable=mock_open, read_data="6666:John:: :IT\n")
    def test_5_parts_empty_surname(self, mock_file):
        """Line with 5 parts and empty surname (whitespace) is skipped."""
        existing = set()
        results = read_input_files(["five_parts_empty_surname.txt"], existing)
        self.assertEqual(len(results), 0)

    @patch("builtins.open", side_effect=Exception("Simulated read error"))
    @patch("sys.stderr", new_callable=StringIO)
    def test_file_read_error(self, mock_stderr, mock_file):
        existing = set()
        results = read_input_files(["error.txt"], existing)
        self.assertEqual(len(results), 0)

        # Check stderr output
        error_output = mock_stderr.getvalue()
        self.assertIn("[Error] Unexpected error reading error.txt: Simulated read error", error_output)

    @patch("builtins.open", new_callable=mock_open, read_data="""\
    4563:Jozef::Murgas:Development
    4563:Pista::Hufnagel:Sales
    """)
    def test_duplicate_ids(self, mock_file):
        existing = set()
        results = read_input_files(["duplicate_ids.txt"], existing)
        self.assertEqual(len(results), 2)  # Both records should be processed
        self.assertIn("4563:jmurgas:Jozef::Murgas:Development", results[0])
        self.assertIn("4563:phufnage:Pista::Hufnagel:Sales", results[1])

    @patch("builtins.open", new_callable=mock_open, read_data="7777:John:Middle::Department:Extra\n")
    def test_more_than_5_parts_empty_surname(self, mock_file):
        """Line with >5 parts and empty surname (parts[3]) is skipped."""
        existing = set()
        results = read_input_files(["six_parts_empty_surname.txt"], existing)
        self.assertEqual(len(results), 0)

    @patch("builtins.open", new_callable=mock_open, read_data="abc:John:Doe:IT\n")
    def test_non_numeric_id(self, mock_file):
        existing = set()
        results = read_input_files(["invalid_id.txt"], existing)
        self.assertEqual(len(results), 0)  # Invalid ID → record skipped

    @patch("builtins.open", new_callable=mock_open, read_data="1234:Anna:Smith:IT\n")
    def test_4_parts_valid(self, mock_file):
        """Line with 4 parts (ID:forename:surname:department) is processed."""
        existing = set()
        results = read_input_files(["four_parts_valid.txt"], existing)
        self.assertEqual(len(results), 1)
        self.assertIn("1234:", results[0])
        self.assertIn(":Anna::Smith:IT", results[0])

    @patch("builtins.open", new_callable=mock_open, read_data="\n\n   \n")
    def test_empty_lines(self, mock_file):
        """Skipping entirely empty lines or whitespace-only lines."""
        existing = set()
        results = read_input_files(["empty_lines.txt"], existing)
        self.assertEqual(len(results), 0)

    @patch("builtins.open", new_callable=mock_open, read_data="5555:Maria:  :HR\n")
    def test_surname_whitespace(self, mock_file):
        """Surname is whitespace => skipped."""
        existing = set()
        results = read_input_files(["whitespace_surname.txt"], existing)
        self.assertEqual(len(results), 0)

    @patch("builtins.open", new_callable=mock_open, read_data="8888:John::Marketing\n")
    def test_4_parts_empty_surname(self, mock_file):
        """Line with 4 parts but empty surname is skipped."""
        existing = set()
        results = read_input_files(["four_parts_empty_surname.txt"], existing)
        self.assertEqual(len(results), 0)

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_file_not_found(self, mock_file):
        existing = set()
        results = read_input_files(["nonexistent.txt"], existing)
        self.assertEqual(len(results), 0)

    @patch("builtins.open", new_callable=mock_open, read_data="""\
1111:Pista::Hufnagel:Sales
2222:Pista::Hufnagel:Sales
""")
    def test_collision_in_same_file(self, mock_file):
        existing = set()
        results = read_input_files(["collision_file.txt"], existing)
        self.assertEqual(len(results), 2)
        self.assertIn("1111:phufnage:Pista::Hufnagel:Sales", results[0])
        self.assertIn("2222:phufnage1:Pista::Hufnagel:Sales", results[1])

    @patch("builtins.open", new_callable=mock_open, read_data="""\
9999:Jozef
""")
    def test_less_than_4_parts(self, mock_file):
        existing = set()
        results = read_input_files(["few_parts.txt"], existing)
        self.assertEqual(len(results), 0, "No valid records, so zero lines returned.")

    @patch("builtins.open", new_callable=mock_open, read_data="""\
8888:Jozef:Extra:Miloslav:Hurban:Department:OneMore
""")
    def test_extra_fields_case(self, mock_file):
        """
        There's a line with more than 5 parts => the code should ignore extras
        but still produce a valid record.
        """
        existing = set()
        results = read_input_files(["too_many_parts.txt"], existing)
        self.assertEqual(len(results), 1)
        # expected: 8888:<login>:Jozef:Extra:Miloslav:...
        line_parts = results[0].split(":")
        # ID should be 8888
        self.assertEqual(line_parts[0], "8888")
        # Forename = Jozef => line_parts[2]
        self.assertEqual(line_parts[2], "Jozef")
        # Middlename = Extra => line_parts[3]
        self.assertEqual(line_parts[3], "Extra")
        # Surname = Miloslav => line_parts[4]
        self.assertEqual(line_parts[4], "Miloslav")
        # Department = Hurban => line_parts[5]

    @patch("builtins.open", new_callable=mock_open, read_data="""\
7777:Jozef:: :Something
""")
    def test_empty_surname(self, mock_file):
        """
        If the surname is empty (or whitespace), the code should skip that entry (cannot generate).
        """
        existing = set()
        results = read_input_files(["no_surname.txt"], existing)
        self.assertEqual(len(results), 0)

    @patch("builtins.open", new_callable=mock_open, read_data="9999:Anna:Marketing:Sales:HR:Global\n")
    def test_department_with_colon(self, mock_file):
        """Test department field containing a colon."""
        existing = set()
        results = read_input_files(["dept_colon.txt"], existing)
        self.assertEqual(len(results), 1)
        self.assertIn(":HR:Global", results[0])  # Verify department

    @patch("builtins.open", new_callable=mock_open, read_data="1234:John:Doe:IT:Support:EMEA\n")
    def test_extra_parts_department(self, mock_file):
        """Test line with >5 parts (department includes colon)."""
        existing = set()
        results = read_input_files(["extra_parts.txt"], existing)
        self.assertEqual(len(results), 1)
        self.assertIn(":IT:Support:EMEA", results[0])

    @patch("builtins.open", new_callable=mock_open, read_data="1000:Jan:Novak:HR\n")
    def test_4_parts_no_middle_name(self, mock_file):
        existing = set()
        results = read_input_files(["no_middle_name.txt"], existing)
        self.assertEqual(len(results), 1)
        self.assertIn("1000:", results[0])
        self.assertIn(":Jan::Novak:HR", results[0])

    @patch("builtins.open", new_callable=mock_open, read_data="9999:John:William:Doe:Engineering:ExtraInfo:Misc\n")
    def test_more_than_5_parts(self, mock_file):
        existing = set()
        results = read_input_files(["extra_fields.txt"], existing)
        self.assertEqual(len(results), 1)
        self.assertIn("9999:", results[0])
        self.assertIn(":John:William:Doe:", results[0])
        self.assertIn(":Engineering:ExtraInfo:Misc", results[0])


class TestWriteOutputFile(unittest.TestCase):
    """Tests write_output_file() function."""

    def test_write_output(self):
        data = [
            "1234:jmhurban:Jozef:Miloslav:Hurban:Legal",
            "4567:mrstefan:Milan:Rastislav:Stefanik:Defence"
        ]
        with patch("builtins.open", mock_open()) as mocked_file:
            write_output_file("some_output.txt", data)

        handle = mocked_file()
        handle.write.assert_any_call("1234:jmhurban:Jozef:Miloslav:Hurban:Legal\n")
        handle.write.assert_any_call("4567:mrstefan:Milan:Rastislav:Stefanik:Defence\n")


class TestMainFunction(unittest.TestCase):
    """Tests the main() function end-to-end with mocks for file operations."""

    @patch("sys.argv", ["ugen.py", "-o", "out.txt", "input1.txt"])
    @patch("ugen.read_input_files", return_value=[
        "1234:jmhurban:Jozef:Miloslav:Hurban:Legal",
        "4567:mrstefan:Milan:Rastislav:Stefanik:Defence"
    ])
    @patch("ugen.write_output_file")
    def test_main_normal_run(self, mock_write, mock_read):
        """Checks that main() calls read_input_files() & write_output_file() with correct arguments."""
        main()
        mock_read.assert_called_once_with(["input1.txt"], set())
        mock_write.assert_called_once_with(
            "out.txt",
            [
                "1234:jmhurban:Jozef:Miloslav:Hurban:Legal",
                "4567:mrstefan:Milan:Rastislav:Stefanik:Defence"
            ]
        )

    @patch("sys.argv", ["ugen.py", "input1.txt"])
    def test_main_missing_output_arg(self):
        """
        Missing the -o/--output argument => parse_arguments() triggers SystemExit.
        """
        with self.assertRaises(SystemExit):
            main()


if __name__ == "__main__": # pragma: no cover
    unittest.main()