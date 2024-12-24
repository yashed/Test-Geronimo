from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

class SummarizationTask:
    def __init__(self, llm):
        self.llm = llm

    def generate_summary(self, content, query):
        prompt_template = PromptTemplate(
            input_variables=["query", "chunk"],
            template=(
                "You are a summarization assistant. Based on the following query, summarize the content provided below. "
                "Focus only on the relevant information related to the query. Ignore irrelevant data. "
                "Query: {query}\n\nContent: {chunk}\n\nSummary:"
            ),
        )
        chain = LLMChain(llm=self.llm, prompt=prompt_template)
        return chain.run({"query": query, "chunk": content})
