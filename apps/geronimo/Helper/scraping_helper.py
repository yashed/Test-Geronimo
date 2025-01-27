import requests
from bs4 import BeautifulSoup
import Helper.langchain_helper as lh


def fetch_with_requests(url, query, chunk_size=1500, overlap=200):
    """
    Fetch content using requests and BeautifulSoup
    Args:
        url (str): The URL to fetch content from
        query (str): The query used to summarize the content
        chunk_size (int): The size of each chunk for summarization
        overlap (int): The overlap between chunks for summarization
    Returns:
        str: The extracted content from the URL
    """
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

        elements = soup.find_all(["p", "h1", "h2", "li"])
        content = [
            tag.get_text(strip=True) for tag in elements if tag.get_text(strip=True)
        ]

        content_str = "\n".join(content)

        # If content is too large, summarize it using summarize_large_content
        if len(content_str) > 40000:
            print(f"Content from {url} is too large, summarizing it...")
            return lh.summarize_large_content(content_str, query)
        elif len(content_str) > 900000:
            return None

        return content_str

    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"Error fetching content with requests: {e}")
        return None
