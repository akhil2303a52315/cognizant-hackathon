from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_cohere import ChatCohere
import os


def get_groq_client(model="llama-3.3-70b-versatile"):
    return ChatGroq(groq_api_key=os.getenv("GROQ_API_KEY"), model_name=model, temperature=0.3, max_tokens=2048)


def get_openrouter_client(model="meta-llama/llama-3.3-70b-instruct:free"):
    return ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        model=model, temperature=0.3, max_tokens=2048,
        default_headers={"HTTP-Referer": "https://supplychaingpt.ai", "X-Title": "SupplyChainGPT"},
    )


def get_nvidia_client(model="nvidia/llama-3.1-nemotron-70b-instruct"):
    return ChatOpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=os.getenv("NVIDIA_API_KEY"),
        model=model, temperature=0.3, max_tokens=2048,
    )


def get_google_client(model="gemini-2.0-flash"):
    return ChatGoogleGenerativeAI(google_api_key=os.getenv("GOOGLE_API_KEY"), model=model, temperature=0.3)


def get_cohere_client(model="command-r-plus"):
    return ChatCohere(cohere_api_key=os.getenv("COHERE_API_KEY"), model=model, temperature=0.3)


def get_sambanova_client(model="Meta-Llama-3.3-70B-Instruct"):
    return ChatOpenAI(
        base_url="https://api.sambanova.ai/v1",
        api_key=os.getenv("SAMBANOVA_API_KEY"),
        model=model, temperature=0.3, max_tokens=2048,
    )
