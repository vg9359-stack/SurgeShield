from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import math

app = FastAPI(title="SurgeShield Simulation Engine")

# Enable CORS for local HTML testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SimulationRequest(BaseModel):
    dam_key: str
    lat: float
    lng: float
    volume: float  # m³
    height: float  # meters

# Real Dam Downstream Settlement Data Dictionary
SETTLEMENTS_DB = {
    "chembarambakkam": [
        {"name": "Kundu Rathur", "dist_km": 4.5, "elev_diff": 8.0},
        {"name": "Anakaputhur", "dist_km": 11.2, "elev_diff": 4.0},
        {"name": "Porur Suburb", "dist_km": 8.0, "elev_diff": 6.5}
    ],
    "puzhal": [
        {"name": "Red Hills Market", "dist_km": 2.1, "elev_diff": 3.0},
        {"name": "Madhavaram", "dist_km": 6.8, "elev_diff": 5.2},
        {"name": "Kolathur", "dist_km": 9.5, "elev_diff": 7.0}
    ],
    "poondi": [
        {"name": "Ramanjeri", "dist_km": 3.4, "elev_diff": 6.0},
        {"name": "Tiruvallur Town", "dist_km": 12.0, "elev_diff": 12.0},
        {"name": "Veeraraghavapuram", "dist_km": 7.5, "elev_diff": 8.5}
    ],
    "cholavaram": [
        {"name": "Karanodai", "dist_km": 3.8, "elev_diff": 4.5},
        {"name": "Sholavaram Village", "dist_km": 1.8, "elev_diff": 2.1},
        {"name": "Padiyanallur", "dist_km": 5.2, "elev_diff": 5.0}
    ],
    "kallanai": [
        {"name": "Tiruchirappalli East", "dist_km": 14.0, "elev_diff": 15.0},
        {"name": "Koviladi", "dist_km": 5.1, "elev_diff": 3.5},
        {"name": "Thiruvaiyaru", "dist_km": 18.5, "elev_diff": 10.0}
    ]
}

@app.post("/api/run-simulation")
def run_simulation(req: SimulationRequest):
    g = 9.81
    k_o = 1.3  # Overtopping assumption

    # 1. Froehlich Empirical Calculations
    b_avg = 0.27 * k_o * (req.volume ** 0.32) * (req.height ** 0.19)
    t_failure_min = (63.2 * math.sqrt(req.volume / (g * (req.height ** 2)))) / 60.0
    q_peak = 0.607 * (req.volume ** 0.295) * (req.height ** 1.24)

    # 2. Downstream Threat Assessment
    settlements = SETTLEMENTS_DB.get(req.dam_key, [
        {"name": "Downstream Zone A", "dist_km": 5.0, "elev_diff": 5.0},
        {"name": "Downstream Zone B", "dist_km": 12.0, "elev_diff": 10.0}
    ])
    
    assessed_settlements = []
    # Wave celerity estimation: V = sqrt(g * h)
    wave_velocity = math.sqrt(g * (req.height * 0.4)) * 3.6  # km/h
    
    for s in settlements:
        arrival_time = round((s["dist_km"] / wave_velocity) * 60.0, 1)
        # Attenuated depth estimation
        depth = max(0.2, round((req.height * 0.35) * math.exp(-0.1 * s["dist_km"]), 2))
        
        status = "EVACUATE" if depth >= 1.0 else ("WARNING" if depth >= 0.3 else "MONITOR")
        assessed_settlements.append({
            "name": s["name"],
            "arrival_min": arrival_time,
            "depth_m": depth,
            "status": status
        })

    # 3. Dynamic GeoJSON Flood Extent Polygon Generation
    lat, lng = req.lat, req.lng
    spread = 0.015 + (req.volume / 2e9) * 0.03
    
    geojson_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"hazard_level": "High", "risk_color": "#dc2626"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [lng, lat],
                        [lng + spread * 0.4, lat - spread * 0.5],
                        [lng + spread * 0.8, lat - spread * 1.2],
                        [lng - spread * 0.2, lat - spread * 1.5],
                        [lng - spread * 0.5, lat - spread * 0.6],
                        [lng, lat]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {"hazard_level": "Moderate", "risk_color": "#f59e0b"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [lng + spread * 0.4, lat - spread * 0.5],
                        [lng + spread * 1.2, lat - spread * 1.8],
                        [lng + spread * 0.5, lat - spread * 2.2],
                        [lng - spread * 0.6, lat - spread * 2.0],
                        [lng - spread * 0.2, lat - spread * 1.5],
                        [lng + spread * 0.4, lat - spread * 0.5]
                    ]]
                }
            }
        ]
    }

    return {
        "metrics": {
            "b_avg": f"{b_avg:.1f} meters",
            "t_failure": f"{t_failure_min:.1f} mins",
            "q_peak": f"{round(q_peak):,} m³/s",
            "raw_q_peak": round(q_peak)
        },
        "settlements": assessed_settlements,
        "geojson": geojson_data
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)