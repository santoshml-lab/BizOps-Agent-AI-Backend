from fastapi import FastAPI

app = FastAPI(
    title="BizOps Agent AI",
    description="Agentic AI system for business operations",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "status": "success",
        "message": "BizOps Agent AI API is running"
    }
