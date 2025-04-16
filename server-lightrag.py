import os
from dotenv import load_dotenv
load_dotenv()

import asyncio
import nest_asyncio
nest_asyncio.apply()

import logging
logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed
from lightrag.kg.shared_storage import initialize_pipeline_status

WORKING_DIR = "./lightRAG_data"
if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)

async def initialize_rag():
    rag = LightRAG(
        working_dir=WORKING_DIR,
        embedding_func=openai_embed,
        llm_model_func=gpt_4o_mini_complete,
    )
    await rag.initialize_storages()
    await initialize_pipeline_status()
    logging.info("LightRAG đã sẵn sàng trong lifespan handler.")
    return rag

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.rag = await initialize_rag()
    yield

app = FastAPI(lifespan=lifespan)

# Thêm CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/query")
def query_endpoint(q: str):
    try:
        rag = app.state.rag
        result = rag.query(q, param=QueryParam(mode="hybrid"))
        return {"query": q, "result": result}
    except Exception as e:
        logging.error(f"Error processing query: {e}")
        return {"error": str(e)}

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "API is running."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server-lightrag:app", host="0.0.0.0", port=8000, reload=True)