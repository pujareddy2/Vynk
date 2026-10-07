from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import check_db_connection

app = FastAPI(title="Localy API")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    db_status = "connected" if check_db_connection() else "disconnected"
    return {
        "status": "connected",
        "database": db_status,
        "message": f"backend connected (database {db_status})",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
