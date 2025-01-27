import concurrent.futures
from langchain.prompts import PromptTemplate
import requests
import json
from langchain.chains import LLMChain
import os
from dotenv import load_dotenv
from langchain.chains import SequentialChain
from langchain_google_community import GoogleSearchAPIWrapper
from langchain_community.chat_models import ChatOpenAI
from langchain.chat_models import AzureChatOpenAI
from . import json_helper as jh
from . import scraping_helper as sh

# Load environment variables
load_dotenv(override=True)

# Fetching the variables from the .env file
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")
OPENAI_DEPLOYMENT_NAME = os.getenv("OPENAI_DEPLOYMENT_NAME")
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

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
        SERPER_API_KEY,
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


# Function to perform a Google search using the Serper API
def google_search(query, num_results=8, use_google_api=False):
    """
    Perform a search using either the Serper API or the Google Search API.

    Args:
        query (str): The search query.
        num_results (int): Number of results to retrieve.
        use_google_api (bool): If True, use the Google Search API. If False, use Serper API.

    Returns:
        list: Search results.
    """
    if use_google_api:
        # Use Google Search API
        google_search_wrapper = GoogleSearchAPIWrapper()
        try:
            return google_search_wrapper.results(query, num_results=num_results)
        except Exception as e:
            print(f"Error: Google Search API failed with error: {e}")
            return []
    else:
        # Use Serper API
        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": query, "num": num_results})
        headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}

        response = requests.post(url, headers=headers, data=payload)
        if response.status_code == 200:
            return response.json().get("organic", [])
        else:
            print(
                f"Error: Serper request failed with status code {response.status_code}"
            )
            return []


def parallel_google_search(queries, num_results=8, use_google_api=False):
    """
    Perform parallel searches for multiple queries using either Serper API or Google Search API.

    Args:
        queries (list of str): A list of search queries.
        num_results (int): Number of results to retrieve for each query.
        use_google_api (bool): If True, use the Google Search API. If False, use Serper API.

    Returns:
        list of list: A list where each element contains the search results for a query.
    """

    def fetch_results(query):
        return google_search(
            query, num_results=num_results, use_google_api=use_google_api
        )

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(fetch_results, queries))
    return results


def parallel_web_scraping(results, queries):
    """
    Perform web scraping in parallel.

    Args:
        results (list of list): A list of search results for each query.
        queries (list of str): A list of search queries.
    Returns:
        list of list: A list where each element contains the scraped data for a query.
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
            combined_results.append([data for data in scraped_data if data])

    return combined_results


def fetch_top_google_results(
    name, company, num_results=5, company_flag=0, competitors=0, news=0
):
    """
    Fetch Google search results and scrape the content in parallel.

    Args:
        name (str): The name of the person.
        company (str): The name of the company.
        num_results (int): Number of results to retrieve.
        company_flag (int): Flag to indicate whether to get company information.
        competitors (int): Flag to indicate whether to get company competitors.
        news (int): Flag to indicate whether to get company news.
    Return:
        list: A list of dictionaries containing the scraped data for each result.
    """
    queries = []
    if company_flag == 1:  # Get company information
        queries.append(f"{company}")
    elif (
        company_flag == 0 and competitors == 0 and news == 0
    ):  # Get personal information
        queries.append(f"{name} in {company}")
    elif (
        competitors == 1 and company_flag == 0 and news == 0
    ):  # Get company competitors
        queries.append(f"{company} competitors")
    elif news == 1 and company_flag == 0 and competitors == 0:  # Get company news
        queries.append(f"{company} company recent news")

    print("Queries:", queries)

    try:
        search_results = parallel_google_search(queries, num_results=num_results)
        print("Search Results - ", search_results)
        # Perform parallel web scraping for each query's results
        scraped_results = parallel_web_scraping(search_results, queries)
        return scraped_results[0] if scraped_results else []

    except Exception as e:
        print(f"Error during search or processing: {e}")
        return []


def generate_data(name, company, position, country):
    """
    Generate data for a given person and company using LLM chains.

    Args:
        name (str): The name of the person.
        company (str): The name of the company.
        position (str): The position of the person.
        country (str): The country of the person.
    Returns:
        JSON formatted data containing the generated content.
        -personal_summary: A concise professional summary of the person.
        -social_media_links: A JSON array containing the social media links of the person.
        -company_summary: A summary of the company.
        -company_competitors: A list of the company's competitors.
        -company_news: A JSON array containing the company's recent news.
            Each news item should have the following format:
            {
                "title": "Title of the news",
                "url": "URL of the news",
                "description": "Description of the news"
            }

    """

    # Fetch Google results
    person_google_results = fetch_top_google_results(name, company, num_results=8)
    company_google_results = fetch_top_google_results(
        name, company, num_results=3, company_flag=1
    )
    company_competitors_results = fetch_top_google_results(
        name, company, num_results=4, competitors=1
    )
    company_news_results = fetch_top_google_results(
        name, company, num_results=10, news=1
    )

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
        input_variables=["name", "company", "position", "country", "google_results"],
        template=(
            "Create an engaging summary about {name} from {company} that helps understand them professionally and personally "
            "to facilitate meaningful conversations.\n\n"
            "Extract and summarize in 120 words:\n"
            "- Their current work and interests\n"
            "- Professional background and expertise\n"
            "- Any passion projects or focus areas\n"
            "- Notable achievements or contributions\n"
            "- Industry perspectives or thought leadership\n"
            "- Any interesting professional activities (speaking, writing, research)\n"
            "- Areas they seem passionate about\n\n"
            "Be flexible with role titles - focus on their domain and actual work rather than exact position matches. "
            "If you find partial information, include it as long as it helps build a conversation with infromation that can get from given data.\n\n"
            "IMPORTANT - Respond 'Geronimo unable to provide information about {name} at {company}' only if:\n"
            "- 1. Theres no any information about {name} in {company} \n"
            "- 2. The found information is about a completely different person in an unrelated field\n\n"
            "- If the data is there but not enough to create a summary, provide as much information as possible.\n"
            "Dont Just say 'No information found' if there is some information available.\n\n"
            "Google Search Results: {google_results}\n\n"
            "Summary: "
        ),
    )

    chain_summary = LLMChain(
        llm=llm, prompt=prompt_template_summary, output_key="professional_summary"
    )

    # Second chain: Extract social media links
    prompt_template_social_links = PromptTemplate(
        input_variables=["name", "company", "position", "country", "google_links"],
        template=(
            "Find the most accurate personal and professional profile links for {name}, who works at {company} as {position} in {country}. "
            "\n\n"
            "Guidelines for link verification:\n"
            "- Verify profile ownership by matching name, company, and professional background\n"
            "- Select only ONE most relevant and active link per platform\n"
            "- Prioritize profiles that show current role or company association\n"
            "- For similar names, use company and role information to confirm identity\n"
            "\n"
            "Look for these types of profiles:\n"
            "1. Professional Networks: LinkedIn, Xing, etc.\n"
            "2. Tech Profiles: GitHub, GitLab, Stack Overflow\n"
            "3. Social Media: Twitter, Mastodon\n"
            "4. Content Platforms: Medium, personal blog, speaking profiles\n"
            "5. Professional Directories: Company staff profile, conference speaker profiles\n"
            "Try to find the atleast correct LinkedIn profile of the person from the given results\n"
            "\n"
            "Exclude:\n"
            "- Company or organization main pages\n"
            "- News articles or press releases\n"
            "- Project repositories or team pages\n"
            "- Duplicate profiles on the same platform\n"
            "- Inactive or outdated profiles\n"
            "\n"
            "Output the result as a JSON array each item enclosed with curly brackets in the following format:\n\n"
            '  -platform": "platform_name", -url": "URL",\n'
            "Ensure there is one object for each social media link. If no valid links are found, return an empty array. but try to identify atleast one platform link\n\n"
            "IMPORTANT - Do not generate any URL by using person name, just give the URL if it is found in the google search results else Do not hallucinate URL \n\n"
            "\n"
            "Google Search Results with URL: {google_links}\n"
            "\n"
            "JSON Array Output:"
        ),
    )

    chain_social_links = LLMChain(
        llm=llm, prompt=prompt_template_social_links, output_key="social_media_links"
    )

    # Third chain: Summary of the company
    prompt_template_company_summary = PromptTemplate(
        input_variables=["company", "country", "google_company_results"],
        template=(
            "Create a detailed company summary for {company} based in {country} using the provided search results. Each search result contains: "
            "title, link, snippet, and content sections.\n\n"
            "First, analyze the search results for relevant company information:\n"
            "- Check company name matches in titles and content\n"
            "- Look for official company websites or verified business listings\n"
            "- Focus on business descriptions from credible sources\n\n"
            "If ANY valid company information is found, create a comprehensive summary (around 250 words) covering:\n"
            "1. Company's primary business activities and focus\n"
            "2. Key services and products offered\n"
            "3. Geographical presence and market coverage\n"
            "4. Notable projects, achievements, or unique aspects\n"
            "5. Industry expertise and target sectors\n\n"
            "Important Guidelines:\n"
            "- Use information from multiple search result sections (title, snippet, content) to verify details\n"
            "- Create a flowing narrative that connects available information\n"
            "- Include specific examples when available\n"
            "- If some aspects are unknown, focus on the information that is available\n"
            "- Even minimal but verified information about the company should be included\n\n"
            "If multiple companies are found with the same name:\n"
            "First try to find the company that is given in the query and provide the details about that company\n"
            "You can use person name and position to identify the correct company\n"
            "if not , Start with: 'Geronimo Found multiple companies named {company}. Here are the details:'\n"
            "Then provide a flowing paragraph about each company, focusing on their core business, key offerings, and distinguishing "
            "characteristics. Keep the total response within 250 words and maintain clear separation between companies without using "
            "bullets, numbers, or special formatting.\n\n"
            "ONLY return 'Geronimo unable to find valid information about {company}' if:\n"
            "- None of the search results mention the company's business activities\n"
            "- All search results are about a different company\n"
            "- The search results contain no usable company information\n\n"
            "Search Results: {google_company_results}\n\n"
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
            "Do not generate news articles, just give the news according to the given data with reference to the URL. "
            "For each article, include the following details:\n"
            "- 'title': A clear , detailed and accurate title that gives a precise idea of the news.\n"
            "- 'url': The full complete and correct link to the news article.\n"
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
            chain_news,
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
            "company_news_results": formatted_news,
        }
    )

    # Send the email with the response data
    print("Response Data - ", response)
    formatted_response = format_response(response)
    print("Formatted Response - ", formatted_response)
    return formatted_response


# summazing the scraped content
def summarize_large_content(content, query, chunk_size=10000, overlap=200):
    """
    Summarize large content by splitting it into chunks and summarizing each chunk.
    Args:
        content (str): The large content to be summarized.
        query (str): The query related to the content.
        chunk_size (int): The size of each chunk.
        overlap (int): The overlap between chunks.
    Returns:
        str: The summarized content
    """

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
            "Content:\n{chunks}\n\n"
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
    """
    Format the response data into a JSON object.
    Args:
        response_data (dict): The response data from the chains.
    Returns:
        dict: The formatted JSON object.
    """

    # Extracting details from response_data
    professional_summary = response_data.get("professional_summary", "")
    company_summary = response_data.get("company_summary", "")

    company_competitors_raw = response_data.get("company_competitors", "")
    company_news_raw = response_data.get("company_news", "")
    social_media_links_raw = response_data.get("social_media_links", "")

    print("social_media_links_raw - ", social_media_links_raw)
    # print("Company News Raw - ", company_news_raw)

    # convert company_news_raw and social_media_links_raw to json
    company_news_json = jh.format_json_string(company_news_raw)
    social_media_links_json = jh.format_json_string(social_media_links_raw)
    print("Social Media Links JSON - ", social_media_links_json)

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
        "social_media_links": social_media_links_json,
        "company_summary": company_summary,
        "company_competitors": company_competitors,
        "company_news": company_news_json,
    }

    return formatted_json
