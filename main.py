from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io

app = FastAPI()

# 🔓 CORS (مهم للربط مع الفرونت)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # لاحقًا حط دومينك
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🏠 الصفحة الرئيسية
@app.get("/")
def home():
    return {"message": "API is running 🚀"}

# 📤 رفع ملف Excel وتحليله
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # قراءة الملف
        contents = await file.read()

        # تحويله إلى DataFrame
        df = pd.read_excel(io.BytesIO(contents))

        # التحقق من أن الملف يحتوي بيانات
        if df.empty:
            raise HTTPException(status_code=400, detail="الملف فارغ")

        # 📊 إحصائيات عامة
        summary = df.describe(include="all").fillna(0).to_dict()

        # 🧠 معلومات إضافية
        info = {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "columns_names": list(df.columns)
        }

        # 🔢 استخراج الأعمدة الرقمية فقط للرسم
        numeric_df = df.select_dtypes(include=['number'])

        means = {}
        if not numeric_df.empty:
            means = numeric_df.mean().to_dict()

        return {
            "info": info,
            "summary": summary,
            "means": means
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
