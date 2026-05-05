from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import traceback

app = FastAPI()

# 🔓 CORS
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
    try:
        contents = await file.read()

        if len(contents) > 20_000_000:
            return {"error": "الملف كبير جدًا"}

        # قراءة Excel
        df = pd.read_excel(
            io.BytesIO(contents),
            engine="openpyxl",
            dtype=str,
            sheet_name=0
        )

        if df is None or df.empty:
            return {"error": "الملف فارغ"}

        # تنظيف
        df = df.fillna("")
        df = df.loc[:, ~df.columns.duplicated()]
        df = df.dropna(axis=1, how="all")

        df.columns = [
            f"col_{i}" if str(c).strip() == "" else str(c).strip()
            for i, c in enumerate(df.columns)
        ]

        # تحديد الحجم
        if len(df) > 1000:
            df = df.head(1000)

        if df.shape[1] > 50:
            df = df.iloc[:, :50]

        # تحويل أرقام
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col])
            except:
                pass

        return {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "columns_names": list(df.columns),
            "preview": df.head(10).to_dict(orient="records")
        }

    except Exception as e:
        # 🔥 أهم نقطة: لا نكسر السيرفر
        return {
            "error": str(e),
            "trace": traceback.format_exc()
        }
