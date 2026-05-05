import React, { useState } from "react";
import Plot from "react-plotly.js";

const API_URL = "http://127.0.0.1:8000/upload"; // محلي

function Upload() {
  const [file, setFile] = useState(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const [chartType, setChartType] = useState("");
  const [xColumn, setXColumn] = useState("");
  const [yColumn, setYColumn] = useState("");

  // 📤 رفع الملف
  const handleUpload = async () => {
    if (!file) return alert("اختر ملف Excel");

    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);

      const res = await fetch(API_URL, {
        method: "POST",
        body: formData,
      });

      // 🔥 هنا أهم تعديل
      const text = await res.text();
      console.log("RAW RESPONSE:", text);

      let result;
      try {
        result = JSON.parse(text);
      } catch {
        alert("❌ الرد ليس JSON:\n\n" + text);
        return;
      }

      if (!res.ok) {
        alert("❌ خطأ من السيرفر:\n\n" + JSON.stringify(result, null, 2));
        return;
      }

      setData(result);
      setChartType("");
      setXColumn("");
      setYColumn("");

    } catch (err) {
      console.log("ERROR:", err);
      alert("❌ فشل الاتصال بالسيرفر");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      maxWidth: "700px",
      margin: "auto",
      padding: "15px",
      background: "#f8f6f1",
      minHeight: "100vh"
    }}>
      
      <h2 style={{ textAlign: "center" }}>📊 تحليل Excel</h2>

      <input
        type="file"
        accept=".xlsx,.xls"
        style={{ width: "100%", marginBottom: "10px" }}
        onChange={(e) => setFile(e.target.files[0])}
      />

      <button
        onClick={handleUpload}
        style={{
          width: "100%",
          padding: "12px",
          background: "#007bff",
          color: "white",
          border: "none",
          borderRadius: "8px",
          fontWeight: "bold"
        }}
      >
        تحليل الملف
      </button>

      {loading && <p>⏳ جاري التحليل...</p>}

      {data && (
        <div style={{ marginTop: "20px" }}>
          <h3>📌 معلومات:</h3>
          <pre>{JSON.stringify(data.info, null, 2)}</pre>

          <div style={{
            marginTop: "20px",
            padding: "15px",
            background: "#ffffff",
            borderRadius: "10px"
          }}>
            <h3>🤖 التحليل:</h3>
            <div style={{ whiteSpace: "pre-line" }}>
              {data.ai_analysis}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Upload;
