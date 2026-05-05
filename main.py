from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io

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


# 📊 Insights بسيطة
def generate_insights(df):
    insights = {}

    numeric_df = df.select_dtypes(include=["number"])

    if not numeric_df.empty:
        insights["mean"] = numeric_df.mean().to_dict()
        insights["max"] = numeric_df.max().to_dict()
        insights["min"] = numeric_df.min().to_dict()

    return insights


# 📤 رفع وتحليل
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        contents = await file.read()

        if len(contents) > 20_000_000:
            raise HTTPException(status_code=400, detail="الملف كبير جدًا")

        # 📊 قراءة Excel
        df = pd.read_excel(io.BytesIO(contents), engine="openpyxl")

        if df is None or df.empty:
            raise HTTPException(status_code=400, detail="الملف فارغ")

        # 🧹 تنظيف الأعمدة (مهم جدًا)
        df.columns = [
            str(col).replace("\n", " ").strip()
            for col in df.columns
        ]

        # 🧹 تنظيف القيم
        df = df.fillna("")

        # ⚠️ تحديد الحجم
        if len(df) > 1000:
            df = df.head(1000)

        if df.shape[1] > 50:
            df = df.iloc[:, :50]

        # 🔢 تحويل الأعمدة الرقمية
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col])
            except:
                pass

        # 📊 معلومات
        info = {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "columns_names": list(df.columns)
        }

        # 📊 البيانات
        records = df.to_dict(orient="records")

        numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()
        categorical_columns = df.select_dtypes(include=["object"]).columns.tolist()

        # 📊 insights
        insights = generate_insights(df)

        return {
            "info": info,
            "records": records,
            "numeric_columns": numeric_columns,
            "categorical_columns": categorical_columns,
            "insights": insights,
            "ai_analysis": "AI disabled"
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
