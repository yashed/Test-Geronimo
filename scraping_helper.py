from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from bs4 import BeautifulSoup


def fetch_with_selenium(url):
    """
    Fetch content using Selenium for JavaScript-heavy or interactive websites.
    """
    # Set up Chrome options for headless browsing
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    # Set up ChromeDriver with WebDriverManager
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )

    try:
        # Open the URL
        driver.get(url)

        # Wait for the page to load and locate body content
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Extract text content from specific elements to avoid noise
        elements = driver.find_elements(By.XPATH, "//p | //h1 | //h2 | //h3 | //li")
        content = [el.text.strip() for el in elements if el.text.strip()]

        # Return joined content
        return "\n".join(content)

    except Exception as e:
        print(f"Error fetching content with Selenium: {e}")
        return None

    finally:
        driver.quit()


def fetch_with_requests(url):
    """
    Fetch content using requests and BeautifulSoup for static websites.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
    }

    try:
        # Attempt to fetch content using requests
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract relevant content (p, h1, h2, h3, li tags)
        elements = soup.find_all(["p", "h1", "h2", "h3", "li"])
        content = [
            tag.get_text(strip=True) for tag in elements if tag.get_text(strip=True)
        ]

        return "\n".join(content)

    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"Error fetching content with requests: {e}")
        return None


# Example Usage
url = "https://stackoverflow.com/questions/71324949/import-selenium-could-not-be-resolved-pylance-reportmissingimports"
content = fetch_with_requests(url)
if content:
    print("Extracted Content:\n", content)
else:
    print("Failed to extract content.")
