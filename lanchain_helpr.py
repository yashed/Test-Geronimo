from langchain.agents import initialize_agent, Tool, ZeroShotAgent
from langchain.memory import ConversationBufferMemory
from langchain_openai import AzureChatOpenAI
from langchain_google_community import GoogleSearchAPIWrapper
from langchain.schema import AIMessage, HumanMessage
import requests
import os
import json

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
def google_search(query, num_results=8, use_serper=True):
    if use_serper:
        # Serper API call
        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": query, "num": num_results})
        headers = {"X-API-KEY": X_API_KEY, "Content-Type": "application/json"}

        response = requests.request("POST", url, headers=headers, data=payload)

        if response.status_code == 200:
            return response.json().get("organic", [])
        else:
            return {
                "error": f"Serper request failed with status code {response.status_code}"
            }

    else:
        # GoogleSearchAPIWrapper call
        google_search_tool = GoogleSearchAPIWrapper()
        return google_search_tool.results(query, num_results=num_results)


def web_scraping(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text[:500]  # Return first 500 characters of the response
        else:
            return f"Failed to retrieve data from {url}"
    except Exception as e:
        return str(e)


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
    agent_type=ZeroShotAgent,
    memory=memory,
    handle_parsing_errors=True,
    verbose=True,
    max_iterations=10,
)


# Main Function
def gather_info(name, job_title, company_name, country):
    query = (
        f"You are an intelligent agent tasked with collecting information about a person and their company. "
        f"The inputs are: Name: {name}, Job Title: {job_title}, Company: {company_name}, Country: {country}. "
        f"Your output must be a JSON object with the following keys:\n"
        f"1. 'personal_summary': A detailed 300-word summary about the person, focusing on their professional achievements and background.\n"
        f"2. 'social_media_links': A JSON object with the person's most accurate social media URLs. Include only verified and relevant profiles for platforms like LinkedIn, Twitter, GitHub, or others the person actively uses. Also, suggest other relevant links related to the person, such as personal blogs, portfolio websites, or interview pages.\n"
        f"3. 'company_summary': A comprehensive summary of the company's services, products, and market presence.\n"
        f"4. 'company_competitors': A list of competitor company names in the same domain , not product names, separated by commas.\n"
        f"5. 'company_news': A list of the recent 3 to 5 news articles about the company. News aetical needs to be recent one for today For each article, provide:\n"
        f"    - 'title': A clear and accurate title that gives a precise idea of the news.\n"
        f"    - 'url': The link to the news article.\n"
        f"    - 'description': A detailed summary of the news content. The summary must include the main points and be concise but informative, not exceeding 100 words.\n"
        f"If you lack data, use tools like Google Search and Web Scraping to gather more information. Ensure all information is verified, reliable, and formatted correctly."
    )

    best_result = None
    iteration_results = []
    for i in range(agent.max_iterations):
        try:
            response = agent.run(query)
            iteration_results.append(response)

            if all(
                key in response
                for key in [
                    "personal_summary",
                    "social_media_links",
                    "company_summary",
                    "company_competitors",
                    "company_news",
                ]
            ):
                best_result = response
                break
        except Exception as e:
            iteration_results.append({"error": str(e)})

    # Select the most complete and accurate result from all iterations
    if not best_result:
        best_result = max(
            iteration_results, key=lambda res: len(res) if isinstance(res, dict) else 0
        )

    return best_result


# Main Function to Test the Code
if __name__ == "__main__":

    name = "Yashed Thisara"
    job_title = "Developer"
    company_name = "WSO2"
    country = "Sri Lanka"

    result = gather_info(name, job_title, company_name, country)
    print("Type of Result = ", type(result))
    print("Response = ", result)
