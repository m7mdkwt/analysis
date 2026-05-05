import React, { useState } from "react";
import axios from "axios";
import Plot from "react-plotly.js";

const API_URL = "https://web-production-85e50.up.railway.app/upload";

function Upload() {
  const [file, setFile] = useState(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!file) return alert("اختر ملف Excel");

    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);

      const res = await axios.post(API_URL, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      console.log("DATA:", res.data);
      setData(res.data);

    } catch (err) {
      console.log("ERROR:", err);
      alert(JSON.stringify(err.response?.data || "Unknown error"));
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

      {/* رفع الملف */}
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

      {/* 🔥 أهم حماية ضد الصفحة البيضاء */}
      {data && data.preview && (
        <div style={{ marginTop: "20px" }}>

          {/* معلومات */}
          <h3>📌 معلومات:</h3>
          <p>عدد الصفوف: {data.rows}</p>

          {/* الأعمدة */}
          <h4>الأعمدة:</h4>
          <ul>
            {data.columns.map((col, i) => (
              <li key={i}>{col}</li>
            ))}
          </ul>

          {/* 📊 Charts تلقائية */}
          <h3>📊 الرسوم:</h3>

          {data.charts && data.charts.length > 0 ? (
            data.charts.map((chart, i) => (
              <Plot
                key={i}
                style={{ width: "100%", marginBottom: "20px" }}
                data={[{
                  x: chart.x,
                  y: chart.y,
                  labels: chart.labels,
                  values: chart.values,
                  type: chart.type,
                  mode: chart.type === "scatter" ? "markers" : undefined
                }]}
                layout={{ title: chart.title }}
              />
            ))
          ) : (
            <p>لا يوجد رسوم مناسبة</p>
          )}

          {/* 🧠 Insights */}
          <h3>🧠 التحليل:</h3>

          {data.insights && data.insights.length > 0 ? (
            <ul>
              {data.insights.map((insight, i) => (
                <li key={i}>{insight}</li>
              ))}
            </ul>
          ) : (
            <p>لا يوجد insights</p>
          )}

          {/* 📋 Preview */}
          <h3>📋 عينة البيانات:</h3>

          <div style={{ overflowX: "auto" }}>
            <table border="1" style={{ width: "100%", background: "white" }}>
              <thead>
                <tr>
                  {data.columns.map((col, i) => (
                    <th key={i}>{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.preview.map((row, i) => (
                  <tr key={i}>
                    {data.columns.map((col, j) => (
                      <td key={j}>{row[col]}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

        </div>
      )}
    </div>
  );
}

export default Upload;
