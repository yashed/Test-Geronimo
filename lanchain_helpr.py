import concurrent.futures
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os
from dotenv import load_dotenv
from langchain.chains import SequentialChain
from langchain_google_community import GoogleSearchAPIWrapper
import scraping_helper as sh
from langchain_community.chat_models import ChatOpenAI
from langchain.chat_models import AzureChatOpenAI
from mailService import send_mail
import json_helpr as jh

# Load environment variables
load_dotenv()

# Fetching the variables from the .env file
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")
OPENAI_DEPLOYMENT_NAME = os.getenv("OPENAI_DEPLOYMENT_NAME")
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION")

print("Google API Key - ", GOOGLE_API_KEY)
print("Google CSE ID - ", GOOGLE_CSE_ID)
print("OpenAI API Key - ", OPENAI_API_KEY)
print("OpenAI API Base - ", OPENAI_API_BASE)
print("OpenAI Deployment Name - ", OPENAI_DEPLOYMENT_NAME)
print("OpenAI API Version - ", OPENAI_API_VERSION)


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

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["OPENAI_API_TYPE"] = "Azure"
os.environ["OPENAI_API_VERSION"] = OPENAI_API_VERSION
os.environ["OPENAI_API_BASE"] = OPENAI_API_BASE

# Initialize ChatOpenAI model
llm = AzureChatOpenAI(
    openai_api_key=os.environ["OPENAI_API_KEY"],
    deployment_name=OPENAI_DEPLOYMENT_NAME,
    temperature=0.0,
)


def parallel_google_search(queries, num_results=8):
    """
    Perform Google searches in parallel.
    """
    google_search = GoogleSearchAPIWrapper()

    def fetch_results(query):
        return google_search.results(query, num_results=num_results)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(fetch_results, queries))
    return results


def parallel_web_scraping(results, queries):
    """
    Perform web scraping in parallel.
    """

    def scrape(result, query):
        link = result.get("link")
        if not link:
            return None
        return {
            "title": result.get("title"),
            "link": link,
            "snippet": result.get("snippet"),
            "content": sh.fetch_with_requests(link, query),
        }

    combined_results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for query_results, query in zip(results, queries):
            scraped_data = list(
                executor.map(lambda res: scrape(res, query), query_results)
            )
            combined_results.append(
                [data for data in scraped_data if data]
            )  # Filter out None results

    return combined_results


def fetch_top_google_results(
    name, company, num_results=5, company_flag=0, competitors=0 , news=0
):
    """
    Fetch Google search results and scrape the content in parallel.
    """
    queries = []
    if company_flag == 1:  # Get company information
        queries.append(f"{company}")
    elif company_flag == 0 and competitors == 0 and news == 0:  # Get personal information
        queries.append(f"{name} in {company}")
    elif competitors == 1 and company_flag == 0 and news == 0:  # Get company competitors
        queries.append(f"{company} competitors")
    elif news == 1 and company_flag == 0 and competitors == 0:  # Get company news
        queries.append(f"{company} recent news")

    print("Queries:", queries)

    try:
        search_results = parallel_google_search(queries, num_results=num_results)

        # Perform parallel web scraping for each query's results
        scraped_results = parallel_web_scraping(search_results, queries)
        return scraped_results[0] if scraped_results else []

    except Exception as e:
        print(f"Error during search or processing: {e}")
        return []


def generate_data(name, company, position, country):

    # Fetch Google results
    person_google_results = fetch_top_google_results(name, company)
    company_google_results = fetch_top_google_results(
        name, company, num_results=3, company_flag=1
    )
    company_competitors_results = fetch_top_google_results(
        name, company, num_results=4, competitors=1
    )
    company_news_results = fetch_top_google_results(name , company, num_results=10, news=1)

    print("Company Competitors - ", company_competitors_results)

    # Format Google results for input into the prompts
    formatted_person_results = "\n\n".join(
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

    # to get social media links
    formatted_links = "\n".join(
        [
            f"{res['title']}\nLink: {res['link']}\nSnippet: {res['snippet']}\nContent: {res['content']}"
            for res in person_google_results
        ]
    )

    # to get company competitors
    formatted_competitors = "\n\n".join(
        [
            f"Title: {res['title']}\nLink: {res['link']}\nSnippet: {res['snippet']}\nContent: {res['content']}"
            for res in company_competitors_results
        ]
    )
    
    # to get company news
    formatted_news = "\n\n".join(
        [
            f"Title: {res['title']}\nLink: {res['link']}\nSnippet: {res['snippet']}\nContent: {res['content']}"
            for res in company_news_results
        ]
    )

    print("Formatted Results - ", formatted_competitors)

    # First chain: Generate a concise professional summary
    prompt_template_summary = PromptTemplate(
        input_variables=["name", "company", "position", "google_results"],
        template=(
            "Provide a detailed and unbiased summary about {name}, who is currently associated with {company} as a {position}. "
            "Keep the summary around 120 words and Include key details about their career, areas of interest, significant achievements, and any other notable or unique aspects about them. "
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

    # Fourth chain: Competitors of the company
    prompt_template_competitors = PromptTemplate(
        input_variables=["company", "company_competitors_results"],
        template=(
            "Based on the following Google Search results for {company}'s competitors, extract a concise list containing only the names of competitor companies. "
            "Strictly avoid including product names, services, or any unrelated details. "
            "Provide 3 to 5 of the most significant competitors based on the search results. "
            "If no valid company names can be identified, respond with 'No competitors found.' "
            "Ensure that only competitor company names are returned, and sort the list alphabetically.\n\n"
            "Google Search Results: {company_competitors_results}\n\n"
            "Competitor Company Names:"
        ),
    )

    chain_competitors = LLMChain(
        llm=llm, prompt=prompt_template_competitors, output_key="company_competitors"
    )
    
    # Fifth chain: Company News
    prompt_template_news = PromptTemplate(
        input_variables=["company", "company_news_results"],
        template=(
            "Based on the following Google Search results for {company}'s recent news, provide a JSON-formatted summary of the top 3 to 5 most relevant news articles from the last 12 months. "
            "Focus on articles related to the company's financial performance, major partnerships, executive changes, or significant industry developments. "
            "For each article, include the following details:\n"
            "- 'title': A clear , detailed and accurate title that gives a precise idea of the news.\n"
            "- 'url': The link to the news article.\n"
            "- 'description': A concise but informative summary of the news content, not exceeding 100 words.\n"
            "If no valid news articles are found, respond with 'No recent news found.'\n\n"
            "Google Search Results: {company_news_results}\n\n"
            "Company News Json:"
        ),
    )
    
    chain_news = LLMChain(
        llm=llm, prompt=prompt_template_news, output_key="company_news"
        )


    # Combine the two chains into a SequentialChain
    chain = SequentialChain(
        chains=[
            chain_summary,
            chain_social_links,
            chain_company_summary,
            chain_competitors,
            chain_news
        ],
        input_variables=[
            "name",
            "company",
            "position",
            "google_results",
            "google_links",
            "country",
            "google_company_results",
            "company_competitors_results",
            "company_news_results",
        ],
        output_variables=[
            "professional_summary",
            "social_media_links",
            "company_summary",
            "company_competitors",
            "company_news",
        ],
    )

    # Execute the SequentialChain
    response = chain.invoke(
        {
            "name": name,
            "company": company,
            "position": position,
            "google_results": formatted_person_results,
            "google_links": formatted_links,
            "country": country,
            "google_company_results": formatted_company_results,
            "company_competitors_results": formatted_competitors,
            "company_news_results": formatted_news
        }
    )

    # Send the email with the response data
    send_mail(response)

    return format_response(response)


# summazing the scraped content
def summarize_large_content(content, query, chunk_size=10000, overlap=200):

    chunks = []
    start = 0
    while start < len(content):
        end = min(start + chunk_size, len(content))
        chunks.append(content[start:end])
        start += chunk_size - overlap

    # Define a refined prompt template to focus on meaningful summary
    prompt_template = PromptTemplate(
        input_variables=["query", "chunk"],
        template=(
            "You are a summarization assistant. Based on the following query, summarize the content provided below. "
            "Give detailed summary with including nearly 200 words. "
            "Focus only on the relevant information related to the query. Ignore and remove irrelevant data such as "
            "phone numbers, personal names, addresses, or any other unrelated information that does not contribute to answering the query.\n\n"
            "This is web-scraped content, and your task is to produce a summary that is most meaningful and relevant to the query, "
            "Summary should be related to the Query"
            "without including any unnecessary details.\n\n"
            "Query: {query}\n\n"
            "Content:\n{chunk}\n\n"
            "Summary:"
        ),
    )

    chain = LLMChain(llm=llm, prompt=prompt_template)

    # Generate summaries for each chunk
    chunk_summaries = []
    for i, chunk in enumerate(chunks):
        # print(f"Summarizing chunk {i + 1}/{len(chunks)}...")
        chunk_summary = chain.run({"query": query, "chunk": chunk})
        chunk_summaries.append(chunk_summary)

    combined_summary = "\n".join(chunk_summaries)

    # If the combined summary is still too long, summarize it again
    if len(combined_summary) > chunk_size:
        final_summary = chain.run({"query": query, "chunk": combined_summary})
        return final_summary

    return combined_summary


# function to format the content into json
def format_response(response_data):

    # Extracting details from response_data
    professional_summary = response_data.get("professional_summary", "")
    company_summary = response_data.get("company_summary", "")
    social_media_links_raw = response_data.get("social_media_links", "")
    company_competitors_raw = response_data.get("company_competitors", "")
    company_news_raw = response_data.get("company_news", "")
    
    print("Company News Raw - ", company_news_raw)
    
    #convert company_news_raw to json
    company_news_json = jh.format_json_string(company_news_raw)
    print("Company News JSON - ", company_news_json)

    # Parse social media links into the required format
    social_media_links = {}
    for line in social_media_links_raw.split("\n"):
        if "-" in line:
            key, value = map(str.strip, line.split("-", 1))
            social_media_links[key] = value

    # Parse company competitors into a comma-separated list
    company_competitors = ", ".join(
        [
            competitor.strip()
            for competitor in company_competitors_raw.split("\n")
            if competitor.strip()
        ]
    )

    # Create the final formatted JSON object
    formatted_json = {
        "professional_summary": professional_summary,
        "social_media_links": social_media_links,
        "company_summary": company_summary,
        "company_competitors": company_competitors,
        "company_news": company_news_json
    }

    return formatted_json
