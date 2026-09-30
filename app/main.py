"""LLM Gateway API service."""

from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health_check():
    """
    Health check for the load balancer.
    
    Return only the status on purpose. Extra details such as the
    version would help attackers look up known vulnerabilities.
    """
    return {"status": "ok"}