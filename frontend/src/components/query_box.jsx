import { useState } from "react";
import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE_URL;

export default function QueryBox({ onResult }) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);

  const exampleQueries = [
    "Analyze UHI for Irvine",
    "What if green cover increased in Pasadena by 10%?",
    "How would reducing concrete affect UHI in LA?",
    "Explain UHI in simple terms",
  ];

  const runAnalysis = async () => {
    if (!query.trim()) return;

    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/analyze`, { query });

      onResult({
        run_id: res.data?.run_id || null,
        text: res.data?.analysis || "",
      });
    } catch (err) {
      onResult({
        run_id: null,
        text: "Error processing query. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {/* Example Queries */}
      <div style={styles.examples}>
        <div style={styles.examplesTitle}>Try examples:</div>
        {exampleQueries.map((q, i) => (
          <div
            key={i}
            style={styles.exampleItem}
            onClick={() => setQuery(q)}
          >
            {q}
          </div>
        ))}
      </div>
      <textarea
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault(); // prevent newline
            runAnalysis();
          }
        }}
        placeholder="Ask a question about urban heat islands..."
        rows={3}
        style={styles.textarea}
      />

      <button
        onClick={runAnalysis}
        disabled={loading}
        style={styles.button}
      >
        {loading ? "Analyzing..." : "Analyze"}
      </button>
      {/* Cold start note – only while loading */}
      {loading && (
        <p
          style={{
            marginTop: "6px",
            fontSize: "11px",
            color: "#666",
            lineHeight: "1.4",
          }}
        >
          ⏱️ First query may take 2–3 minutes while the server starts (free-tier cold start).
        </p>
      )}
    </div>
  );
}

const styles = {
  textarea: {
    width: "96%",
    padding: "8px",
    fontSize: "13px",
    borderRadius: "4px",
    border: "1px solid #ccc",
    resize: "none",
  },
  button: {
    marginTop: "8px",
    width: "100%",
    padding: "8px",
    fontSize: "13px",
    cursor: "pointer",
  },
  examples: {
    marginTop: "12px",
    fontSize: "12px",
    color: "#555",
  },
  examplesTitle: {
    marginBottom: "6px",
    fontWeight: "bold",
  },
  exampleItem: {
    cursor: "pointer",
    marginBottom: "4px",
    color: "#2563eb",
  },
};
