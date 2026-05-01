from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import os
import anthropic

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# تأكد أن المتغير البيئي معرف في جهازك أو استبدله بالمفتاح مباشرة للتجربة
# os.environ["ANTHROPIC_API_KEY"] = "sk-ant-..." 
client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

@app.get("/")
def home():
    return {"message": "API is running 🚀"}

# 🤖 Claude AI Analysis
def generate_ai_insights(df):
    try:
        # تحويل أول 10 أسطر لنص (مع التأكد من عدم ضياع الأعمدة)
        sample = df.head(10).to_csv(index=False) # CSV أحياناً يكون أوضح للموديل من string عشوائي

        prompt = f"""
        لديك عينة من البيانات التالية (أول 10 أسطر):

        {sample}

        قم بتحليل البيانات وقدم:
        - ملخص سريع لما تدور حوله البيانات.
        - أهم 3 ملاحظات ذكية.
        - توصية عملية بناءً على هذه الأرقام.

        اكتب الإجابة باللغة العربية بتنسيق نقاط واضح.
        """

        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1000, # زدنا التوكنز ليعطي تحليل أعمق
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # التصحيح هنا: الوصول للنص بشكل آمن
        return response.content[0].text

    except Exception as e:
        return f"Claude Error: {str(e)}"

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # التأكد من نوع الملف
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="يرجى رفع ملف Excel فقط")

    try:
        contents = await file.read()
        # استخدام engine='openpyxl' لضمان قراءة ملفات xlsx الحديثة
        df = pd.read_excel(io.BytesIO(contents))

        if df.empty:
            raise HTTPException(status_code=400, detail="الملف فارغ")

        # تحويل الـ Summary لنوع بيانات يقبله JSON (تحويل الـ Timestamp لـ string)
        summary = df.describe(include="all").astype(str).to_dict()

        info = {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "columns_names": list(df.columns)
        }

        numeric_df = df.select_dtypes(include=['number'])
        means = numeric_df.mean().to_dict() if not numeric_df.empty else {}

        # 🤖 طلب التحليل من ذكاء كلود
        ai_text = generate_ai_insights(df)

        return {
            "info": info,
            "summary": summary,
            "means": means,
            "ai_analysis": ai_text
        }

    except Exception as e:
        # طباعة الخطأ في الكونسول لتسهيل التنقيح (Debugging)
        print(f"Error detail: {e}")
        raise HTTPException(status_code=500, detail=f"حدث خطأ أثناء معالجة الملف: {str(e)}")
