from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import os
from openai import OpenAI

app = FastAPI()

# 🔓 CORS (مهم للربط مع الفرونت)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # لاحقًا ضع دومينك
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🤖 OpenAI Client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.get("/")
def home():
    return {"message": "API is running 🚀"}


# 🤖 تحليل AI
def generate_ai_insights(df):
    try:
        # نأخذ عينة من البيانات لتقليل التكلفة
        sample = df.head(10).to_string()

        prompt = f"""
        لديك البيانات التالية:

        {sample}

        قم بتحليل البيانات وقدم:
        - أهم الملاحظات
        - العلاقات بين الأعمدة
        - توصيات مفيدة

        اكتب بالعربية وبشكل واضح وبسيط.
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"OpenAI Error: {str(e)}"


# 📤 رفع ملف Excel وتحليله
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))

        if df.empty:
            raise HTTPException(status_code=400, detail="الملف فارغ")

        # 📊 إحصائيات
        summary = df.describe(include="all").fillna(0).to_dict()

        info = {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "columns_names": list(df.columns)
        }

        # 🔢 الأعمدة الرقمية
        numeric_df = df.select_dtypes(include=['number'])
        means = numeric_df.mean().to_dict() if not numeric_df.empty else {}

        # 🤖 تحليل AI
        ai_text = generate_ai_insights(df)

        return {
            "info": info,
            "summary": summary,
            "means": means,
            "ai_analysis": ai_text
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
