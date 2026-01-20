import { useState } from "react";
import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE_URL;

export default function QueryBox({ onResult }) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const runAnalysis = async () => {
    const trimmed = query.trim();
    if (!trimmed) return;

    setLoading(true);
    setError(null);

    try {
      const res = await axios.post(`${API_BASE}/analyze`, {
        query: trimmed,
      });

      // ✅ Pass ONLY what backend actually returns
      onResult({
        run_id: res.data.run_id,
        text: res.data.analysis || "",
      });

    } catch (err) {
      console.error(err);
      setError("Failed to reach backend");
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
        disabled={loading}
        style={{
          width: "100%",
          padding: "6px",
          opacity: loading ? 0.7 : 1,
        }}
      />

      <button
        onClick={runAnalysis}
        disabled={loading || !query.trim()}
        style={{
          marginTop: "8px",
          width: "100%",
          cursor: loading ? "not-allowed" : "pointer",
        }}
      >
        {loading ? "Running analysis..." : "Run Analysis"}
      </button>

      {error && (
        <p style={{ color: "red", fontSize: "12px", marginTop: "6px" }}>
          {error}
        </p>
      )}
    </div>
  );
}
