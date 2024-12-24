from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

def summarize_large_content(content, query, chunk_size=10000, overlap=200):
    """
    Summarize large content by splitting it into manageable chunks.
    """
    from services.llm_service import llm  # LLM instance

    chunks = []
    start = 0
    while start < len(content):
        end = min(start + chunk_size, len(content))
        chunks.append(content[start:end])
        start += chunk_size - overlap

    prompt_template = PromptTemplate(
        input_variables=["query", "chunk"],
        template=(
            "Summarize the content below based on the query provided. Focus on relevant details and avoid unrelated data.\n\n"
            "Query: {query}\n\nContent:\n{chunk}\n\nSummary:"
        ),
    )
    chain = LLMChain(llm=llm, prompt=prompt_template)

    # Generate summaries for each chunk
    chunk_summaries = [chain.run({"query": query, "chunk": chunk}) for chunk in chunks]

    # Combine and re-summarize if necessary
    combined_summary = "\n".join(chunk_summaries)
    if len(combined_summary) > chunk_size:
        return chain.run({"query": query, "chunk": combined_summary})

    return combined_summary
