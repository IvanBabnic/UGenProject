#!/usr/bin/env python3
"""
Module tests for ugen.py.
"""

import sys
import os
import subprocess

def run_ugen(ugen_script, output_file, input_files):
    """
    Executes ugen.py with specified arguments.
    Returns a tuple (return_code, stdout, stderr).
    """
    cmd = ["python3", ugen_script, "-o", output_file] + input_files
    process = subprocess.run(cmd, capture_output=True, text=True)
    return process.returncode, process.stdout, process.stderr

def compare_files(file1, file2):
    """
    Compares two files, ignoring trailing whitespace.
    Returns (True, "") if identical, else (False, diff_details).
    """
    if not (os.path.exists(file1) and os.path.exists(file2)):
        return False, "One or both files do not exist."

    with open(file1, "r", encoding="utf-8") as f1, open(file2, "r", encoding="utf-8") as f2:
        data1 = [line.rstrip() for line in f1.read().splitlines()]
        data2 = [line.rstrip() for line in f2.read().splitlines()]

    if data1 == data2:
        return True, ""

    diff = []
    for i, (line1, line2) in enumerate(zip(data1, data2)):
        if line1 != line2:
            diff.append(f"Line {i + 1}:\nExpected: {line1}\nActual:   {line2}")

    if len(data1) != len(data2):
        diff.append(f"Line count mismatch: Expected {len(data1)}, Actual {len(data2)}")

    return False, "\n\n".join(diff)

def main():
    os.makedirs("temp_outputs", exist_ok=True)

    if len(sys.argv) < 3:
        print("Usage: python3 test.py <ugen_script> <test_data_folder>")
        sys.exit(1)

    ugen_script = sys.argv[1]
    test_data_folder = sys.argv[2]

    # You could optionally allow a custom output filename:
    # e.g. if len(sys.argv) == 4: html_file = sys.argv[3]
    # else: html_file = "test_report.html"
    html_file = "test_report.html"

    # Define multiple scenarios. Each scenario includes:
    #   name: A label for easy identification
    #   input_files: A list of input file paths
    #   expected_output: Path to the file with expected results
    #                    (can be None if you only check for a successful run)
    #   temp_output: A temporary output file created by the script
    scenarios = [
        {
            "name": "scenario_correct_1",
            "input_files": [os.path.join(test_data_folder, "input_correct_1.txt")],
            "expected_output": os.path.join(test_data_folder, "expected_output_1.txt"),
            "temp_output": os.path.join("temp_outputs", "temp_output_1.txt")
        },
        {
            "name": "scenario_collision",
            "input_files": [os.path.join(test_data_folder, "input_collision.txt")],
            "expected_output": os.path.join(test_data_folder, "expected_collision.txt"),
            "temp_output": os.path.join("temp_outputs", "temp_collision.txt")
        },
        {
            "name": "scenario_empty",
            "input_files": [os.path.join(test_data_folder, "input_empty.txt")],
            "expected_output": os.path.join(test_data_folder, "expected_empty.txt"),
            "temp_output": os.path.join("temp_outputs", "temp_empty.txt")
        },
        {
            "name": "scenario_nonsense",
            "input_files": [os.path.join(test_data_folder, "input_nonsense.txt")],
            "expected_output": None,  # we'll just verify it doesn't crash
            "temp_output": os.path.join("temp_outputs", "temp_nonsense.txt")
        },
        {
            "name": "scenario_multiple_files",
            "input_files": [
            os.path.join(test_data_folder, "input_correct_1.txt"),
            os.path.join(test_data_folder, "input_collision.txt")
        ],
        "expected_output": os.path.join(test_data_folder, "expected_multiple.txt"),
        "temp_output": os.path.join("temp_outputs", "temp_multiple.txt")
        },
        {
            "name": "scenario_duplicate_ids",
            "input_files": [
                os.path.join(test_data_folder, "input_duplicate_1.txt"),
                os.path.join(test_data_folder, "input_duplicate_2.txt")
        ],
        "expected_output": os.path.join(test_data_folder, "expected_duplicate.txt"),
        "temp_output": os.path.join("temp_outputs", "temp_duplicate.txt")
        },
    ]

    results = []

    # 1) Run each scenario
    for scenario in scenarios:
        scenario_name = scenario["name"]
        input_files = scenario["input_files"]
        expected_file = scenario["expected_output"]
        output_file = scenario["temp_output"]

        rc, stdout, stderr = run_ugen(ugen_script, output_file, input_files)

        # Decide pass/fail
        if rc != 0:
            results.append({
                "scenario": scenario_name,
                "status": "FAIL",
                "info": f"Return code: {rc}\nStderr:\n{stderr}"
            })
            continue

        if expected_file and os.path.exists(expected_file):
            files_match, diff = compare_files(output_file, expected_file)
            if files_match:
                results.append({
                    "scenario": scenario_name,
                    "status": "PASS",
                    "info": "Output matches expected output file."
                })
            else:
                results.append({
                    "scenario": scenario_name,
                    "status": "FAIL",
                    "info": f"Output differs from expected output file.\n\n{diff}"
                })
        else:
            # If no expected output is provided, just consider it a PASS if rc==0
            results.append({
                "scenario": scenario_name,
                "status": "PASS",
                "info": "No expected output; script ran successfully."
            })

    # 2) Create an HTML report
    # We'll generate a table with scenario name, status, and info.
    passed_count = sum(1 for r in results if r["status"] == "PASS")
    fail_count = sum(1 for r in results if r["status"] == "FAIL")

    html_content = """\
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Module Test Report</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      margin: 20px;
    }
    h1, h2, h3 {
      margin-top: 0;
    }
    table {
      border-collapse: collapse;
      margin-top: 1em;
      width: 100%%;
      max-width: 800px;
    }
    th, td {
      border: 1px solid #ccc;
      padding: 8px;
    }
    th {
      background-color: #f2f2f2;
    }
    .pass {
      color: green;
      font-weight: bold;
    }
    .fail {
      color: red;
      font-weight: bold;
    }
    .info {
      white-space: pre-wrap; /* preserve newlines */
      font-size: 0.9em;
      color: #555;
    }
  </style>
</head>
<body>
  <h1>Module Test Report</h1>
  <table>
    <thead>
      <tr>
        <th>Scenario</th>
        <th>Status</th>
        <th>Details</th>
      </tr>
    </thead>
    <tbody>
"""

    for result in results:
        scenario_name = result["scenario"]
        status = result["status"]
        info = result["info"]
        status_class = "pass" if status == "PASS" else "fail"

        html_content += f"""
      <tr>
        <td>{scenario_name}</td>
        <td class="{status_class}">{status}</td>
        <td class="info">{info}</td>
      </tr>
"""

    html_content += """\
    </tbody>
  </table>
  <h3>Summary</h3>
"""

    html_content += f"<p>Passed: <strong>{passed_count}</strong>, Failed: <strong>{fail_count}</strong>, Total: <strong>{len(results)}</strong></p>"

    html_content += """\
</body>
</html>
"""

    # 3) Write the HTML to file
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"HTML report generated: {html_file}")

    # 4) Also print text summary in console if you want
    print("====== CONSOLE SUMMARY ======")
    for r in results:
        print(f"Scenario: {r['scenario']} -> {r['status']}")
        print(f"  Info: {r['info']}")

    # Return appropriate exit code
    sys.exit(1 if fail_count > 0 else 0)

if __name__ == "__main__":
    main()