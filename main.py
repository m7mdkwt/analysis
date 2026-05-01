from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io

app = FastAPI()

# CORS (مهم للربط مع GoDaddy)
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
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()

    df = pd.read_excel(io.BytesIO(contents))

    summary = df.describe().to_dict()

    info = {
        "rows": df.shape[0],
        "columns": df.shape[1],
        "columns_names": list(df.columns)
    }

    return {
        "summary": summary,
        "info": info
    }