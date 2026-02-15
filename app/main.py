from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="SaaS Application", version="1.0.0")


@app.get("/")
def root():
    """Root endpoint returning health status."""
    return JSONResponse(content={"status": "ok"})


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return JSONResponse(content={"status": "healthy", "service": "saas-app"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
