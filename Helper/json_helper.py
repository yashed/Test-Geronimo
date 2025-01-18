import re
import json


def format_json_string(response):
    try:
        # Attempt to parse the string as-is
        return json.loads(response)
    except json.JSONDecodeError:
        # Try to extract the JSON-like structure
        json_match = re.findall(r"\{.*?\}", response, re.DOTALL)

        if json_match:
            # Attempt to format the extracted items as a JSON array
            json_array_string = "[" + ", ".join(json_match) + "]"
            try:
                parsed_json = json.loads(json_array_string)
                return parsed_json
            except json.JSONDecodeError:
                return {"error": "No data found."}
        else:
            return {"error": "No valid Data found"}
