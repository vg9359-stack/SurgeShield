# 🌊 SurgeShield AI Engine

**SurgeShield** is a 2D hydrodynamic dam-breach assessment and flood-inundation simulation platform. Built with FastAPI and Python, it simulates reservoir failure dynamics using numerical shallow water approximations, evaluates downstream settlement risks, and exports hazard boundaries and PDF reports.

---

## 🚀 Features

* **Hydrodynamic Simulation Engine:** Solves 2D shallow water flow equations combined with Froehlich breach parameter formulas (overtopping & piping modes).
* **Real DEM Ingestion:** Processes real GeoTIFF/CartoDEM elevation data (`dem.tif`) with synthetic terrain fallback.
* **Downstream Risk Assessment:** Integrates directly with Neon PostgreSQL to track affected settlements and issue automated risk alerts (**SAFE**, **WARNING**, **EVACUATE**).
* **Automated Report Generation:** Generates downloadable, executive-level PDF inundation assessment reports.
* **GeoJSON Export:** Exports hazard inundation boundaries for GIS visualization.

---
