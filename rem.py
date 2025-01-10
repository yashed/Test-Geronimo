from langchain.agents import initialize_agent, Tool, ZeroShotAgent
from langchain.memory import ConversationBufferMemory
from langchain_openai import AzureChatOpenAI
from langchain_google_community import GoogleSearchAPIWrapper
from langchain.schema import AIMessage, HumanMessage
import requests
import os
import re
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from typing import Dict, List, Any, Union

load_dotenv(override=True)

# Initialize Environment Variables
os.environ["OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
os.environ["OPENAI_API_TYPE"] = "azure"
os.environ["OPENAI_API_BASE"] = os.getenv("OPENAI_API_BASE")
os.environ["OPENAI_API_VERSION"] = os.getenv("OPENAI_API_VERSION")

X_API_KEY = os.getenv("SERPER_API_KEY")

# LLM
llm = AzureChatOpenAI(
    openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    deployment_name=os.getenv("OPENAI_DEPLOYMENT_NAME"),
    azure_endpoint=os.getenv("OPENAI_API_BASE"),
    temperature=0.1,
)


# Tools
def google_search(
    query: str, num_results: int = 8, use_serper: bool = True
) -> List[Dict[str, Any]]:
    if use_serper:
        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": query, "num": num_results})
        headers = {"X-API-KEY": X_API_KEY, "Content-Type": "application/json"}

        response = requests.request("POST", url, headers=headers, data=payload)

        if response.status_code == 200:
            return response.json().get("organic", [])
        else:
            return [
                {
                    "error": f"Serper request failed with status code {response.status_code}"
                }
            ]

    else:
        google_search_tool = GoogleSearchAPIWrapper()
        return google_search_tool.results(query, num_results=num_results)


def web_scraping(url: str) -> str:
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            visible_text = soup.get_text()
            return visible_text.strip()
        else:
            return f"Failed to retrieve data from {url}. Status code: {response.status_code}"
    except Exception as e:
        return f"An error occurred: {str(e)}"


tools = [
    Tool(
        name="Google Search",
        func=google_search,
        description="Search Google for relevant information.",
    ),
    Tool(
        name="Web Scraping",
        func=web_scraping,
        description="Scrape content from a given URL.",
    ),
]

# Agent Initialization
memory = ConversationBufferMemory(memory_key="chat_history")
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent_type="zero-shot-react-description",  # Changed from ZeroShotAgent
    memory=memory,
    handle_parsing_errors=True,
    verbose=True,
    max_iterations=10,
)


def gather_info(
    name: str, job_title: str, company_name: str, country: str
) -> Dict[str, Any]:
    # Breaking down into smaller queries

    # Get Personal Information from the agent : Personal Summary and Social Media Links
    def get_personal_info() -> Dict[str, Any]:
        personal_query = f"""Find and return information about {name} who works as {job_title} at {company_name} in {country}.
        Return ONLY a JSON object in this EXACT format:
        {{
            "personal_summary": "<A detailed 300-word summary about the person, focusing on their professional achievements, career history, expertise, and notable contributions in their field>",
            "social_media_links": [
                {{
                    "platform": "LinkedIn",
                    "url": "<verified LinkedIn profile URL>"
                }},
                {{
                    "platform": "Twitter",
                    "url": "<verified Twitter/X profile URL>"
                }},
                {{
                    "platform": "GitHub",
                    "url": "<verified GitHub profile URL>"
                }},
                {{
                    "platform": "Company Profile",
                    "url": "<verified company profile or author page URL>"
                }},
                {{
                    "platform": "Personal Website",
                    "url": "<verified personal website or blog URL>"
                }}
            ]
        }}

    Instructions for data collection:
    1. For personal_summary: Focus on verified professional information, achievements, and expertise
    2. For social_media_links:
       - Each link must be in a separate object with "platform" and "url" fields
       - Only include platforms where you find verified profiles
       - Remove any platform objects where you can't find a verified URL
       - Add additional platform objects if you find other relevant professional profiles
       - Ensure all URLs are direct links to the person's profiles
       - Verify that each URL is accessible and belongs to the correct person

    Remember: Return ONLY the JSON structure with actual data, no placeholder text or additional commentary."""

        response = agent.invoke(input={"input": personal_query})
        return extract_json(response)

    # Get Company Information from the agent : Company Summary and Competitors
    def get_company_info() -> Dict[str, Any]:
        company_query = f"""Research {company_name} and return information in this exact JSON format:
        {{
            "company_summary": "<comprehensive company summary with nearly 250 words>",
            "company_competitors": "<3-5 main competitors,give only company names not product names, separated by commas>"
        }}"""

        response = agent.invoke(input={"input": company_query})
        return extract_json(response)

    def get_news_info() -> Dict[str, Any]:
        news_query = f"""Find 3-5 MOST RECENT news articles about {company_name}. 

        Search instructions:
        1. Use search terms like "latest news {company_name}", "recent announcements {company_name}", "{company_name} announces", "{company_name} launches", "latest updates {company_name}", "most recent {company_name}"
        2. IMPORTANT: Focus ONLY on the newest and most recent news without using specific dates in your search
        3. Use filters and search techniques to get the most recent results first
        4. Prioritize official company press releases and major tech news websites
    
    
        Return the data in this exact JSON format:
        {{
            "company_news": [
                {{
                    "title": "<exact title of the latest news article>",
                    "url": "<direct URL to the news article>",
                    "description": "<100-word summary focusing on key announcements and impacts>"
                }},
                {{
                    "title": "<exact title of another recent news article>",
                    "url": "<direct URL to the news article>",
                    "description": "<100-word summary focusing on key announcements and impacts>"
                }},
                {{
                    "title": "<exact title of another recent news article>",
                    "url": "<direct URL to the news article>",
                    "description": "<100-word summary focusing on key announcements and impacts>"
                }}
            ]
        }}
    
    Remember: Only include the MOST RECENT news articles. Do not use specific dates in your search. Focus on terms like 'latest', 'recent', 'newest', and 'just announced' to find current information."""

        response = agent.invoke(input={"input": news_query})
        return extract_json(response)

    def extract_json(response: Any) -> Dict[str, Any]:
        try:
            if isinstance(response, dict) and "output" in response:
                response_text = response["output"]
            else:
                response_text = str(response)

            # find and parse JSON
            json_match = re.search(r"\{[\s\S]*\}", response_text)
            if json_match:
                return json.loads(json_match.group(0))
            return {"error": "No JSON found in response"}
        except Exception as e:
            return {"error": f"JSON parsing error: {str(e)}"}

    try:
        # Get information
        # Check Whether we can get this data parallelly
        personal_data = get_personal_info()
        company_data = get_company_info()
        news_data = get_news_info()

        # Check for errors
        if any("error" in x for x in [personal_data, company_data, news_data]):
            error_messages = []
            if "error" in personal_data:
                error_messages.append(f"Personal: {personal_data['error']}")
            if "error" in company_data:
                error_messages.append(f"Company: {company_data['error']}")
            if "error" in news_data:
                error_messages.append(f"News: {news_data['error']}")

            return {"error": "One or more queries failed", "details": error_messages}

        # Combine all data into final format
        final_result = {
            "personal_summary": personal_data.get("personal_summary", "Not available"),
            "social_media_links": personal_data.get("social_media_links", {}),
            "company_summary": company_data.get("company_summary", "Not available"),
            "company_competitors": company_data.get("company_competitors", ""),
            "company_news": news_data.get("company_news", []),
        }

        return final_result

    except Exception as e:
        return {"error": "Error in data gathering process", "details": str(e)}


# Main Function for testing
if __name__ == "__main__":
    test_inputs = {
        "name": "Malith Jayasignhe",
        "job_title": "Developer",
        "company_name": "WSO2",
        "country": "Sri Lanka",
    }

    result = gather_info(**test_inputs)
    if "error" not in result:
        print("\nSuccessfully gathered information:")
        print(json.dumps(result, indent=2))
    else:
        print("\nError occurred:")
        print(json.dumps(result, indent=2))
