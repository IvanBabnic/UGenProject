#!/usr/bin/env python3
"""
Module for generating user login names from input text files.
"""

import argparse
import sys

__author__ = "Ivan Babnič"

def parse_arguments():
    """
    Parses command-line arguments using argparse.

    Returns:
        argparse.Namespace: Object with attributes:
            - output (str): Path to the output file.
            - input_files (list): List of input file paths.

    Raises:
        SystemExit: If invalid arguments are provided (handled by argparse).
    """
    parser = argparse.ArgumentParser(
        description="Generate user login names from one or more input files.")

    parser.add_argument("-o", "--output", required=True,
                        help="Path to the output file where generated data will be saved.")
    parser.add_argument("input_files", nargs="+",
                        help="One or more input files containing user records.")

    return parser.parse_args()


def create_login_name(given_name, middle_name, family_name, existing_logins):
    """
    Generates a unique login name using the following rules:
    1. Take the first letter of the given name (lowercase).
    2. Take the first letter of the middle name (lowercase, optional).
    3. Use the full family name (lowercase).
    4. Truncate the combined string to 8 characters.
    5. Append a numeric suffix (1, 2, 3...) if the username already exists.

    Example:
      Input: "Jozef", "Miloslav", "Hurban" → "jmhurban"
      Collision: "jmhurban" → "jmhurban1"

    Args:
        given_name (str): User's first name.
        middle_name (str): User's middle name (optional).
        family_name (str): User's surname.
        existing_logins (set): Set of existing usernames to avoid collisions.

    Returns:
        str: A unique username.
    """
    initials = given_name[:1].lower()
    if middle_name:
        initials += middle_name[:1].lower()

    base_name = (initials + family_name).lower()
    base_name = base_name[:8]

    username = base_name
    counter = 1
    while username in existing_logins:
        username = base_name + str(counter)
        counter += 1

    existing_logins.add(username)
    return username


def read_input_files(files, existing_logins):
    """
    Processes input files to generate user records with unique login names.

    Input File Format:
        Each line must contain at least 4 colon-separated fields:
        - ID (numeric)
        - Forename
        - [Optional] Middle Name
        - Surname
        - Department

    Invalid lines are skipped (logged to stderr).

    Args:
        files (list): List of input file paths.
        existing_logins (set): Set to track existing usernames globally.

    Returns:
        list: Processed records in the format:
            ID:login:forename:middlename:surname:department
    """
    combined_records = []
    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as input_f:
                for line in input_f:
                    line = line.strip()
                    if not line:
                        continue  # skip empty lines

                    # Split on all ':' and strip parts (no maxsplit)
                    parts = [p.strip() for p in line.split(":")]
                    if len(parts) < 4:
                        continue  # Invalid format

                    user_id = parts[0]
                    if not user_id.isdigit():
                        print(f"[Warning] Invalid non-numeric ID '{user_id}' in line: {line}. Skipping...", file=sys.stderr)
                        continue

                    given_name = parts[1]
                    middle_name = ""
                    surname = ""
                    department = ""

                    if len(parts) == 5:
                        # ID:forename:middlename:surname:department
                        middle_name = parts[2]
                        surname = parts[3]
                        department = parts[4]
                    elif len(parts) == 4:
                        # ID:forename:surname:department (no middle name)
                        surname = parts[2]
                        department = parts[3]
                    elif len(parts) > 5:
                        # Department field contains extra ':' – merge all extra parts into one department
                        middle_name = parts[2]
                        surname = parts[3]
                        department = ":".join(parts[4:])

                    if not surname.strip():
                        # cannot proceed without a surname
                        continue

                    login = create_login_name(given_name, middle_name, surname, existing_logins)
                    output_line = f"{user_id}:{login}:{given_name}:{middle_name}:{surname}:{department}"
                    combined_records.append(output_line)
        except Exception as e:
            sys.stderr.write(f"[Error] Unexpected error reading {file_path}: {str(e)}\n")
            continue

    return combined_records


def write_output_file(destination, records):
    """
    Writes all processed user records to the specified destination file.

    :param destination: Path to the output file.
    :param records: A list of strings, each representing a user record.
    """
    with open(destination, "w", encoding="utf-8") as out_f:
        for record in records:
            out_f.write(record + "\n")


def main():
    """
    Main entry point of the script. Handles argument parsing, reads input files, generates
    unique login names, and writes the final results to an output file.
    """
    args = parse_arguments()

    existing_logins = set()
    final_records = read_input_files(args.input_files, existing_logins)

    write_output_file(args.output, final_records)


if __name__ == "__main__":  # pragma: no cover
    main()