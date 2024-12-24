from langchain.tools import BaseTool
import requests
from bs4 import BeautifulSoup
from utils.langchain_helper import summarize_large_content


class WebScraperAgent(BaseTool):
    """
    Web Scraper Agent for fetching and processing webpage content.
    """
    name: str = "web_scraper"  # Required type annotation
    description: str = "Agent to scrape webpage content and provide meaningful text."  # Required type annotation

    def run(self, url: str, query: str = None) -> str:
        """
        Public method to run the scraping task.
        Args:
            url (str): The URL to scrape.
            query (str): Optional query for content summarization.

        Returns:
            str: Scraped or summarized content.
        """
        return self._run(url, query)

    def _run(self, url: str, query: str = None) -> str:
        """
        Scrape content from the URL and process it.
        Args:
            url (str): The URL to scrape.
            query (str): Optional query for content summarization.

        Returns:
            str: Scraped or summarized content.
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
                tag.get_text(strip=True)
                for tag in elements
                if tag.get_text(strip=True)
            ]

            content_str = "\n".join(content)

            # Summarize content if it's too large
            if len(content_str) > 20000:  # Adjustable threshold
                print(f"Content from {url} is too large, summarizing...")
                return summarize_large_content(content_str, query)

            return content_str

        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"Error fetching content: {e}")
            return "Error: Unable to fetch content from the URL."

    async def _arun(self, url: str, query: str = None) -> str:
        """
        Asynchronous version of the scraping logic.
        """
        raise NotImplementedError("Async scraping is not yet implemented.")
