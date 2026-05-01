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
    allow_origins=["*"],  # لاحقًا ضع دومينك
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🤖 OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@app.get("/")
def home():
    return {"message": "API is running 🚀"}


# 🤖 تحليل AI فقط (بدون فرض رسوم)
def generate_ai_insights(df):
    try:
        sample = df.head(10).to_string()

        prompt = f"""
لديك البيانات التالية:

{sample}

قم بتحليلها بشكل بسيط:
- أهم ملاحظة
- علاقة محتملة بين عمودين
- توصية واحدة

اكتب بالعربية بشكل مختصر.
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


# 📤 رفع وتحليل الملف
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()

        # ❗ تحقق من الحجم
        if len(contents) > 5_000_000:
            raise HTTPException(status_code=400, detail="حجم الملف كبير")

        # ❗ قراءة Excel
        try:
            df = pd.read_excel(io.BytesIO(contents))
        except Exception:
            raise HTTPException(status_code=400, detail="الملف غير صالح أو ليس Excel")

        if df.empty:
            raise HTTPException(status_code=400, detail="الملف فارغ")

        # 📊 معلومات
        info = {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "columns_names": list(df.columns)
        }

        # 📊 بيانات كاملة (للرسم)
        records = df.to_dict(orient="records")

        # 📊 أعمدة رقمية (مفيد للواجهة)
        numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()

        # 📊 أعمدة نصية
        categorical_columns = df.select_dtypes(include=["object"]).columns.tolist()

        # 🤖 AI تحليل (اختياري)
        ai_text = generate_ai_insights(df)

        return {
            "info": info,
            "records": records,
            "numeric_columns": numeric_columns,
            "categorical_columns": categorical_columns,
            "ai_analysis": ai_text
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ داخلي: {str(e)}")
