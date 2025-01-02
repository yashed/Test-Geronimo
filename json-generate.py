import json
import re

# File paths
input_file = "response.txt"
output_file = "response.json"

# Read the content from the file
with open(input_file, "r") as file:
    response = file.read()

# Use a regular expression to extract the JSON part (content between { and })
json_match = re.search(r"\{.*\}", response, re.DOTALL)
if json_match:
    # Get the matched JSON string
    json_string = json_match.group(0)
    print("Extracted JSON String = ", json_string)

    # Parse and save the JSON
    try:
        parsed_json = json.loads(json_string)
        # Save the parsed JSON to a new file
        with open(output_file, "w") as json_file:
            json.dump(parsed_json, json_file, indent=4)  # Indented for readability
        print(f"JSON saved to {output_file}")
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
else:
    print("No valid JSON found in the response.")
