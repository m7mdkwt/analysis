from fastapi import FastAPI, File, UploadFile
import pandas as pd
import io

app = FastAPI()

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
            "columns": list(df.columns)
        }

    except Exception as e:
        return {"error": str(e)}
