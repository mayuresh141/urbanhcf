import { MapContainer, TileLayer, GeoJSON, useMap } from "react-leaflet";
import { useState, useEffect } from "react";
import L from "leaflet";

/** Sequential color for UHI / counterfactual / LST */
function getUHIColor(v) {
  if (typeof v !== "number") return "#ccc";
  return v > 4 ? "#800026" :
         v > 3 ? "#BD0026" :
         v > 1 ? "#E31A1C" :
         v > 0 ? "#FC4E2A" :
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

/** Auto-fit bounds whenever geojson changes */
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
  } else {
    title = activeLayer === "lst" ? "LST (relative)" : "UHI (°C)";
    items = [
      { color: "#2C7BB6", label: "< 0" },
      { color: "#FC4E2A", label: "0–1" },
      { color: "#E31A1C", label: "1–3" },
      { color: "#BD0026", label: "3–4" },
      { color: "#800026", label: "> 4" },
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

  const hasData = geojson?.features?.length > 0;

  const styleFn = (feature) => {
    const p = feature.properties ?? {};

    switch (activeLayer) {
      case "lst":
        const lstNorm = (p.lst ?? 300) - 300;
        return {
          fillColor: getUHIColor(lstNorm / 5),
          fillOpacity: 0.7,
          color: "#444",
          weight: 0.3,
        };

      case "counterfactual_uhi":
        return {
          fillColor: getUHIColor(p.counterfactual_uhi),
          fillOpacity: 0.7,
          color: "#444",
          weight: 0.3,
        };

      case "delta_uhi":
        return {
          fillColor: getDeltaColor(p.delta_uhi),
          fillOpacity: 0.7,
          color: "#444",
          weight: 0.3,
        };

      case "uhi":
      default:
        return {
          fillColor: getUHIColor(p.uhi),
          fillOpacity: 0.7,
          color: "#444",
          weight: 0.3,
        };
    }
  };

  const formatValue = (v, suffix = "") =>
    typeof v === "number" ? v.toFixed(2) + suffix : "N/A";

  return (
    <MapContainer
      center={[34.05, -118.25]}
      zoom={9}
      style={{ height: "100%", width: "100%" }}
    >
      <TileLayer
        attribution="© OpenStreetMap"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

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

      {/* Only render spatial layers if geojson exists */}
      {hasData && (
        <>
          <FitBounds geojson={geojson} />
          <Legend activeLayer={activeLayer} />

          <GeoJSON
            key={geojson.features.length}
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
