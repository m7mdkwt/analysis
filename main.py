from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import os
import anthropic

app = FastAPI()

# 🔓 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🤖 Claude Client
client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

@app.get("/")
def home():
    return {"message": "API is running 🚀"}


# 🤖 AI تحليل باستخدام Claude
def generate_ai_insights(df):
    try:
        sample = df.head(10).to_string()

        prompt = f"""
        لديك البيانات التالية:

        {sample}

        قم بتحليل البيانات وقدم:
        - أهم الملاحظات
        - العلاقات بين الأعمدة
        - توصيات

        اكتب بالعربية وبشكل واضح.
        """

        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=500,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response.content[0].text

    except Exception as e:
        return f"Claude Error: {str(e)}"


# 📤 رفع ملف Excel وتحليله
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))

        if df.empty:
            raise HTTPException(status_code=400, detail="Empty file")

        summary = df.describe(include="all").fillna(0).to_dict()

        info = {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "columns_names": list(df.columns)
        }

        numeric_df = df.select_dtypes(include=['number'])
        means = numeric_df.mean().to_dict() if not numeric_df.empty else {}

        ai_text = generate_ai_insights(df)

        return {
            "info": info,
            "summary": summary,
            "means": means,
            "ai_analysis": ai_text
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
