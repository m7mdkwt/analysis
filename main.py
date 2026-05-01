from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import os
from openai import OpenAI

app = FastAPI()

# 🔓 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@app.get("/")
def home():
    return {"message": "API is running 🚀"}


# 🤖 AI تحليل
def generate_ai_insights(df):
    try:
        sample = df.head(10).to_string()

        prompt = f"""
لديك البيانات التالية:

{sample}

قم بإعطاء:
- أهم ملاحظة
- علاقة بين عمودين
- توصية واحدة

بالعربية وبشكل مختصر.
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"AI Error: {str(e)}"


# 📊 Insights ذكية (بدون AI)
def generate_insights(df):
    insights = {}

    numeric_df = df.select_dtypes(include=["number"])

    if not numeric_df.empty:
        insights["means"] = numeric_df.mean().to_dict()
        insights["max"] = numeric_df.max().to_dict()
        insights["min"] = numeric_df.min().to_dict()

        # correlation
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

        if len(contents) > 5_000_000:
            raise HTTPException(status_code=400, detail="حجم الملف كبير")

        try:
            df = pd.read_excel(io.BytesIO(contents))
        except Exception:
            raise HTTPException(status_code=400, detail="ملف غير صالح")

        if df.empty:
            raise HTTPException(status_code=400, detail="الملف فارغ")

        info = {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "columns_names": list(df.columns)
        }

        records = df.to_dict(orient="records")

        numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()
        categorical_columns = df.select_dtypes(include=["object"]).columns.tolist()

        # 📊 insights محلية
        insights = generate_insights(df)

        # 🤖 AI insights
        ai_text = generate_ai_insights(df)

        return {
            "info": info,
            "records": records,
            "numeric_columns": numeric_columns,
            "categorical_columns": categorical_columns,
            "insights": insights,
            "ai_analysis": ai_text
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
