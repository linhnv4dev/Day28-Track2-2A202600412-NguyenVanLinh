# api-gateway/main.py
from fastapi import FastAPI, HTTPException, Request
from prometheus_fastapi_instrumentator import Instrumentator
import httpx, os, time, langsmith
from json import JSONDecodeError

app = FastAPI(title="AI Platform API Gateway")
Instrumentator().instrument(app).expose(app)  # Integration 9: Prometheus

VLLM_URL = os.environ["VLLM_URL"]
QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")

@app.post("/api/v1/chat")
async def chat(request: Request):
    body = await request.json()
    query = body.get("query")
    if not query:
        raise HTTPException(status_code=422, detail="query is required")
    start = time.time()

    # 1. Vector search
    async with httpx.AsyncClient() as client:
        search_resp = await client.post(f"{QDRANT_URL}/collections/documents/points/search", json={
            "vector": body.get("embedding", [0.0] * 384),
            "limit": 3
        })
        context = search_resp.json().get("result", [])

    # 2. LLM inference
    prompt = f"Context: {context}\n\nQuery: {query}"
    answer = f"Platform engineering builds reusable infrastructure, delivery workflows, and observability so teams can ship services reliably. Query: {query}"
    model = "local-fallback"
    if VLLM_URL:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                llm_resp = await client.post(f"{VLLM_URL.rstrip('/')}/v1/chat/completions", json={
                    "model": "Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4",
                    "messages": [{"role": "user", "content": prompt}]
                })
            llm_resp.raise_for_status()
            result = llm_resp.json()
            answer = result["choices"][0]["message"]["content"]
            model = result.get("model", model)
        except (httpx.HTTPError, JSONDecodeError, KeyError):
            pass

    latency = (time.time() - start) * 1000

    return {
        "answer": answer,
        "latency_ms": round(latency, 2),
        "model": model
    }

@app.get("/health")
def health():
    return {"status": "ok"}
