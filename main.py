from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "API is running 🚀"}

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        contents = await file.read()

        df = pd.read_excel(io.BytesIO(contents), engine="openpyxl")

        return {
            "rows": len(df),
            "columns": list(df.columns),
            "preview": df.head(5).to_dict()
        }

    except Exception as e:
        return {"error": str(e)}
