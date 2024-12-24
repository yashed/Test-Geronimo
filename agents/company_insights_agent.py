import os
from langchain.agents import Tool, initialize_agent, AgentExecutor
from langchain.agents import ZeroShotAgent
from langchain.memory import ConversationBufferMemory
from langchain_openai import AzureChatOpenAI
from langchain_google_community import GoogleSearchAPIWrapper
from langchain.schema import AIMessage, HumanMessage
import requests
import json

# Set environment variables for APIs
os.environ["OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
os.environ["OPENAI_API_TYPE"] = "azure"
os.environ["OPENAI_API_BASE"] = os.getenv("OPENAI_API_BASE")
os.environ["OPENAI_API_VERSION"] = os.getenv("OPENAI_API_VERSION")

# Initialize the Azure OpenAI model and memory
llm = AzureChatOpenAI(
    openai_api_key=os.environ["OPENAI_API_KEY"],
    deployment_name=os.getenv("OPENAI_DEPLOYMENT_NAME"),
    azure_endpoint=os.getenv("OPENAI_API_BASE"),
    temperature=0.7,
)
memory = ConversationBufferMemory(memory_key="chat_history")

# Define Google Search and Web Scraping tools
def google_search(query, num_results=5):
    google_search_tool = GoogleSearchAPIWrapper()
    return google_search_tool.results(query, num_results=num_results)

def web_scraping(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            return "Failed to retrieve data."
    except Exception as e:
        return f"Error occurred: {e}"

# Define functions for each required task
def get_person_summary(name, company_name):
    search_results = google_search(f"{name} {company_name}", num_results=8)
    search_text = " ".join([result['snippet'] for result in search_results])
    prompt = f"Summarize the following details about {name}, who works at {company_name}: {search_text}. The summary should be 300 words long."
    messages = [HumanMessage(content=prompt)]
    summary = llm(messages)
    return summary.content

def get_person_social_media(name, company_name):
    search_results = google_search(f"{name} {company_name} LinkedIn Facebook Instagram Medium", num_results=10)
    social_links = {}
    for result in search_results:
        if "linkedin.com" in result['link']:
            social_links["LinkedIn"] = result['link']
        elif "facebook.com" in result['link']:
            social_links["Facebook"] = result['link']
        elif "instagram.com" in result['link']:
            social_links["Instagram"] = result['link']
        elif "medium.com" in result['link']:
            social_links["Medium"] = result['link']
        if len(social_links) >= 3:
            break
    return social_links

def get_company_summary(company_name):
    search_results = google_search(f"{company_name} company profile", num_results=8)
    search_text = " ".join([result['snippet'] for result in search_results])
    prompt = f"Provide a detailed summary about the company {company_name}. Include information about their services, products, and other relevant details: {search_text}"
    messages = [HumanMessage(content=prompt)]
    summary = llm(messages)
    return summary.content

def get_company_competitors(company_name):
    search_results = google_search(f"{company_name} competitors", num_results=8)
    competitors = ", ".join([result['title'] for result in search_results])
    return {"competitors": competitors}

def get_company_latest_news(company_name, num_results=5):
    search_results = google_search(f"{company_name} latest news", num_results=num_results)
    news = []
    for result in search_results:
        news.append({
            "Title": result['title'],
            "URL": result['link'],
            "Description": result['snippet']
        })
    return news

# Define the tools
tools = [
    Tool(name="Google Search", func=google_search, description="Performs a Google search."),
    Tool(name="Web Scraping", func=web_scraping, description="Scrapes data from a website."),
    Tool(name="Person Summary", func=get_person_summary, description="Generates a summary about a person."),
    Tool(name="Social Media Links", func=get_person_social_media, description="Fetches social media links of a person."),
    Tool(name="Company Summary", func=get_company_summary, description="Generates a company summary."),
    Tool(name="Company Competitors", func=get_company_competitors, description="Identifies competitors of a company."),
    Tool(name="Company News", func=get_company_latest_news, description="Fetches the latest news about a company."),
]

# Initialize the LangChain agent
agent = initialize_agent(tools, llm, agent_type=ZeroShotAgent, memory=memory, verbose=True)

# Main function to gather information
def gather_info(name, job_title, company_name, country):
    print(f"Gathering information for {name}, {job_title} at {company_name} in {country}...")
    response = {}

    try:
        response["Personal Summary"] = get_person_summary(name, company_name)
    except Exception as e:
        response["Personal Summary"] = f"Error: {e}"

    try:
        response["Social Media Links"] = get_person_social_media(name, company_name)
    except Exception as e:
        response["Social Media Links"] = f"Error: {e}"

    try:
        response["Company Summary"] = get_company_summary(company_name)
    except Exception as e:
        response["Company Summary"] = f"Error: {e}"

    try:
        response["Company Competitors"] = get_company_competitors(company_name)
    except Exception as e:
        response["Company Competitors"] = f"Error: {e}"

    try:
        response["Company News"] = get_company_latest_news(company_name)
    except Exception as e:
        response["Company News"] = f"Error: {e}"

    return json.dumps(response, indent=4)

# Example usage
name = "Yashed Thisara"
job_title = "Developer"
company_name = "WSO2"
country = "Sri Lanka"

response = gather_info(name, job_title, company_name, country)
print(response)
