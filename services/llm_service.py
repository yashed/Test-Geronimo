from langchain_openai import AzureChatOpenAI
import os

def initialize_llm():
    os.environ["OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
    os.environ["OPENAI_API_TYPE"] = "azure" 
    os.environ["OPENAI_API_BASE"] = os.getenv("OPENAI_API_BASE")
    os.environ["OPENAI_API_VERSION"] = os.getenv("OPENAI_API_VERSION")
    
    return AzureChatOpenAI(
       openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        deployment_name=os.getenv("OPENAI_DEPLOYMENT_NAME"),
         azure_endpoint=os.getenv("OPENAI_API_BASE"),
        temperature=0.7
    )
