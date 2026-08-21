from fastapi import FastAPI

app = FastAPI(
    title="Atlas Chat POC",
    description="POC de sistema multi-agente com LangGraph e LangChain",
    version="0.1.0",
)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Atlas Chat POC rodando!"}