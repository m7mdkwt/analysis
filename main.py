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
    allow_origins=["*"],  # لاحقًا حدد دومينك
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🤖 OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@app.get("/")
def home():
    return {"message": "API is running 🚀"}


# 🤖 AI تحليل بسيط
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


# 📤 رفع الملف وتحليله
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # قراءة الملف (بدون الاعتماد على الاسم)
        contents = await file.read()

        # تحقق من الحجم (5MB)
        if len(contents) > 5_000_000:
            raise HTTPException(status_code=400, detail="حجم الملف كبير")

        # محاولة قراءة Excel (هذا هو التحقق الحقيقي)
        try:
            df = pd.read_excel(io.BytesIO(contents))
        except Exception:
            raise HTTPException(status_code=400, detail="الملف غير صالح أو ليس Excel")

        # تحقق من أن الملف ليس فارغ
        if df.empty:
            raise HTTPException(status_code=400, detail="الملف فارغ")

        # 📊 معلومات
        info = {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "columns_names": list(df.columns)
        }

        # 📊 المتوسطات (للـ Bar Chart)
        numeric_df = df.select_dtypes(include=["number"])
        means = numeric_df.mean().to_dict() if not numeric_df.empty else {}

        # 📊 بيانات كاملة (للـ Pie Chart)
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
