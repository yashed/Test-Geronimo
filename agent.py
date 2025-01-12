# This code breaks down a single, large query into three smaller, focused ones:
# 1. Personal information: Finds a detailed summary and social media links for the person.
# 2. Company information: Collects a summary of the company and its competitors.
# 3. Company news: Gathers the latest news articles about the company.
# Splitting the query this way helps avoid hitting the agent's iteration limit and makes it easier to get accurate and reliable results for each part.

# Need to change quearies becasue if data can find then agent generate various quearies to get google data
# Need to give a planer to the agent to get the data
# Need to guide the agent to get the data from the google search


from langchain.agents import initialize_agent, Tool, ZeroShotAgent
from langchain.memory import ConversationBufferMemory
from langchain_openai import AzureChatOpenAI
from langchain_google_community import GoogleSearchAPIWrapper
from langchain.schema import AIMessage, HumanMessage
import requests
import os
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from typing import Dict, List, Any, Union
import time
import os
from typing import Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
import json
import time
import os
from typing import Dict, Any, Optional
from fake_useragent import UserAgent

load_dotenv(override=True)

# Initialize Environment Variables
os.environ["OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
os.environ["OPENAI_API_TYPE"] = "azure"
os.environ["OPENAI_API_BASE"] = os.getenv("OPENAI_API_BASE")
os.environ["OPENAI_API_VERSION"] = os.getenv("OPENAI_API_VERSION")

SERPER_API_KEY = os.getenv("SERPER_API_KEY")
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

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
        headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}

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


# class LinkedInProfileScraper:
#     def __init__(self, email: str, password: str):
#         self.email = email
#         self.password = password
#         self.session = requests.Session()
#         self.headers = {
#             "User-Agent": UserAgent().random,
#             "Accept": "application/json",
#             "Accept-Language": "en-US,en;q=0.9",
#         }
#         self.session.headers.update(self.headers)

#     def login(self) -> bool:
#         """
#         Login to LinkedIn using credentials
#         """
#         try:
#             # Get the login page first to get the CSRF token
#             login_page = self.session.get("https://www.linkedin.com/login")
#             soup = BeautifulSoup(login_page.content, "html.parser")
#             csrf = soup.find("input", {"name": "loginCsrfParam"}).get("value", "")

#             login_data = {
#                 "session_key": self.email,
#                 "session_password": self.password,
#                 "loginCsrfParam": csrf,
#             }

#             response = self.session.post(
#                 "https://www.linkedin.com/checkpoint/lg/login-submit",
#                 data=login_data,
#                 allow_redirects=True,
#             )

#             return response.status_code == 200 and "feed" in response.url

#         except Exception as e:
#             print(f"Login failed: {str(e)}")
#             return False

#     def extract_profile_data(self, html_content: str) -> Dict[str, Any]:
#         """
#         Extract profile information from HTML content
#         """
#         soup = BeautifulSoup(html_content, "html.parser")
#         profile_data = {}

#         try:
#             # Basic information
#             profile_data["name"] = soup.find(
#                 "h1", {"class": "text-heading-xlarge"}
#             ).text.strip()
#             profile_data["headline"] = soup.find(
#                 "div", {"class": "text-body-medium"}
#             ).text.strip()

#             # About section
#             about_section = soup.find("div", {"class": "inline-show-more-text"})
#             profile_data["about"] = (
#                 about_section.text.strip() if about_section else "Not found"
#             )

#             # Experience section
#             experience_section = soup.find("section", {"id": "experience-section"})
#             profile_data["experience"] = []

#             if experience_section:
#                 experiences = experience_section.find_all(
#                     "li", {"class": "artdeco-list__item"}
#                 )
#                 for exp in experiences[:3]:  # Get first 3 experiences
#                     title = exp.find("h3", {"class": "profile-section-card__title"})
#                     company = exp.find("p", {"class": "profile-section-card__subtitle"})

#                     if title and company:
#                         profile_data["experience"].append(
#                             {
#                                 "title": title.text.strip(),
#                                 "company": company.text.strip(),
#                             }
#                         )

#             # Education section
#             education_section = soup.find("section", {"id": "education-section"})
#             profile_data["education"] = []

#             if education_section:
#                 educations = education_section.find_all(
#                     "li", {"class": "artdeco-list__item"}
#                 )
#                 for edu in educations:
#                     school = edu.find("h3", {"class": "profile-section-card__title"})
#                     degree = edu.find("p", {"class": "profile-section-card__subtitle"})

#                     if school:
#                         profile_data["education"].append(
#                             {
#                                 "school": school.text.strip(),
#                                 "degree": (
#                                     degree.text.strip() if degree else "Not specified"
#                                 ),
#                             }
#                         )

#             return profile_data

#         except Exception as e:
#             return {"error": f"Failed to extract profile data: {str(e)}"}

#     def get_profile(self, profile_url: str) -> Dict[str, Any]:
#         """
#         Get profile data from LinkedIn URL
#         """
#         try:
#             if not self.login():
#                 return {"error": "Failed to login to LinkedIn"}

#             # Add delay to avoid rate limiting
#             time.sleep(2)

#             response = self.session.get(profile_url)
#             if response.status_code != 200:
#                 return {
#                     "error": f"Failed to fetch profile. Status code: {response.status_code}"
#                 }

#             return self.extract_profile_data(response.text)

#         except Exception as e:
#             return {"error": f"Failed to get profile: {str(e)}"}

#         finally:
#             self.session.close()


# def linkedin_profile_tool(url: str) -> Dict[str, Any]:
#     """
#     Tool function for integrating with agent services.
#     Requires LinkedIn credentials in environment variables:
#     LINKEDIN_EMAIL and LINKEDIN_PASSWORD
#     """
#     linkedin_email = os.getenv("LINKEDIN_EMAIL")
#     linkedin_password = os.getenv("LINKEDIN_PASSWORD")

#     if not linkedin_email or not linkedin_password:
#         return {"error": "LinkedIn credentials not found in environment variables"}

#     scraper = LinkedInProfileScraper(linkedin_email, linkedin_password)
#     return scraper.get_profile(url)


# Add this to your existing tools list


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
    # Tool(
    #     name="LinkedIn Profile Scraper",
    #     func=linkedin_profile_tool,
    #     description="Scrape detailed information from a LinkedIn profile URL. Returns profile data including name, headline, about section, and experience.",
    # ),
]

# Agent Initialization
memory = ConversationBufferMemory(memory_key="chat_history")
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent_type="zero-shot-react-description",
    memory=memory,
    handle_parsing_errors=True,
    verbose=True,
    max_iterations=10,
)


def gather_info(
    name: str, job_title: str, company_name: str, country: str
) -> Dict[str, Any]:
    """
    Gathers information about a person, their company, and related news.

    Args:
        name (str): Name of the person.
        job_title (str): Job title of the person.
        company_name (str): Name of the company the person works at.
        country (str): Country where the company operates.

    Returns:
        Dict[str, Any]: A dictionary containing personal summary, social media links,
                        company information, and recent news, along with any errors encountered.
    """

    # Breaking down into smaller queries

    # Get Personal Summary from the agent
    def get_personal_summary() -> Dict[str, Any]:
        """Fetches a detailed personal summary of the individual."""
        personal_summary_query = f"""Find and return information about {name} who works as {job_title} at {company_name} in {country}.
        Search instructions:
        1. If it gives only the fist name then use company name and country to get search results and if it gives full name then first use full name to get search results, if not found then use company name and country to get search results.
        2. Use search terms for personal data like "{name}" , "{name} in {company_name}", "{name} {job_title} in {company_name}", "{name} {job_title} {country}"
        3. Do maximum 5 searches to get the data 
        4. Use web Scraping tool to get the data from the google search results if it is possible.
        5. IMPORTANT: if the scraped content is too long, try to summarize it to 300 words or less to provide a concise summary about person.
        3. Focus on the most accurate and up-to-date information available

        {{
            "personal_summary": "<A detailed 300-word summary about the person, focusing on their professional achievements and background.>",
        }}"""

        response = agent.invoke(input={"input": personal_summary_query})
        return extract_json(response)

    # Get Social Media Links from the agent
    def get_social_media_links() -> Dict[str, Any]:
        """Fetches verified social media and relevant online profiles of the individual."""
        social_media_query = f"""Find and return social media information about {name} who works as {job_title} at {company_name}.
        Search instructions:
        1. Try to use minimum searches to get the data, use "{name}", {name} in {company_name}" like queries and identify the social media or person related platform links.
        2. or Use search terms for social media like "{name} in {company_name}, LinkedIn {name} in {company_name}", "Twitter {name}", "personal blog {name}", "portfolio website {name}"
        3. Include only verified and relevant profiles for platforms like LinkedIn, Twitter, Facebook. Suggest other relevant links related to the person, such as personal blogs, portfolio websites, or Company Profile pages any other accurate platform links.
        3. IMPORTANT: Focus on the most accurate and up-to-date information available

        {{
            "social_media_links": [
                {{
                    "platform": "<Platform Name>",
                    "url": "<Direct URL to the person's profile on the platform>"
                }}
            ]
        }}"""

        response = agent.invoke(input={"input": social_media_query})
        return extract_json(response)

    # Get Company Information from the agent: Company Summary and Competitors
    def get_company_info() -> Dict[str, Any]:
        """Fetches a summary of the company and its main competitors."""
        company_query = f"""Research {company_name} and return information in this exact JSON format:
        {{
            "company_summary": "<comprehensive company summary with nearly 250 words>",
            "company_competitors": "<3-5 main competitors, give only company names not product names, separated by commas>"
        }}"""

        response = agent.invoke(input={"input": company_query})
        return extract_json(response)

    # Get News Information from the agent: Company News
    def get_news_info() -> Dict[str, Any]:
        """Fetches the most recent news articles about the company."""
        news_query = f"""Find 3-5 MOST RECENT news articles about {company_name}. 

        Search instructions:
        1. Use only search terms like "latest news {company_name}", "recent announcements {company_name}", "{company_name} News", "{company_name} launches", "latest updates of {company_name} in {country}", "most recent News in {company_name}"
        2. IMPORTANT: Focus ONLY on the newest and most recent news without using specific dates in your search
        3. Use filters and search techniques to get the most recent results first
        4. Prioritize official company press releases and major tech news websites
        5. minimum number of news articles is 1 and maximum is 5
         

        Return the data in this exact JSON format:
        {{
            "company_news": [
                {{
                    "title": "<A short and precise title that provides an overall idea of the news. Avoid lengthy phrases>",
                    "url": "<direct URL to the news article, give only one URL>",
                    "description": "<100-word summary focusing on key announcements and impacts>"
                }},
                {{
                    "title": "<A short and precise title that provides an overall idea of the news. Avoid lengthy phrases>",
                    "url": "<direct URL to the news article, give only one URL>",
                    "description": "<100-word summary focusing on key announcements and impacts>"
                }}
            ]
        }}
    
    Remember: Only include the MOST RECENT news articles. Do not use specific dates in your search. Focus on terms like 'latest', 'recent', 'newest', and 'just announced' to find current information."""

        response = agent.invoke(input={"input": news_query})
        return extract_json(response)

    def extract_json(response: Any) -> Dict[str, Any]:
        """Parses the agent's response to extract JSON data."""
        try:
            print("Response = ", response)
            if isinstance(response, dict) and "output" in response:
                response_text = response["output"]
            else:
                response_text = str(response)

            # Try to find and parse JSON
            import re

            json_match = re.search(r"\{[\s\S]*\}", response_text)
            if json_match:
                return json.loads(json_match.group(0))
            return {"error": "No JSON found in response"}
        except Exception as e:
            return {"error": f"JSON parsing error: {str(e)}"}

    try:
        import concurrent.futures

        # Execute all tasks in parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_personal_summary = executor.submit(get_personal_summary)
            future_social_media = executor.submit(get_social_media_links)
            future_company_info = executor.submit(get_company_info)
            future_news_info = executor.submit(get_news_info)

            personal_summary_data = future_personal_summary.result()
            print("personal_summary_data = ", personal_summary_data)
            social_media_data = future_social_media.result()
            company_data = future_company_info.result()
            news_data = future_news_info.result()

        """Uncomment the below code and comment the above code to run the tasks in parallel"""
        # personal_summary_data = get_personal_summary()
        # social_media_data = get_social_media_links()
        # company_data = get_company_info()
        # news_data = get_news_info()

        # Check for errors in any response
        error_messages = []
        if any(
            "error" in x
            for x in [personal_summary_data, social_media_data, company_data, news_data]
        ):
            if "error" in personal_summary_data:
                error_messages.append(
                    f"Personal Summary: {personal_summary_data['error']}"
                )
            if "error" in social_media_data:
                error_messages.append(f"Social Media: {social_media_data['error']}")
            if "error" in company_data:
                error_messages.append(f"Company: {company_data['error']}")
            if "error" in news_data:
                error_messages.append(f"News: {news_data['error']}")

        # Combine all data into final format
        final_result = {
            "personal_summary": personal_summary_data.get(
                "personal_summary", "Not available"
            ),
            "social_media_links": social_media_data.get(
                "social_media_links", "Not available"
            ),
            "company_summary": company_data.get("company_summary", "Not available"),
            "company_competitors": company_data.get(
                "company_competitors", "Not available"
            ),
            "company_news": news_data.get("company_news", "Not available"),
            "errors": error_messages,
        }

        print("Final Result = ", final_result)
        return final_result

    except Exception as e:
        return {"error": "Error in data gathering process", "details": str(e)}


# Main execution code
if __name__ == "__main__":
    test_inputs = {
        "name": "Malith Jayasinghe",
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
