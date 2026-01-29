import { MapContainer, TileLayer, GeoJSON, useMap } from "react-leaflet";
import { useState, useEffect } from "react";
import L from "leaflet";

/** Sequential color for UHI / counterfactual */
function getUHIColor(v) {
  if (typeof v !== "number") return "#ccc";
  return v > 4 ? "#800026" :
         v > 3 ? "#BD0026" :
         v > 1 ? "#e35a1a" :
         v > 0 ? "#fc932a" :
                 "#2C7BB6";
}

/** Diverging color for delta_uhi */
function getDeltaColor(v) {
  if (typeof v !== "number") return "#ccc";
  return v > 1 ? "#b2182b" :
         v > 0.5 ? "#ef8a62" :
         v > 0 ? "#fddbc7" :
         v > -0.5 ? "#d1e5f0" :
         v > -1 ? "#67a9cf" :
                  "#2166ac";
}

/** Sequential color for LST (Kelvin) */
function getLSTColor(v) {
  if (typeof v !== "number") return "#ccc";
  return v > 315 ? "#800026" :
         v > 310 ? "#E31A1C" :
         v > 305 ? "#fc932a" :
         v > 295 ? "#fed976" :
                   "#2C7BB6";
}

/** Auto-fit bounds */
function FitBounds({ geojson }) {
  const map = useMap();

  useEffect(() => {
    if (geojson?.features?.length) {
      const layer = L.geoJSON(geojson);
      map.fitBounds(layer.getBounds(), { padding: [20, 20] });
    }
  }, [geojson, map]);

  return null;
}

/** Help Panel */
function HelpPanel({ onClose }) {
  return (
    <div style={{
      position: "absolute",
      top: 50,
      right: 10,
      zIndex: 1500,
      width: "320px",
      background: "white",
      padding: "12px",
      borderRadius: "8px",
      boxShadow: "0 2px 8px rgba(0,0,0,0.25)",
      fontSize: "13px",
      lineHeight: "1.4"
    }}>
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <b>About UrbanHCF</b>
        <button
          onClick={onClose}
          style={{
            border: "none",
            background: "transparent",
            cursor: "pointer",
            fontSize: "14px"
          }}
        >
          ✕
        </button>
      </div>

      <hr />

      <p>
        <b>UrbanHCF</b> is an interactive tool for analyzing
        <b> Urban Heat Island (UHI)</b> patterns using satellite-derived land
        surface temperature and counterfactual reasoning.
      </p>

      <p>UHI values indicate how much warmer a location is compared to nearby rural areas (in °C).
      Higher values represent stronger urban heat effects and greater heat stress. 
      You can ask questions and run "what-if" scenarios to explore how different interventions could improve thermal conditions in the city. 
      Try changing factors like building height, surface moisture, vegetation, and surface reflectivity.</p>

      <b>How to use</b>
      <ul>
        <li>Enter a natural language query (e.g. UHI in Anaheim, if vegetation is increased by 10%).</li>
        <li>The system simulates a counterfactual scenario.</li>
        <li>Results appear as spatial layers on the map(if mentioned).</li>
        <li>Click on any block on the map to see detailed values for that location.</li>
      </ul>

      <b>How to read the map</b>
      <ul>
        <li><b>UHI:</b> Current urban heat intensity (°C).</li>
        <li><b>Counterfactual UHI:</b> Simulated heat after intervention.</li>
        <li><b>ΔUHI:</b> Cooling or warming due to intervention.</li>
        <li><b>LST:</b> Land surface temperature (Kelvin).</li>
      </ul>
    </div>
  );
}

/** Legend */
function Legend({ activeLayer }) {
  let items = [];
  let title = "";

  if (activeLayer === "delta_uhi") {
    title = "ΔUHI (°C)";
    items = [
      { color: "#2166ac", label: "< -1" },
      { color: "#67a9cf", label: "-1 to -0.5" },
      { color: "#d1e5f0", label: "-0.5 to 0" },
      { color: "#fddbc7", label: "0 to 0.5" },
      { color: "#ef8a62", label: "0.5 to 1" },
      { color: "#b2182b", label: "> 1" },
    ];
  } else if (activeLayer === "lst") {
    title = "Land Surface Temperature (K)";
    items = [
      { color: "#2C7BB6", label: "< 295 K" },
      { color: "#fed976", label: "295–305 K" },
      { color: "#fc932a", label: "305–310 K" },
      { color: "#E31A1C", label: "310–315 K" },
      { color: "#800026", label: "> 315 K" },
    ];
  } else {
    title = "Urban Heat Island (°C)";
    items = [
      { color: "#2C7BB6", label: "< 0 (Cooler)" },
      { color: "#fcc02a", label: "0–1 (Neutral)" },
      { color: "#e35a1a", label: "1–3 (Mild urban heat)" },
      { color: "#BD0026", label: "3–4 (Strong UHI)" },
      { color: "#800026", label: "> 4 (Extreme heat stress zones)" },
    ];
  }

  return (
    <div style={{
      position: "absolute",
      bottom: 20,
      right: 10,
      zIndex: 1000,
      background: "white",
      padding: "8px",
      borderRadius: "6px",
      boxShadow: "0 1px 4px rgba(0,0,0,0.3)",
      fontSize: "12px"
    }}>
      <b>{title}</b>
      <div style={{ marginTop: "6px" }}>
        {items.map((item, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center" }}>
            <span style={{
              background: item.color,
              width: "14px",
              height: "14px",
              marginRight: "6px",
              display: "inline-block"
            }} />
            {item.label}
          </div>
        ))}
      </div>
    </div>
  );
}

/** Main MapView */
export default function MapView({ geojson }) {
  const [activeLayer, setActiveLayer] = useState("uhi");
  const [showHelp, setShowHelp] = useState(false);

  const hasData = geojson?.features?.length > 0;

  const styleFn = (feature) => {
    const p = feature.properties ?? {};

    switch (activeLayer) {
      case "lst":
        return { fillColor: getLSTColor(p.lst), fillOpacity: 0.7, color: "#444", weight: 0.3 };
      case "counterfactual_uhi":
        return { fillColor: getUHIColor(p.counterfactual_uhi), fillOpacity: 0.7, color: "#444", weight: 0.3 };
      case "delta_uhi":
        return { fillColor: getDeltaColor(p.delta_uhi), fillOpacity: 0.7, color: "#444", weight: 0.3 };
      default:
        return { fillColor: getUHIColor(p.uhi), fillOpacity: 0.7, color: "#444", weight: 0.3 };
    }
  };

  const formatValue = (v, suffix = "") =>
    typeof v === "number" ? v.toFixed(2) + suffix : "N/A";

  return (
    <MapContainer center={[34.05, -118.25]} zoom={9} style={{ height: "100%", width: "100%" }}>
      <TileLayer attribution="© OpenStreetMap" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

      {/* Help icon */}
      <div style={{ position: "absolute", top: 10, right: 10, zIndex: 1400 }}>
      <button
        onClick={() => setShowHelp(!showHelp)}
        title="How to use UrbanHCF"
        style={{
          display: "flex",
          alignItems: "center",
          gap: "6px",
          padding: "6px 12px",
          borderRadius: "16px",
          border: "1px solid #aaa",
          background: "white",
          cursor: "pointer",
          fontSize: "12px",
          boxShadow: "0 1px 4px rgba(0,0,0,0.25)"
        }}
      >
        <span style={{ fontWeight: "bold" }}>ℹ</span>
        How to use
      </button>
    </div>

      {showHelp && <HelpPanel onClose={() => setShowHelp(false)} />}

      {/* Layer toggles */}
      <div style={{
        position: "absolute",
        bottom: 20,
        left: 10,
        zIndex: 1000,
        background: "white",
        padding: "8px",
        borderRadius: "6px",
        boxShadow: "0 1px 4px rgba(0,0,0,0.3)"
      }}>
        {["uhi", "counterfactual_uhi", "delta_uhi", "lst"].map((l) => (
          <button
            key={l}
            onClick={() => setActiveLayer(l)}
            style={{
              display: "block",
              margin: "4px 0",
              width: "150px",
              background: activeLayer === l ? "#ddd" : "#fff",
              border: "1px solid #aaa",
              cursor: "pointer"
            }}
          >
            {l}
          </button>
        ))}
      </div>

      {hasData && (
        <>
          <FitBounds geojson={geojson} />
          <Legend activeLayer={activeLayer} />
          <GeoJSON
            data={geojson}
            style={styleFn}
            onEachFeature={(feature, layer) => {
              const p = feature.properties ?? {};
              layer.bindPopup(`
                <b>LST:</b> ${formatValue(p.lst, " K")}<br/>
                <b>UHI:</b> ${formatValue(p.uhi, " °C")}<br/>
                <b>CF UHI:</b> ${formatValue(p.counterfactual_uhi, " °C")}<br/>
                <b>ΔUHI:</b> ${formatValue(p.delta_uhi, " °C")}
              `);
            }}
          />
        </>
      )}
    </MapContainer>
  );
}
