import csv
import os
import time
import json
import sys

# Add the root directory to Python's module search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent import gather_info  # Import the function from agent.py

# File paths
TEST_DATA_FILE = os.path.join(os.path.dirname(__file__), "test-data.csv")
TEST_RESULTS_FILE = os.path.join(os.path.dirname(__file__), "test-results.json")


def format_time(elapsed_time):
    """Formats time in MM:SS:MS."""
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    milliseconds = int((elapsed_time % 1) * 1000)
    return f"{minutes:02}:{seconds:02}:{milliseconds:03}"


def run_tests():
    # Read test data from CSV
    if not os.path.exists(TEST_DATA_FILE):
        print(f"Error: Test data file '{TEST_DATA_FILE}' not found.")
        return

    with open(TEST_DATA_FILE, mode="r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        test_data = list(reader)

    # If the JSON file exists, load existing results; otherwise, initialize an empty list
    if os.path.exists(TEST_RESULTS_FILE):
        with open(TEST_RESULTS_FILE, mode="r", encoding="utf-8") as result_file:
            try:
                results = json.load(result_file)
            except json.JSONDecodeError:
                results = []
    else:
        results = []

    # Track processed test indexes to avoid duplication
    processed_indexes = {result["test_index"] for result in results}

    for index, row in enumerate(test_data, start=1):

        if index in processed_indexes:
            continue

        name = row.get("name", "").strip()
        job_title = row.get("job_title", "").strip()
        company_name = row.get("company_name", "").strip()
        country = row.get("country", "").strip()

        print(
            f"\nStarting test {index} for: {name}, {job_title}, {company_name}, {country}"
        )

        # Start timing the test
        start_time = time.perf_counter()

        response = {}
        test_status = "Pass"

        try:
            response_data = gather_info(name, job_title, company_name, country)
            if "error" in response_data:
                test_status = "Fail"
                print(
                    f"Test {index} failed for: {name}. Error: {response_data['error']}"
                )
            else:
                print(f"Test {index} passed for: {name}. Response: {response_data}")
            response = response_data
        except Exception as e:
            response = {"error": str(e)}
            test_status = "Fail"
            print(f"Test {index} failed with an exception: {response}")

        # Stop timing the test
        end_time = time.perf_counter()
        elapsed_time = format_time(end_time - start_time)

        # Append result to JSON file immediately
        result = {
            "test_index": index,
            "input": {
                "name": name,
                "job_title": job_title,
                "company_name": company_name,
                "country": country,
            },
            "response": response,
            "status": test_status,
            "time_taken": elapsed_time,
        }
        results.append(result)

        with open(TEST_RESULTS_FILE, mode="w", encoding="utf-8") as result_file:
            json.dump(results, result_file, indent=2, ensure_ascii=False)

        # Update the current row in the test data
        row["response"] = json.dumps(response)
        row["test_status"] = test_status
        row["time_taken"] = elapsed_time

        print(f"Test {index} completed in {elapsed_time}.")

        # Add a 10-second delay before starting the next test
        print("Waiting 10 seconds before the next test...")
        time.sleep(10)

    print("\nTesting completed. Results saved to test-data.csv and test-results.json.")


if __name__ == "__main__":
    run_tests()
