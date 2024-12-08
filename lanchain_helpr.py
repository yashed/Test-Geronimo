from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os
from dotenv import load_dotenv
from langchain.chains import SequentialChain
from langchain.utilities import GoogleSearchAPIWrapper
import scraping_helper as sh
from langchain_community.chat_models import ChatOpenAI


# Load environment variables
load_dotenv()

# Fetching the variables from the .env file

GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("AZURE_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")
OPENAI_DEPLOYMENT_NAME = os.getenv("OPENAI_DEPLOYMENT_NAME")
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION")

# Ensure all variables are set correctly
if not all(
    [
        GOOGLE_CSE_ID,
        GOOGLE_API_KEY,
        OPENAI_API_KEY,
        OPENAI_API_BASE,
        OPENAI_DEPLOYMENT_NAME,
        OPENAI_API_VERSION,
    ]
):
    raise ValueError("Please ensure all the necessary environment variables are set.")


# installe bellows
# pip install -U langchain-community openai==0.28


print("APi Key - ", OPENAI_API_KEY)
print("API Base - ", OPENAI_API_BASE)
print("Deployment Name - ", OPENAI_DEPLOYMENT_NAME)
print("API Version - ", OPENAI_API_VERSION)

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["OPENAI_API_TYPE"] = "Azure"
os.environ["OPENAI_API_VERSION"] = OPENAI_API_VERSION
os.environ["OPENAI_API_BASE"] = OPENAI_API_BASE


# Initialize ChatOpenAI model (correct method for chat-based models)
llm = ChatOpenAI(
    openai_api_key=OPENAI_API_KEY,
    engine=OPENAI_DEPLOYMENT_NAME,
    model="gpt-4",  
    temperature=0.7,  
)


def fetch_top_google_results(name, company, num_results=8 , company_flag = 0):
    
    if company_flag == 1:
        query = f"{name} {company}"
    elif company_flag == 0:
        query = f"{name} in {company}"
    

    google_search = GoogleSearchAPIWrapper()

    search_results = google_search.results(query, num_results=num_results)
    results = []
    
    print("Search Results - ", search_results)
    for result in search_results:

        link = result.get("link")
        page_content = sh.fetch_with_requests(link) if link else "No content available"
        # print(page_content)

        results.append(
            {
                "title": result.get("title"),
                "link": link,
                "snippet": result.get("snippet"),
                "content": page_content,
            }
        )
    return results


def generate_data(name, company, position,country):

    # Fetch Google results
    person_google_results = fetch_top_google_results(name, company)
    company_google_results = fetch_top_google_results(name, company, num_results=3 , company_flag = 1)

    # Format Google results for input into the prompts
    formatted_results = "\n\n".join(
        [
            f"Title: {res['title']}\nLink: {res['link']}\nSnippet: {res['snippet']}\nContent: {res['content']}"
            for res in person_google_results
        ]
    )
    
    # Format Company Google results for input into the prompts
    formatted_company_results = "\n\n".join(
        [
            f"Title: {res['title']}\nLink: {res['link']}\nSnippet: {res['snippet']}\nContent: {res['content']}"
            for res in company_google_results
        ]
    )
    
    #to get social media links
    formatted_links = "\n".join(
        [
            f"{res['title']}:{res['link']}"
            for res in person_google_results
        ]
    )

    # First chain: Generate a concise professional summary
    prompt_template_summary = PromptTemplate(
        input_variables=["name", "company", "position", "google_results"],
        template=(
            "Provide a detailed and unbiased summary about {name}, who is currently associated with {company} as a {position}. "
            "Keep the summary around 100 words and Include key details about their career, areas of interest, significant achievements, and any other notable or unique aspects about them. "
            "Mention any relevant insights or interesting facts that could help a team initiate an engaging and informed conversation with this person. "
            "Use only the most accurate and relevant information from the provided Google Search Results. "
            "Be mindful that not all search results may pertain to this individual; filter out any unrelated or incorrect data. "
            "Google Search Results: {google_results}\n\n"
            "Summary: "
        ),
    )

    chain_summary = LLMChain(
        llm=llm, prompt=prompt_template_summary, output_key="professional_summary"
    )

    # Second chain: Extract social media links
    prompt_template_social_links = PromptTemplate(
        input_variables=["name", "company", "position", "google_links"],
        template=(
            "Extract and list the most accurate and relevant social media links for {name} based on the provided Google Search Results. "
            "There can be some false positives, so ensure the links are valid and related to the person not for any organization. "
            "Prioritize LinkedIn if available, followed by other platforms like Twitter, GitHub, personal websites, Blog Sites like Medium. "
            "Ensure that only accurate and valid links are included. Do not include any links that are not related to the person like organizations social media links. "
            "Just give the [platform name]-[URL], remove additional information. "
            "Google Search Results with Links: {google_links}\n\n"
            "Social Media Links: "
        ),
    )

    chain_social_links = LLMChain(
        llm=llm, prompt=prompt_template_social_links, output_key="social_media_links"
    )
    
    # Third chain: Summary of the company
    prompt_template_company_summary = PromptTemplate(
        input_variables=["company", "country", "google_company_results"],
        template=(
            "Based on the provided Google Search Results, create a concise yet detailed summary about {company}, highlighting the following key points:"
            "\n1. A brief overview of what the company does."
            "\n2. The countries or regions where the company operates."
            "\n3. The main services and products the company offers."
            "\n4. Any notable achievements, milestones, or unique aspects about the company."
            "\n5. Relevant and engaging insights to help initiate informed conversations."
            "Ensure that the summary is accurate, unbiased, and limited to around 100 words. "
            "Filter out any unrelated or incorrect data from the Google Search Results."
            "\n\nGoogle Search Results: {google_company_results}\n\n"
            "Summary:"
        ),
    )

    
    chain_company_summary = LLMChain(
        llm=llm, prompt=prompt_template_company_summary, output_key="company_summary"
    )

    # Combine the two chains into a SequentialChain
    chain = SequentialChain(
        chains=[chain_summary, chain_social_links, chain_company_summary],
        input_variables=["name", "company", "position", "google_results", "google_links", "country","google_company_results"],
        output_variables=["professional_summary", "social_media_links", "company_summary"],
    )

    # Execute the SequentialChain
    response = chain.invoke(
        {
            "name": name,
            "company": company,
            "position": position,
            "google_results": formatted_results,
            "google_links": formatted_links,
            "country": country,
            "google_company_results": formatted_company_results,
        }
    )

    return response
