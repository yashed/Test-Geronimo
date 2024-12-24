from tasks.fetch_google_results_task import FetchGoogleResultsTask

class GoogleSearchAgent:
    def __init__(self):
        self.fetch_task = FetchGoogleResultsTask()

    def search(self, queries):
        results = []
        for query in queries:
            result = self.fetch_task._run(query)
            results.append(result)
        return results
