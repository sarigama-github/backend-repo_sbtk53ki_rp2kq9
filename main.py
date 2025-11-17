import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        # Try to import database module
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response

GITHUB_API = "https://api.github.com"


def _github_headers() -> dict:
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


@app.get("/api/github/profile")
def get_github_profile(username: str):
    """Fetch GitHub profile details for a username"""
    url = f"{GITHUB_API}/users/{username}"
    r = requests.get(url, headers=_github_headers(), timeout=10)
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.json().get("message", "Failed to fetch profile"))
    data = r.json()
    # Normalize minimal fields we care about
    profile = {
        "login": data.get("login"),
        "name": data.get("name") or data.get("login"),
        "avatar_url": data.get("avatar_url"),
        "bio": data.get("bio"),
        "location": data.get("location"),
        "blog": data.get("blog"),
        "html_url": data.get("html_url"),
        "followers": data.get("followers"),
        "following": data.get("following"),
        "public_repos": data.get("public_repos"),
        "company": data.get("company"),
        "twitter_username": data.get("twitter_username"),
        "hireable": data.get("hireable"),
    }
    return profile


@app.get("/api/github/repos")
def get_github_repos(username: str, per_page: int = 12, sort: str = "updated"):
    """Fetch public repositories for a username"""
    url = f"{GITHUB_API}/users/{username}/repos"
    params = {"per_page": per_page, "sort": sort, "type": "owner"}
    r = requests.get(url, params=params, headers=_github_headers(), timeout=10)
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.json().get("message", "Failed to fetch repos"))
    repos = []
    for repo in r.json():
        repos.append({
            "id": repo.get("id"),
            "name": repo.get("name"),
            "full_name": repo.get("full_name"),
            "html_url": repo.get("html_url"),
            "description": repo.get("description"),
            "language": repo.get("language"),
            "stargazers_count": repo.get("stargazers_count"),
            "forks_count": repo.get("forks_count"),
            "updated_at": repo.get("updated_at"),
            "homepage": repo.get("homepage"),
            "topics": repo.get("topics", []),
            "archived": repo.get("archived"),
            "visibility": repo.get("visibility"),
        })
    return {"count": len(repos), "items": repos}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
