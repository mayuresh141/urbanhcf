# urbanhcf
# UrbanHCF

UrbanHCF is an interactive web application for analyzing **Urban Heat Island (UHI)** effects and exploring **counterfactual scenarios** (what-if changes) in urban environments.

The system combines geospatial data, machine learning–driven reasoning, and an AI agent to help users understand how factors such as vegetation (green cover) influence urban heat patterns.

---

## What does it do?

- Accepts a **natural language query** about urban heat at a location  
- Uses an **agent-based reasoning pipeline (MCP)** to decide which analyses to run  
- Computes **Land Surface Temperature (LST)** and **Urban Heat Island (UHI)** metrics  
- Applies **counterfactual changes** (e.g., increased green cover interpreted as vegetation indices such as EVI)  
- Returns **interactive GeoJSON layers** visualized on a map  
- Produces a **concise, user-friendly explanation** of the results  

Results are cached temporarily using Redis to support concurrent users and smooth frontend interaction.

---

## Tech Stack

- **Frontend:** React, Leaflet  
- **Backend:** FastAPI (Python)  
- **Agent Framework:** MCP (tool-based reasoning)  
- **Caching:** Redis (Render Key-Value)  
- **Deployment:** Netlify (frontend), Render (backend)  

---

## Example

Below is an example of the UrbanHCF interface showing Urban Heat Island layers and counterfactual analysis results:

![UrbanHCF Example](./assets/urbanhcf_example.png)

---

## Notes

- Results are ephemeral and cached for a short duration.
- User-facing explanations are intentionally separated from system-level agent reasoning.
- This project is designed as a portfolio and research-oriented system rather than a chatbot.

---

More detailed documentation and architectural explanations will be added soon.

