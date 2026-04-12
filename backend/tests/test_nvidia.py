import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = "false"

MODELS = [
    "meta/llama-3.1-8b-instruct",
    "meta/llama-3.1-70b-instruct",
    "nvidia/llama-3.1-nemotron-70b-instruct",
    "mistralai/mixtral-8x7b-instruct-v0.1",
    "mistralai/mistral-7b-instruct-v0.3",
    "google/gemma-7b",
    "google/gemma-2b",
    "nvidia/nemotron-mini-4b-instruct",
    "microsoft/phi-3-mini-128k-instruct",
    "microsoft/phi-3-medium-128k-instruct",
    "qwen/qwen2.5-7b-instruct",
    "qwen/qwen2.5-72b-instruct",
    "deepseek-ai/deepseek-r1",
    "ibm/granite-34b-code-instruct",
    "snowflake/arctic",
]

async def test():
    from langchain_openai import ChatOpenAI
    working = []
    for model in MODELS:
        print(f"Testing: {model}...", end=" ", flush=True)
        client = ChatOpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=os.getenv("NVIDIA_API_KEY"),
            model=model,
            temperature=0.3,
            max_tokens=30,
        )
        try:
            r = await client.ainvoke([{"role": "user", "content": "Say hi."}])
            print(f"OK - {r.content[:50]}")
            working.append(model)
        except Exception as e:
            err = str(e)[:80]
            print(f"FAIL - {err}")
    print(f"\nWorking models ({len(working)}):")
    for m in working:
        print(f"  {m}")
    return working

asyncio.run(test())
