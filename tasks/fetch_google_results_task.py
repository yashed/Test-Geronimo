from langchain.agents import Tool
from langchain_google_community import GoogleSearchAPIWrapper
from pydantic import BaseModel

class FetchGoogleResultsTask(BaseModel):
    """
    Task to fetch Google Search results using a wrapper.
    """
    google_search: GoogleSearchAPIWrapper = GoogleSearchAPIWrapper()

    def _run(self, query: str) -> dict:
        """
        Run the task to fetch search results for a given query.
        """
        try:
            results = self.google_search.run(query)
            return results
        except Exception as e:
            raise RuntimeError(f"Failed to fetch search results: {e}")

    def _arun(self, query: str):
        """
        Asynchronous version of the _run method.
        """
        raise NotImplementedError("Async operations are not supported for this task.")