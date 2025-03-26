# UGenProject

A Python program that generates unique login usernames from one or more input text files. This project demonstrates command-line argument parsing, file handling, string processing, and both unit and integration testing with full test coverage.

---

## 📌 Features

- Accepts multiple input files with user data.
- Generates unique login usernames based on given rules.
- Handles duplicate usernames by appending numeric suffixes.
- Robust against incorrect or malformed input data.
- Includes 100% unit test coverage and integration test report.

---

## 📂 File Structure

```
UGenProject/
├── ugen.py               # Main script for generating usernames
├── test.py               # Script for integration tests
├── tests/
│   └── test_ugen.py      # Unit tests
├── test_data/            # Input & expected output files for test.py
├── temp_outputs/         # Temporary outputs generated during test.py
├── test_report.html      # Human-readable test report
└── README.md             # Project info and usage
```

---

## 🧾 Input Format

Each line in the input files should have 4 or 5 colon-separated fields:
```
ID:Forename[:Middlename]:Surname:Department
```

Example:
```
1234:Jozef:Miloslav:Hurban:Legal
4563:Jozef::Murgas:Development
```

---

## 🔐 Username Generation Rules

- First letter of first name (lowercase)
- First letter of middle name (optional, lowercase)
- Full surname (lowercase)
- Truncated to 8 characters if necessary
- If already used, append a numeric suffix (`1`, `2`, ...)

Example:
```
Jozef Miloslav Hurban → jmhurban
Duplicate → jmhurban1
```

---

## ▶️ Usage

### Run the main script:
```bash
python3 ugen.py -o output_file.txt input1.txt input2.txt ...
```

### Show help:
```bash
python3 ugen.py -h
```

---

## 🧪 Run Unit Tests

```bash
python3 -m unittest discover -s tests
```

Or using `pytest` (if installed):
```bash
pytest tests/test_ugen.py
```

---

## 🧪 Run Integration Tests

```bash
python3 test.py ugen.py test_data
```

This will:
- Process all scenarios in `test_data/`
- Write outputs to `temp_outputs/`
- Generate `test_report.html`

---

## ✅ Code Coverage

This project achieves **100% unit test coverage**.  
To generate an HTML report (optional):
```bash
coverage run -m unittest discover -s tests
coverage html
```
Then open `htmlcov/index.html` in your browser.

---

## 👨‍💻 Author

Ivan Babnič  
2025
