import re
import json


def format_json_string(response):
    """
    Format a JSON-like string into a valid JSON format
    Mainly used for format social media links and company news to JSON Array
    Args:
        response (str): The JSON-like string to be formatted
    Returns:
        dict: The formatted JSON object


    """
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
