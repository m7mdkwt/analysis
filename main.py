from fastapi import FastAPI, File, UploadFile

app = FastAPI()

@app.get("/")
def home():
    return {"message": "API is running 🚀"}

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    return {"status": "ok", "filename": file.filename}
