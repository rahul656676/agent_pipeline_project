from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from agents.pipeline import AgentPipeline
from database import init_db, save_run, get_history
import uvicorn

app = FastAPI()

# Initialize database
init_db()

pipeline = AgentPipeline()

class GenerateRequest(BaseModel):
    grade: int
    topic: str
    user_id: str

@app.post("/generate")
async def generate_content(req: GenerateRequest):
    try:
        run_artifact = pipeline.run(grade=req.grade, topic=req.topic)
        # Save run artifact to SQLite
        save_run(
            run_id=run_artifact["run_id"],
            user_id=req.user_id,
            grade=req.grade,
            topic=req.topic,
            status=run_artifact["final"]["status"],
            artifact_dict=run_artifact
        )
        return run_artifact
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
async def get_run_history(user_id: str):
    try:
        return get_history(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve the index.html on root path
@app.get("/")
async def read_index():
    return FileResponse("ui/index.html")

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=5000, reload=True)
