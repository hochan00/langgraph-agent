from fastapi import APIRouter, UploadFile, File

from api.schema import GenerateRequest, GenerateResponse, RAGRequest, RAGResponse
from api.services.generate_service import generate_text
from api.services.rag_service import add_documents, query_rag

router = APIRouter()


@router.post("/generate", response_model=GenerateResponse, tags=["Generate"])
async def generate(req: GenerateRequest):
    generated_text = await generate_text(
        prompt=req.prompt,
        max_length=req.max_length,
        temperature=req.temperature,
        top_k=req.top_k,
    )
    return GenerateResponse(prompt=req.prompt, generated_text=generated_text)


@router.post("/documents", tags=["RAG"])
async def upload_document(file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode("utf-8")
    chunk_count = await add_documents(text=text, source=file.filename)
    return {"message": f"'{file.filename}' 문서가 등록되었습니다.", "chunks": chunk_count}


@router.post("/rag", response_model=RAGResponse, tags=["RAG"])
async def rag_query(req: RAGRequest):
    result = await query_rag(req.question)
    return RAGResponse(question=req.question, **result)
