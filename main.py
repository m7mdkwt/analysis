import React, { useState } from "react";
import Plot from "react-plotly.js";

const API_URL = "https://web-production-85e50.up.railway.app/upload";

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

      const result = await res.json();

      console.log("SUCCESS:", result);

      if (!res.ok) {
        alert(JSON.stringify(result));
        return;
      }

      setData(result);
      setChartType("");
      setXColumn("");
      setYColumn("");

    } catch (err) {
      console.log("ERROR:", err);
      alert("فشل الاتصال بالسيرفر");
    } finally {
      setLoading(false);
    }
  };

  // 📊 Bar
  const renderBar = () => {
    if (!xColumn || !yColumn) return <p>⚠️ اختر X و Y</p>;

    if (typeof data.records[0][yColumn] !== "number") {
      return <p>⚠️ العمود Y يجب أن يكون رقم</p>;
    }

    const grouped = {};

    data.records.forEach(r => {
      const key = r[xColumn];
      const value = Number(r[yColumn]);

      if (!isNaN(value)) {
        grouped[key] = (grouped[key] || 0) + value;
      }
    });

    return (
      <Plot
        style={{ width: "100%" }}
        data={[{
          x: Object.keys(grouped),
          y: Object.values(grouped),
          type: "bar",
          marker: { color: "#007bff" }
        }]}
        layout={{
          title: `${yColumn} حسب ${xColumn}`
        }}
      />
    );
  };

  // 🥧 Pie
  const renderPie = () => {
    if (!xColumn || !yColumn) return <p>⚠️ اختر X و Y</p>;

    if (typeof data.records[0][yColumn] !== "number") {
      return <p>⚠️ العمود Y يجب أن يكون رقم</p>;
    }

    const grouped = {};

    data.records.forEach(r => {
      const key = r[xColumn];
      const value = Number(r[yColumn]);

      if (!isNaN(value)) {
        grouped[key] = (grouped[key] || 0) + value;
      }
    });

    return (
      <Plot
        style={{ width: "100%" }}
        data={[{
          labels: Object.keys(grouped),
          values: Object.values(grouped),
          type: "pie"
        }]}
        layout={{
          title: `توزيع ${yColumn} حسب ${xColumn}`
        }}
      />
    );
  };

  // 📈 Scatter
  const renderScatter = () => {
    if (!xColumn || !yColumn) return <p>⚠️ اختر X و Y</p>;

    if (
      typeof data.records[0][xColumn] !== "number" ||
      typeof data.records[0][yColumn] !== "number"
    ) {
      return <p>⚠️ Scatter يحتاج أعمدة رقمية</p>;
    }

    const x = data.records.map(r => r[xColumn]);
    const y = data.records.map(r => r[yColumn]);

    return (
      <Plot
        style={{ width: "100%" }}
        data={[{
          x: x,
          y: y,
          mode: "markers",
          type: "scatter",
          marker: { color: "red" }
        }]}
        layout={{
          title: `العلاقة بين ${xColumn} و ${yColumn}`,
          xaxis: { title: xColumn },
          yaxis: { title: yColumn }
        }}
      />
    );
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

          <h3>🎛️ تخصيص الرسم:</h3>

          <select
            value={chartType}
            onChange={(e) => setChartType(e.target.value)}
            style={{ width: "100%", marginBottom: "10px" }}
          >
            <option value="">اختر نوع الرسم</option>
            <option value="bar">Bar</option>
            <option value="pie">Pie</option>
            <option value="scatter">Scatter</option>
          </select>

          <select
            value={xColumn}
            onChange={(e) => setXColumn(e.target.value)}
            style={{ width: "100%", marginBottom: "10px" }}
          >
            <option value="">اختر X</option>
            {data.info.columns_names.map(col => (
              <option key={col}>{col}</option>
            ))}
          </select>

          <select
            value={yColumn}
            onChange={(e) => setYColumn(e.target.value)}
            style={{ width: "100%", marginBottom: "20px" }}
          >
            <option value="">اختر Y</option>
            {data.info.columns_names.map(col => (
              <option key={col}>{col}</option>
            ))}
          </select>

          {chartType === "bar" && renderBar()}
          {chartType === "pie" && renderPie()}
          {chartType === "scatter" && renderScatter()}

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
