from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import numpy as np

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
    return {"message": "Smart Analyzer (No AI) 🚀"}


# 🧹 تنظيف ذكي قوي
def clean_df(df):
    df = df.dropna(how="all")

    best_row = 0
    max_valid = 0

    for i in range(min(10, len(df))):
        count = df.iloc[i].notna().sum()
        if count > max_valid:
            max_valid = count
            best_row = i

    df.columns = df.iloc[best_row]
    df = df[best_row + 1:]

    df.columns = [
        str(c).replace("\n", " ").strip()
        for c in df.columns
    ]

    df = df.dropna(axis=1, how="all")
    df = df.fillna("")

    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


# 📊 اختيار الرسم الأفضل
def choose_chart(df):
    charts = []

    numeric = df.select_dtypes(include=[np.number])
    text = df.select_dtypes(exclude=[np.number])

    # 📈 Line (تواريخ)
    for col in df.columns:
        parsed = pd.to_datetime(df[col], errors="coerce")
        if parsed.notna().sum() > len(df) * 0.6:
            if not numeric.empty:
                num = numeric.columns[0]
                charts.append({
                    "type": "line",
                    "x": parsed.astype(str).tolist(),
                    "y": df[num].tolist(),
                    "title": f"{num} over time"
                })
                return charts

    # 📊 Bar
    if not text.empty and not numeric.empty:
        cat = text.columns[0]
        variances = numeric.var()
        num = variances.idxmax()

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

        if len(counts) < 10:
            charts.append({
                "type": "pie",
                "labels": counts.index.tolist(),
                "values": counts.values.tolist(),
                "title": f"Distribution of {col}"
            })

    return charts


# 🧠 Insights
def generate_insights(df):
    insights = []
    numeric = df.select_dtypes(include=[np.number])

    for col in numeric.columns:
        mean = df[col].mean()
        insights.append(f"{col}: avg={round(mean,2)}")

    if len(numeric.columns) >= 2:
        corr = numeric.corr()

        for c1 in corr.columns:
            for c2 in corr.columns:
                if c1 != c2:
                    val = corr.loc[c1, c2]
                    if abs(val) > 0.7:
                        insights.append(f"{c1} ↔ {c2} strong relation")

    for col in numeric.columns:
        mean = df[col].mean()
        std = df[col].std()

        if std > 0:
            outliers = df[
                (df[col] > mean + 2*std) |
                (df[col] < mean - 2*std)
            ]

            if len(outliers) > 0:
                insights.append(f"{col} has outliers")

    return insights


# 📤 رفع وتحليل
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
        insights = generate_insights(df)

        return {
            "rows": len(df),
            "columns": list(df.columns),
            "charts": charts,
            "insights": insights,
            "preview": df.head(10).to_dict(orient="records")
        }

    except Exception as e:
        return {"error": str(e)}
