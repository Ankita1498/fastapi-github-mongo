from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
import requests

# MongoDB connection setup
client = MongoClient("mongodb://localhost:27017/")
db = client["github_data"]
contributors_collection = db["contributors"]

app = FastAPI()

class GitHubRepoInfo(BaseModel):
    owner: str
    repo: str
    username: str
    type: str

class SuccessResponse(BaseModel):
    message: str
    contributors_count: int

@app.post("/ingest-contributors", response_model=SuccessResponse)
def ingest_contributors(repo_info: GitHubRepoInfo):
    owner = repo_info.owner
    repo = repo_info.repo

    # Fetch contributors from GitHub API
    github_url = f"https://api.github.com/repos/{owner}/{repo}/contributors"
    headers = {"Accept": "application/vnd.github.v3+json"}
    response = requests.get(github_url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="GitHub API request failed")

    contributors_data = response.json()
    contributors_count = len(contributors_data)

    # Insert contributors into MongoDB
    contributors_collection.insert_many(contributors_data)

    return {
        "message": f"Successfully ingested {contributors_count} contributors into {owner}_{repo}.contributors",
        "contributors_count": contributors_count
    }
#################### Part 2 #######################
class ContributorInfo(BaseModel):
    username: str
    avatar_url: str
    site_admin: bool
    contributions: int

@app.post("/contributors")
def get_contributor_info(contributor_info: GitHubRepoInfo):
    owner = contributor_info.owner
    repo = contributor_info.repo
    username = contributor_info.username
    contributor_type = contributor_info.type

    # Retrieve contributor information from GitHub API
    github_url = f"https://api.github.com/repos/{owner}/{repo}/contributors"
    headers = {"Accept": "application/vnd.github.v3+json"}
    response = requests.get(github_url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="GitHub API request failed")

    contributors_data = response.json()

    # Filter contributor data based on username and type
    filtered_contributors = [
        contributor for contributor in contributors_data
        if contributor["login"] == username and contributor["type"] == contributor_type
    ]

    if not filtered_contributors:
        raise HTTPException(status_code=404, detail="Contributor not found")
    
    relevant_contributor = filtered_contributors[0]
    contributor_info = ContributorInfo(
        username=relevant_contributor["login"],
        avatar_url=relevant_contributor["avatar_url"],
        site_admin=relevant_contributor["site_admin"],
        contributions=relevant_contributor["contributions"]
    )

    return contributor_info

    return filtered_contributors[0]  # Return the first matching contributor

