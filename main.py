from fastapi import FastAPI, File, UploadFile, HTTPException
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
    return {"message": "Smart Excel Analyzer 🚀"}


# 🧠 تحليل ذكي
def smart_analysis(df):
    results = {}

    numeric = df.select_dtypes(include=["number"])
    text = df.select_dtypes(include=["object"])

    insights = []
    charts = []

    # 📊 أفضل رسم Bar
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

        insights.append(f"Average {num} varies across {cat}")

    # 📈 Scatter ذكي
    if len(numeric.columns) >= 2:
        c1, c2 = numeric.columns[:2]

        charts.append({
            "type": "scatter",
            "x": df[c1].tolist(),
            "y": df[c2].tolist(),
            "title": f"{c1} vs {c2}"
        })

        corr = df[[c1, c2]].corr().iloc[0,1]

        if abs(corr) > 0.6:
            insights.append(f"Strong relationship between {c1} and {c2} ({round(corr,2)})")

    # 🥧 Pie ذكي
    if not text.empty:
        col = text.columns[0]
        counts = df[col].value_counts()

        charts.append({
            "type": "pie",
            "labels": counts.index.tolist(),
            "values": counts.values.tolist(),
            "title": f"Distribution of {col}"
        })

    # 🔍 Outliers
    for col in numeric.columns:
        mean = df[col].mean()
        std = df[col].std()

        outliers = df[(df[col] > mean + 2*std) | (df[col] < mean - 2*std)]

        if len(outliers) > 0:
            insights.append(f"{col} has unusual values")

    return charts, insights


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        contents = await file.read()

        if len(contents) > 20_000_000:
            raise HTTPException(status_code=400, detail="File too large")

        sheets = pd.read_excel(io.BytesIO(contents), engine="openpyxl", sheet_name=None)

        df = None
        for s in sheets.values():
            if not s.empty:
                df = s
                break

        if df is None:
            raise HTTPException(status_code=400, detail="Empty file")

        df = df.dropna(how="all")

        df.columns = df.iloc[0]
        df = df[1:]

        df.columns = [str(c).replace("\n", " ").strip() for c in df.columns]
        df = df.fillna("")

        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col])
            except:
                pass

        charts, insights = smart_analysis(df)

        return {
            "rows": len(df),
            "columns": list(df.columns),
            "charts": charts,
            "insights": insights
        }

    except Exception as e:
        return {"error": str(e)}
