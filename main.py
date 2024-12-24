import os
from langchain.agents import initialize_agent, Tool
from langchain.agents import ZeroShotAgent
from langchain.memory import ConversationBufferMemory
from langchain_openai import AzureChatOpenAI
from langchain_google_community import GoogleSearchAPIWrapper
from langchain.schema import AIMessage, HumanMessage
import requests
import json

# Environment Variables Setup
os.environ["OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
os.environ["OPENAI_API_TYPE"] = "azure"
os.environ["OPENAI_API_BASE"] = os.getenv("OPENAI_API_BASE")
os.environ["OPENAI_API_VERSION"] = os.getenv("OPENAI_API_VERSION")

# Initialize Language Model and Memory
llm = AzureChatOpenAI(
    openai_api_key=os.environ["OPENAI_API_KEY"],
    deployment_name=os.getenv("OPENAI_DEPLOYMENT_NAME"),
    azure_endpoint=os.getenv("OPENAI_API_BASE"),
    temperature=0.7,
)
memory = ConversationBufferMemory(memory_key="chat_history")

# Define Helper Functions for Tools
def google_search(query, num_results=5):
    google_search_tool = GoogleSearchAPIWrapper()
    return google_search_tool.results(query, num_results=num_results)

def web_scraping(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return f"Scraped data from {url}: {response.text[:300]}..."
        else:
            return f"Failed to retrieve data from {url}"
    except Exception as e:
        return f"Error occurred while scraping: {e}"

def summarize_text(text):
    messages = [HumanMessage(content=f"Summarize the following information: {text}")]
    summary = llm(messages)
    return summary.content

# Define Tools
tools = [
    Tool(
        name="Google Search",
        func=google_search,
        description="Use this tool to search Google for any query."
    ),
    Tool(
        name="Web Scraping",
        func=web_scraping,
        description="Scrape content from a given URL."
    ),
    Tool(
        name="Summarize Information",
        func=summarize_text,
        description="Summarize lengthy text into concise information."
    )
]

# Initialize Agent
agent = initialize_agent(tools=tools,
    llm=llm,
    memory=ConversationBufferMemory(),
    handle_parsing_errors=True , verbose=True)

# Main Function

def gather_info(name, job_title, company_name, country):
    query = (
        f"You are an agent tasked with gathering accurate information about a person and their company. "
        f"The details provided are: Name: {name}, Job Title: {job_title}, Company: {company_name}, Country: {country}. "
        f"Generate a JSON response with the following keys: \n"
        f"1. 'personal_summary': A 300-word summary about the person, including their current role, areas of focus, and interests.\n"
        f"2. 'social_media_links': A JSON object with the person's social media URLs (LinkedIn, Twitter, Facebook, etc.).\n"
        f"3. 'company_summary': A summary of the company, including its services and products.\n"
        f"4. 'company_competitors': Competitor company names separated by commas.\n"
        f"5. 'company_news': Latest 3-5 news articles about the company, each including title, URL, and a brief description. "
        f"If data is insufficient, use the tools to gather more information."
    )

    # Agent Processes Query
    response = agent.run(query)

    # Format JSON Response
    return response

# Example Usage
if __name__ == "__main__":
    name = "Yashed Thisara"
    job_title = "Developer"
    company_name = "WSO2"
    country = "Sri Lanka"

    result = gather_info(name, job_title, company_name, country)
    print(result)
