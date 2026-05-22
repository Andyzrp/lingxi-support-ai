from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import numpy as np
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Embedding服务", version="1.0.0")

# 加载模型（启动时执行一次）
MODEL_NAME = os.getenv("MODEL_NAME", "BAAI/bge-small-zh-v1.5")
logger.info(f"正在加载模型: {MODEL_NAME}")
model = SentenceTransformer(MODEL_NAME)
logger.info(f"模型加载完成，向量维度: {model.get_sentence_embedding_dimension()}")


class EncodeRequest(BaseModel):
    texts: list[str]
    batch_size: int = 32


class EncodeResponse(BaseModel):
    embeddings: list[list[float]]
    model: str
    dims: int


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model": MODEL_NAME,
        "dims": model.get_sentence_embedding_dimension()
    }


@app.post("/encode", response_model=EncodeResponse)
async def encode(request: EncodeRequest):
    if not request.texts:
        raise HTTPException(status_code=400, detail="texts不能为空")
    
    if len(request.texts) > 512:
        raise HTTPException(status_code=400, detail="单次最多512条")

    embeddings = model.encode(
        request.texts,
        batch_size=request.batch_size,
        normalize_embeddings=True,  # bge模型必须归一化
        show_progress_bar=False
    )

    return EncodeResponse(
        embeddings=embeddings.tolist(),
        model=MODEL_NAME,
        dims=embeddings.shape[1]
    )