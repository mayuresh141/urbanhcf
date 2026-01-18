import { useState } from "react";
import axios from "axios";

export default function QueryBox({ onResult }) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const runAnalysis = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);

    try {
      const res = await axios.post("http://localhost:8000/analyze", {
        query,
      });

      // NEW: only pass run_id + text_output
      onResult({
        run_id: res.data.run_id,
        text_output: res.data.analysis || "",
      });

    } catch (err) {
      console.error(err);
      setError("Backend error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ marginTop: "16px" }}>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Enter query..."
        style={{ width: "100%", padding: "6px" }}
      />

      <button
        onClick={runAnalysis}
        disabled={loading}
        style={{ marginTop: "8px", width: "100%" }}
      >
        {loading ? "Running..." : "Run Analysis"}
      </button>

      {error && (
        <p style={{ color: "red", fontSize: "12px" }}>{error}</p>
      )}
    </div>
  );
}
