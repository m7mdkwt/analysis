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


# 📊 Charts تلقائية
def generate_auto_charts(df):
    charts = []

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object"]).columns.tolist()

    # Bar
    if cat_cols and numeric_cols:
        x = cat_cols[0]
        y = numeric_cols[0]

        grouped = df.groupby(x)[y].mean().reset_index()

        charts.append({
            "type": "bar",
            "x": grouped[x].tolist(),
            "y": grouped[y].tolist(),
            "title": f"{y} by {x}"
        })

    # Scatter
    if len(numeric_cols) >= 2:
        charts.append({
            "type": "scatter",
            "x": df[numeric_cols[0]].tolist(),
            "y": df[numeric_cols[1]].tolist(),
            "title": f"{numeric_cols[0]} vs {numeric_cols[1]}"
        })

    # Pie
    if cat_cols:
        counts = df[cat_cols[0]].value_counts()

        charts.append({
            "type": "pie",
            "labels": counts.index.tolist(),
            "values": counts.values.tolist(),
            "title": f"Distribution of {cat_cols[0]}"
        })

    return charts


# 🧠 Correlation
def generate_correlations(df):
    results = []

    numeric_df = df.select_dtypes(include=["number"])

    if len(numeric_df.columns) >= 2:
        corr = numeric_df.corr()

        for col1 in corr.columns:
            for col2 in corr.columns:
                if col1 != col2:
                    val = corr.loc[col1, col2]

                    if abs(val) > 0.6:
                        results.append({
                            "between": f"{col1} & {col2}",
                            "correlation": round(val, 2)
                        })

    return results


# 📤 رفع وتحليل
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        contents = await file.read()

        if len(contents) > 20_000_000:
            raise HTTPException(status_code=400, detail="الملف كبير جدًا")

        # قراءة Excel
        df = pd.read_excel(io.BytesIO(contents), engine="openpyxl")

        if df is None or df.empty:
            raise HTTPException(status_code=400, detail="الملف فارغ")

        # تنظيف الأعمدة
        df.columns = [
            str(col).replace("\n", " ").strip()
            for col in df.columns
        ]

        # تنظيف القيم
        df = df.fillna("")

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

        # معلومات
        info = {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "columns_names": list(df.columns)
        }

        records = df.to_dict(orient="records")

        numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()
        categorical_columns = df.select_dtypes(include=["object"]).columns.tolist()

        insights = generate_insights(df)
        charts = generate_auto_charts(df)
        correlations = generate_correlations(df)

        return {
            "info": info,
            "records": records,
            "numeric_columns": numeric_columns,
            "categorical_columns": categorical_columns,
            "insights": insights,
            "charts": charts,
            "correlations": correlations,
            "ai_analysis": "AI disabled"
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
