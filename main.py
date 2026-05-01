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


# 🤖 تحليل AI
def generate_ai_insights(df):
    try:
        sample = df.head(10).to_string()

        prompt = f"""
        لديك البيانات التالية:

        {sample}

        المطلوب:
        - ملاحظات مختصرة
        - توصية واحدة

        اكتب بالعربية بشكل بسيط.
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


# 🤖 اقتراح نوع الرسم
def suggest_chart_with_ai(df):
    try:
        sample = df.head(10).to_string()

      prompt = f"""
لديك البيانات التالية:

{sample}

اختر أفضل نوع رسم بياني (bar أو pie أو scatter)

القواعد:
- استخدم bar للبيانات الرقمية (مثل العمر والراتب)
- استخدم pie للبيانات الفئوية (مثل القسم أو المدينة)
- استخدم scatter إذا كانت هناك علاقة بين عمودين رقميين (مثل العمر والراتب)

ثم أعطني:
- chart: نوع الرسم (bar أو pie أو scatter)
- column: العمود الأساسي
- y: (اختياري) العمود الثاني إذا كان scatter
- explanation: شرح بسيط بالعربية لماذا اخترت هذا الرسم
- tip: نصيحة للمستخدم

أعد النتيجة بصيغة JSON فقط بدون أي شرح إضافي.
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        import json

        import json

content = response.choices[0].message.content.strip()

# تنظيف الرد
if content.startswith("```"):
    content = content.replace("```json", "").replace("```", "").strip()

try:
    result = json.loads(content)
except:
    result = {
        "chart": "bar",
        "column": df.columns[0],
        "explanation": "تعذر تحليل رد الذكاء الاصطناعي",
        "tip": "يمكنك اختيار الرسم يدويًا"
    }

        return {
            "chart": result.get("chart", "bar"),
            "x": result.get("column", None),
            "reason": result.get("explanation", ""),
            "tip": result.get("tip", "")
        }

    except Exception:
        # fallback لو فشل AI
        return {
            "chart": "bar",
            "x": df.columns[0],
            "reason": "تم اختيار Bar كخيار افتراضي",
            "tip": "يمكنك تجربة أنواع رسوم أخرى"
        }


# 📤 رفع وتحليل الملف
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()

        # ❗ تحقق من الحجم (5MB)
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

        # 📊 المتوسطات
        numeric_df = df.select_dtypes(include=["number"])
        means = numeric_df.mean().to_dict() if not numeric_df.empty else {}

        # 📊 البيانات الكاملة
        records = df.to_dict(orient="records")

        # 🤖 AI تحليل
        ai_text = generate_ai_insights(df)

        # 🤖 اقتراح الرسم
        chart_suggestion = suggest_chart_with_ai(df)

        return {
            "info": info,
            "means": means,
            "records": records,
            "chart_suggestion": chart_suggestion,
            "ai_analysis": ai_text
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ داخلي: {str(e)}")
