from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Import Supabase client
from app.supabase_client import supabase

app = FastAPI(title="SaaS Application", version="1.0.0")


# Pydantic model for user creation
class UserCreate(BaseModel):
    email: str


@app.get("/")
def root():
    """Root endpoint returning health status."""
    return JSONResponse(content={"status": "ok"})


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return JSONResponse(content={"status": "healthy", "service": "saas-app"})


@app.post("/users")
def create_user(user: UserCreate):
    """Create a new user in Supabase."""
    try:
        data = {"email": user.email}
        response = supabase.table("users").insert(data).execute()
        
        if response.data:
            return {"status": "success", "user": response.data[0]}
        else:
            raise HTTPException(status_code=400, detail="Failed to create user")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users")
def get_users():
    """Get all users from Supabase."""
    try:
        response = supabase.table("users").select("*").execute()
        return {"status": "success", "users": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
