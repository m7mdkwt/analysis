from fastapi import FastAPI, File, UploadFile, HTTPException
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


# 📊 Insights بدون AI
def generate_insights(df):
    insights = {}

    numeric_df = df.select_dtypes(include=["number"])

    if not numeric_df.empty:
        insights["means"] = numeric_df.mean().to_dict()
        insights["max"] = numeric_df.max().to_dict()
        insights["min"] = numeric_df.min().to_dict()

        corr = numeric_df.corr()
        correlations = []

        for col1 in corr.columns:
            for col2 in corr.columns:
                if col1 != col2:
                    value = corr.loc[col1, col2]
                    if abs(value) > 0.5:
                        correlations.append({
                            "between": f"{col1} و {col2}",
                            "value": round(value, 2)
                        })

        insights["correlations"] = correlations

    return insights


# 📤 رفع وتحليل
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()

        print("File received:", file.filename)
        print("Size:", len(contents))

        if len(contents) > 20_000_000:
            raise HTTPException(status_code=400, detail="الملف كبير جدًا")

        # 🔥 قراءة Excel
        try:
            df = pd.read_excel(
                io.BytesIO(contents),
                engine="openpyxl",
                dtype=str,
                sheet_name=0
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"خطأ قراءة Excel: {str(e)}")

        print("Columns:", df.columns)

        if df is None or df.empty:
            raise HTTPException(status_code=400, detail="الملف فارغ")

        # تنظيف
        df = df.fillna("")
        df = df.loc[:, ~df.columns.duplicated()]
        df = df.dropna(axis=1, how="all")

        df.columns = [
            f"col_{i}" if str(c).strip() == "" else str(c).strip()
            for i, c in enumerate(df.columns)
        ]

        # تقليل الحجم
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

        info = {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "columns_names": list(df.columns)
        }

        records = df.to_dict(orient="records")

        numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()
        categorical_columns = df.select_dtypes(include=["object"]).columns.tolist()

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

    # 🔥 أهم جزء: إظهار الخطأ الحقيقي
    except Exception as e:
        print("🔥 ERROR:", str(e))
        print(traceback.format_exc())

        raise HTTPException(
            status_code=500,
            detail=traceback.format_exc()
        )
