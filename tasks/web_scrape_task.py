from agents.web_scraper_agent import WebScraperAgent

def scrape_webpage(url: str, query: str = None) -> str:
    """
    Task to scrape a webpage using the WebScraperAgent.
    Args:
        url (str): The URL to scrape.
        query (str): Optional query for summarization.

    Returns:
        str: Scraped or summarized content.
    """
    scraper_agent = WebScraperAgent()
    return scraper_agent.run(url, query)
