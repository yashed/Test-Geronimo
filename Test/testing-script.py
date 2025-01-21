import os
import csv
import json
import sys
import time

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from Helper.langchain_helper import generate_data


# Function to load test data from a CSV file
def load_test_data(file_path):
    with open(file_path, mode="r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        return [row for row in reader]


# Main function to orchestrate the testing
def main():
    test_data_path = os.path.join(os.path.dirname(__file__), "test-data-2.csv")
    response_path = os.path.join(os.path.dirname(__file__), "response-test-data-2.json")

    # Load test data from CSV
    try:
        test_data = load_test_data(test_data_path)
    except FileNotFoundError:
        print(f"Test data file not found at: {test_data_path}")
        return

    # Initialize results list
    results = []

    # Process each row in the test data
    for row in test_data:
        try:
            print(f"Processing: {row['name']} at {row['company_name']}...")
            start_time = time.time()

            # Call the function and wait 10 seconds before proceeding
            result = generate_data(
                name=row["name"],
                company=row["company_name"],
                position=row["job_title"],
                country=row["country"],
            )
            time.sleep(10)  # Wait for 10 seconds

            end_time = time.time()
            response_time = end_time - start_time

            results.append(
                {"input": row, "output": result, "response_time": response_time}
            )

        except Exception as e:
            print(f"Error processing {row['name']} at {row['company_name']}: {e}")
            results.append({"input": row, "error": str(e), "response_time": None})

        # Save the current results to a JSON file after each iteration
        try:
            with open(response_path, mode="w", encoding="utf-8") as jsonfile:
                json.dump(results, jsonfile, indent=4)
        except Exception as e:
            print(f"Error saving results to file: {e}")

    print(f"Final results saved to: {response_path}")


# Entry point for the script
if __name__ == "__main__":
    main()
