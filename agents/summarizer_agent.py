from tasks.summarization_task import SummarizationTask

class SummarizerAgent:
    def __init__(self, llm):
        self.summarizer = SummarizationTask(llm)

    def summarize(self, content, query):
        return self.summarizer.generate_summary(content, query)
