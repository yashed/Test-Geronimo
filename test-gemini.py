from langchain_google_genai import ChatGoogleGenerativeAI
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print("Gemini Key - ", GEMINI_API_KEY)

llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=GEMINI_API_KEY)
result = llm.invoke("What are the usecases of LLMs?")
print(result)
