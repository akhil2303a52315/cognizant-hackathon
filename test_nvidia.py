import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = "false"

MODELS = [
    "nvidia/llama-3.1-nemotron-70b-instruct",
    "meta/llama-3.1-8b-instruct",
    "nvidia/llama3-chatbord-model",
    "mistralai/mixtral-8x7b-instruct-v0.1",
    "google/gemma-2b",
]

async def test():
    from langchain_openai import ChatOpenAI
    for model in MODELS:
        print(f"Testing: {model}")
        client = ChatOpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=os.getenv("NVIDIA_API_KEY"),
            model=model,
            temperature=0.3,
            max_tokens=50,
        )
        try:
            r = await client.ainvoke([{"role": "user", "content": "Say hello."}])
            print(f"  SUCCESS: {r.content[:80]}")
            return model
        except Exception as e:
            print(f"  FAILED: {str(e)[:120]}")
    return None

result = asyncio.run(test())
if result:
    print(f"\nWorking model: {result}")
else:
    print("\nNo working model found")
