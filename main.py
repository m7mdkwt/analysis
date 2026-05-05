from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import numpy as np
from openai import OpenAI
import os

app = FastAPI()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "AI Smart Excel Analyzer 🚀"}


# 🧹 تنظيف
def clean_df(df):
    df = df.dropna(how="all")

    # كشف header
    for i in range(min(5, len(df))):
        if df.iloc[i].notna().sum() > len(df.columns) / 2:
            df.columns = df.iloc[i]
            df = df[i+1:]
            break

    df.columns = [str(c).replace("\n", " ").strip() for c in df.columns]
    df = df.fillna("")

    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="ignore")

    return df


# 📊 اختيار الرسم الأفضل
def choose_chart(df):
    numeric = df.select_dtypes(include=[np.number])
    text = df.select_dtypes(include=["object"])

    charts = []

    # 📈 Line (تواريخ)
    for col in df.columns:
        try:
            parsed = pd.to_datetime(df[col], errors="coerce")
            if parsed.notna().sum() > len(df) * 0.5 and not numeric.empty:
                num = numeric.columns[0]
                charts.append({
                    "type": "line",
                    "x": parsed.astype(str).tolist(),
                    "y": df[num].tolist(),
                    "title": f"{num} over time"
                })
                return charts
        except:
            pass

    # 📊 Bar
    if not text.empty and not numeric.empty:
        cat = text.columns[0]
        num = numeric.columns[0]

        grouped = df.groupby(cat)[num].mean().reset_index()

        charts.append({
            "type": "bar",
            "x": grouped[cat].tolist(),
            "y": grouped[num].tolist(),
            "title": f"{num} by {cat}"
        })

    # 📈 Scatter
    if len(numeric.columns) >= 2:
        c1, c2 = numeric.columns[:2]

        charts.append({
            "type": "scatter",
            "x": df[c1].tolist(),
            "y": df[c2].tolist(),
            "title": f"{c1} vs {c2}"
        })

    # 🥧 Pie
    if not text.empty:
        col = text.columns[0]
        counts = df[col].value_counts()

        charts.append({
            "type": "pie",
            "labels": counts.index.tolist(),
            "values": counts.values.tolist(),
            "title": f"Distribution of {col}"
        })

    return charts


# 🤖 AI تحليل
def ai_analysis(df):
    try:
        sample = df.head(5).to_string()

        prompt = f"""
You are a data analyst.

Analyze this dataset sample:

{sample}

Give:
- One key insight
- One relationship between columns
- One recommendation

Keep it short.
"""

        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )

        return res.choices[0].message.content

    except Exception:
        return "AI unavailable"


# 📤 API
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        contents = await file.read()

        sheets = pd.read_excel(
            io.BytesIO(contents),
            engine="openpyxl",
            sheet_name=None
        )

        best = None
        size = 0

        for df in sheets.values():
            if df is not None:
                s = df.shape[0] * df.shape[1]
                if s > size:
                    best = df
                    size = s

        if best is None:
            return {"error": "Empty file"}

        df = clean_df(best)

        charts = choose_chart(df)
        ai_text = ai_analysis(df)

        return {
            "rows": len(df),
            "columns": list(df.columns),
            "charts": charts,
            "ai_analysis": ai_text,
            "preview": df.head(10).to_dict(orient="records")
        }

    except Exception as e:
        return {"error": str(e)}
