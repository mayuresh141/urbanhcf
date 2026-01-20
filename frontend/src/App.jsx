import { useState, useEffect } from "react";
import QueryBox from "./components/query_box";
import MapView from "./components/map_view";
import sampleGeoJSON from "./data/sample_uhi.json";

const API_BASE = import.meta.env.VITE_API_BASE_URL;

export default function App() {
  const [runId, setRunId] = useState(null);
  const [analysisText, setAnalysisText] = useState("");
  const [geojson, setGeojson] = useState(null);
  const [loadingMap, setLoadingMap] = useState(false);

  // Called after POST /analyze
  const handleResult = ({ run_id, text }) => {
    // ✅ Always update text
    setAnalysisText(text || "");

    // ❗ Only trigger map polling if run_id exists
    if (!run_id) return;

    setRunId(run_id);
    setLoadingMap(true);
    setGeojson(null); // clear previous spatial result
  };

  // Load sample data for dev
  useEffect(() => {
    setGeojson(sampleGeoJSON);
    setAnalysisText(
      "Sample UHI data loaded. Mean LST: 318.5 K, Mean UHI: 2.1 °C"
    );
  }, []);

  // Poll Redis-backed result endpoint
  useEffect(() => {
    if (!runId) return;

    let intervalId;
    const startTime = Date.now();
    const maxPollingTime = 20000; // 20s

    const fetchGeoJSON = async () => {
      try {
        const res = await fetch(`${API_BASE}/results/${runId}`);
        if (!res.ok) return;

        const data = await res.json();

        if (data?.geojson) {
          setGeojson(data.geojson);
          setLoadingMap(false);
          clearInterval(intervalId);
        } else if (Date.now() - startTime > maxPollingTime) {
          setLoadingMap(false);
          clearInterval(intervalId);
          console.warn("Polling stopped: timeout reached");
        }
      } catch (err) {
        if (Date.now() - startTime > maxPollingTime) {
          setLoadingMap(false);
          clearInterval(intervalId);
          console.warn("Polling stopped due to error/timeout");
        }
      }
    };

    intervalId = setInterval(fetchGeoJSON, 2000);
    return () => clearInterval(intervalId);
  }, [runId]);

  return (
    <div style={styles.container}>
      {/* MAP */}
      <div style={styles.mapPane}>
        {loadingMap && (
          <div style={styles.mapOverlay}>
            Computing counterfactual map… (auto-stops after 20s)
          </div>
        )}
        <MapView geojson={geojson} />
      </div>

      {/* SIDEBAR */}
      <div style={styles.sidePane}>
        <h3>UrbanHCF</h3>
        <p style={{ fontSize: "14px", color: "#555" }}>
          Query urban heat island scenarios using satellite data and counterfactual analysis.
        </p>

        <QueryBox onResult={handleResult} />

        {analysisText && (
          <div style={styles.infoBox}>
            <h4>Analysis Summary</h4>
            <p>{analysisText}</p>
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  container: {
    display: "flex",
    height: "100vh",
    width: "100vw",
  },
  mapPane: {
    flex: 3,
    position: "relative",
  },
  mapOverlay: {
    position: "absolute",
    top: 10,
    right: 10,
    zIndex: 1200,
    background: "rgba(255,255,255,0.9)",
    padding: "6px 10px",
    borderRadius: "4px",
    fontSize: "12px",
  },
  sidePane: {
    flex: 1,
    padding: "16px",
    borderLeft: "1px solid #ddd",
    backgroundColor: "#fafafa",
    overflowY: "auto",
  },
  infoBox: {
    marginTop: "16px",
    padding: "10px",
    backgroundColor: "#fff",
    border: "1px solid #ddd",
    fontSize: "13px",
  },
};
