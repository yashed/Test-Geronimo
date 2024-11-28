from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os
from dotenv import load_dotenv
from langchain.chains import SequentialChain
from langchain.utilities import GoogleSearchAPIWrapper
from langchain.chat_models import ChatOpenAI
import requests
from bs4 import BeautifulSoup
import time
import json

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

llm = ChatOpenAI(
    model="gpt-4-turbo",
    temperature=0.5,
    api_key=OPENAI_API_KEY,
)


def fetch_page_content(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all(["p", "h1", "h2", "h3", "li"])
        content = [
            tag.get_text(strip=True) for tag in paragraphs if tag.get_text(strip=True)
        ]
        return "\n".join(content)
    except requests.exceptions.HTTPError as e:
        print(f"HTTPError: {e}")
        if response.status_code == 429:
            print("Rate limited. Retrying after 10 seconds...")
            time.sleep(10)

    except Exception as e:
        print(f"An error occurred: {e}")


def fetch_top_google_results(name, company, num_results=8):
    query = f"{name} in {company}"

    google_search = GoogleSearchAPIWrapper()

    search_results = google_search.results(query, num_results=num_results)
    results = []
    for result in search_results:

        link = result.get("link")
        page_content = fetch_page_content(link) if link else "No content available"
        print(page_content)

        results.append(
            {
                "title": result.get("title"),
                "link": link,
                "snippet": result.get("snippet"),
                "content": page_content,
            }
        )
    return results


def generate_person_data(name, company, position):

    # Fetch Google results for additional context
    google_results = fetch_top_google_results(name, company)

    # Format Google results for input into the prompts
    formatted_results = "\n\n".join(
        [
            f"Title: {res['title']}\nLink: {res['link']}\nSnippet: {res['snippet']}\nContent: {res['content']}"
            for res in google_results
        ]
    )

    # First chain: Generate a concise professional summary
    prompt_template_summary = PromptTemplate(
        input_variables=["name", "company", "position", "google_results"],
        template=(
            "Provide a brief but informative summary about {name}'s career and role at {company}. "
            "Keep the summary around 100 words, highlighting the most important aspects of their professional background. "
            "Consider the information in the provided Google Search Results as context. "
            "Google Search Results: {google_results}\n\n"
            "Summary: "
        ),
    )

    chain_summary = LLMChain(
        llm=llm, prompt=prompt_template_summary, output_key="professional_summary"
    )

    # Second chain: Extract social media links
    prompt_template_social_links = PromptTemplate(
        input_variables=["name", "company", "position", "google_results"],
        template=(
            "Extract and list the most accurate and relevant social media links for {name} based on the provided Google Search Results. "
            "There can be some false positives, so ensure the links are valid and related to the person not for any organization. "
            "Prioritize LinkedIn if available, followed by other platforms like Twitter, GitHub, personal websites, Blog Sites like Medium. "
            "Ensure that only accurate and valid links are included. Do not include any links that are not related to the person like organizations social media links. "
            "Just give the [platform name]-[URL], remove additional information. "
            "Google Search Results: {google_results}\n\n"
            "Social Media Links: "
        ),
    )

    chain_social_links = LLMChain(
        llm=llm, prompt=prompt_template_social_links, output_key="social_media_links"
    )

    # Combine the two chains into a SequentialChain
    chain = SequentialChain(
        chains=[chain_summary, chain_social_links],
        input_variables=["name", "company", "position", "google_results"],
        output_variables=["professional_summary", "social_media_links"],
    )

    # Execute the SequentialChain
    response = chain.invoke(
        {
            "name": name,
            "company": company,
            "position": position,
            "google_results": formatted_results,
        }
    )

    return response
