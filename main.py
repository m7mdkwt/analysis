from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import numpy as np

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
    return {"message": "Universal Excel Analyzer 🚀"}


# 🧠 كشف أفضل Header
def detect_header(df):
    for i in range(min(5, len(df))):
        row = df.iloc[i]
        if row.notna().sum() > len(row) / 2:
            return i
    return 0


# 🧹 تنظيف شامل
def clean_dataframe(df):
    df = df.dropna(how="all")

    # كشف header
    header_row = detect_header(df)
    df.columns = df.iloc[header_row]
    df = df[header_row + 1:]

    # تنظيف أسماء الأعمدة
    df.columns = [
        str(c).replace("\n", " ").strip()
        for c in df.columns
    ]

    # حذف الأعمدة الفاضية
    df = df.loc[:, df.notna().any()]

    # تنظيف القيم
    df = df.fillna("")

    # محاولة تحويل الأرقام
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="ignore")

    return df


# 🧠 تحليل ذكي
def analyze(df):
    numeric = df.select_dtypes(include=[np.number])
    text = df.select_dtypes(include=["object"])

    charts = []
    insights = []

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

        corr = df[[c1, c2]].corr().iloc[0,1]
        if abs(corr) > 0.6:
            insights.append(f"Strong relation between {c1} and {c2}")

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

    # 🔍 Outliers
    for col in numeric.columns:
        mean = df[col].mean()
        std = df[col].std()

        outliers = df[(df[col] > mean + 2*std) | (df[col] < mean - 2*std)]

        if len(outliers) > 0:
            insights.append(f"{col} contains unusual values")

    return charts, insights


# 📤 API
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        contents = await file.read()

        # قراءة كل الشيتات
        sheets = pd.read_excel(
            io.BytesIO(contents),
            engine="openpyxl",
            sheet_name=None
        )

        best_df = None
        best_size = 0

        # اختيار أفضل شيت
        for name, df in sheets.items():
            if df is not None:
                size = df.shape[0] * df.shape[1]
                if size > best_size:
                    best_df = df
                    best_size = size

        if best_df is None:
            return {"error": "No valid data found"}

        df = clean_dataframe(best_df)

        charts, insights = analyze(df)

        return {
            "rows": len(df),
            "columns": list(df.columns),
            "preview": df.head(10).to_dict(orient="records"),
            "charts": charts,
            "insights": insights
        }

    except Exception as e:
        return {"error": str(e)}
