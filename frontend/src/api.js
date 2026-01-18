import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function runQuery(query) {
  // For now, mock response
  return {
    bounds: [
      [33.6, -118.9], // SW
      [34.3, -117.6], // NE
    ],
    overlay_url: "test_uhi.png",
  };

  // Later (real):
  // const res = await axios.post(`${API_BASE}/query`, { query });
  // return res.data;
}
