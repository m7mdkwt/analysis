from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import numpy as np

app = FastAPI()

# 🔥 CORS مضبوط للإنتاج
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://pandazone97.com",
        "http://localhost:3000"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "API is running 🚀"}


# 🧹 تنظيف البيانات
def clean_df(df):
    df = df.dropna(how="all")

    best_row = 0
    max_valid = 0

    # 🔍 اكتشاف أفضل header
    for i in range(min(10, len(df))):
        count = df.iloc[i].notna().sum()
        if count > max_valid:
            max_valid = count
            best_row = i

    df.columns = df.iloc[best_row]
    df = df[best_row + 1:]

    # تنظيف أسماء الأعمدة
    df.columns = [
        str(c).replace("\n", " ").strip()
        for c in df.columns
    ]

    df = df.dropna(axis=1, how="all")
    df = df.fillna("")

    # 🔢 تحويل الأرقام بشكل آمن
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        except:
            pass

    return df


# 📊 إنشاء الرسوم
def generate_charts(df):
    charts = []

    numeric = df.select_dtypes(include=[np.number])
    text = df.select_dtypes(exclude=[np.number])

    # 📊 Bar Chart
    if not text.empty and not numeric.empty:
        cat = text.columns[0]
        num = numeric.columns[0]

        grouped = df[df[cat] != ""].groupby(cat)[num].mean().reset_index()

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

        if len(counts) < 10:
            charts.append({
                "type": "pie",
                "labels": counts.index.tolist(),
                "values": counts.values.tolist(),
                "title": f"Distribution of {col}"
            })

    return charts


# 🧠 العلاقات
def generate_correlations(df):
    results = []

    numeric = df.select_dtypes(include=[np.number])

    if len(numeric.columns) >= 2:
        corr = numeric.corr()

        for c1 in corr.columns:
            for c2 in corr.columns:
                if c1 != c2:
                    val = corr.loc[c1, c2]
                    if abs(val) > 0.6:
                        results.append({
                            "between": f"{c1} & {c2}",
                            "correlation": round(val, 2)
                        })

    return results


# 📊 Insights
def generate_insights(df):
    insights = []

    numeric = df.select_dtypes(include=[np.number])

    for col in numeric.columns:
        mean = df[col].mean()
        insights.append(f"{col}: avg={round(mean,2)}")

    return insights


# 📤 رفع وتحليل
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        contents = await file.read()

        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Empty file")

        sheets = pd.read_excel(
            io.BytesIO(contents),
            engine="openpyxl",
            sheet_name=None
        )

        best = None
        size = 0

        # 🔥 اختيار أفضل Sheet
        for df in sheets.values():
            if df is not None:
                s = df.shape[0] * df.shape[1]
                if s > size:
                    best = df
                    size = s

        if best is None:
            raise HTTPException(status_code=400, detail="No data found")

        df = clean_df(best)

        charts = generate_charts(df)
        correlations = generate_correlations(df)
        insights = generate_insights(df)

        return {
            "info": {
                "rows": len(df),
                "columns_names": list(df.columns)
            },
            "records": df.to_dict(orient="records"),
            "charts": charts,
            "correlations": correlations,
            "insights": insights
        }

    except Exception as e:
        return {
            "error": str(e)
        }
