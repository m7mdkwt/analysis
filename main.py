from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import os
from openai import OpenAI

app = FastAPI()

# 🔓 CORS (مسموح للجميع حالياً)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🤖 OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@app.get("/")
def home():
    return {"message": "API is running 🚀"}


# 🤖 تحليل AI مبسط
def generate_ai_insights(df):
    try:
        sample = df.head(10).to_string()

        prompt = f"""
        حلل البيانات التالية بشكل مختصر:

        {sample}

        المطلوب:
        - ملاحظات بسيطة
        - توصية واحدة

        اكتب بالعربية وباختصار.
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"AI Error: {str(e)}"


# 📤 رفع وتحليل Excel
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # ❗ تحقق من نوع الملف
        if not file.filename.endswith((".xlsx", ".xls")):
            raise HTTPException(status_code=400, detail="الملف يجب أن يكون Excel")

        contents = await file.read()

        # ❗ تحقق من الحجم (5MB)
        if len(contents) > 5_000_000:
            raise HTTPException(status_code=400, detail="حجم الملف كبير")

        df = pd.read_excel(io.BytesIO(contents))

        # ❗ ملف فارغ
        if df.empty:
            raise HTTPException(status_code=400, detail="الملف فارغ")

        # 📊 معلومات
        info = {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "columns_names": list(df.columns)
        }

        # 📊 المتوسطات
        numeric_df = df.select_dtypes(include=["number"])
        means = numeric_df.mean().to_dict() if not numeric_df.empty else {}

        # 📊 بيانات للرسم
        records = df.to_dict(orient="records")

        # 🤖 AI
        ai_text = generate_ai_insights(df)

        return {
            "info": info,
            "means": means,
            "records": records,
            "ai_analysis": ai_text
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ داخلي: {str(e)}")
