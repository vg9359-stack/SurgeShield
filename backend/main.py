import os
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import numpy as np
import tifffile as tiff
from typing import List, Dict, Any
from sqlalchemy.orm import Session
import physics
# Database Imports (Neon PostgreSQL Connection)
from database import engine, get_db, init_db
import models

# Import PDF generator helper (Make sure pdf_report.py is in the backend/ folder)
try:
    from pdf_report import generate_pdf_report
except ImportError:
    generate_pdf_report = None

# App Lifecycle Manager to run database initialization on boot
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs schema and populates settlement seed data in Neon DB on startup
    init_db()
    yield

app = FastAPI(
    title="HydroGuard AI Engine API",
    description="2D Dam Break Inundation Engine with Real DEM Ingestion & Alerting Support",
    version="1.3.0",
    lifespan=lifespan
)

# Enable CORS for Frontend Communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REQUEST / RESPONSE DATA SCHEMAS ---

class DamBreachRequest(BaseModel):
    dam_height: float = Field(..., gt=0, description="Height of dam breach in meters (hb)")
    reservoir_volume: float = Field(..., gt=0, description="Reservoir volume at breach in Million m³ (Vw)")
    failure_type: str = Field("overtopping", description="Failure mode: 'overtopping' or 'piping'")
    simulation_hours: float = Field(3.0, gt=0, le=24.0, description="Total simulation duration in hours")
    grid_size: int = Field(50, ge=20, le=200, description="Computational spatial grid resolution (N x N)")
    manning_n: float = Field(0.035, ge=0.01, le=0.15, description="Manning's roughness coefficient (n)")

class SettlementAlert(BaseModel):
    name: str
    population: int
    water_depth_m: float
    risk_level: str  # SAFE, WARNING, EVACUATE

class FrameData(BaseModel):
    time_min: float
    max_depth: float
    inundation_grid: List[List[float]]
    settlement_alerts: List[SettlementAlert] = []

class SimulationSummary(BaseModel):
    breach_width_m: float
    formation_time_min: float
    peak_discharge_m3s: float
    total_flooded_area_km2: float

class DamBreachResponse(BaseModel):
    summary: SimulationSummary
    frames: List[FrameData]

# --- DEM & VILLAGE DATA LOADERS ---

def load_dem_grid(grid_size: int) -> np.ndarray:
    """
    Loads real GeoTIFF/CartoDEM data from `data/dem.tif` using tifffile.
    Falls back to a synthetic river valley slope if file is absent or invalid.
    """
    possible_paths = [
        os.path.join("..", "data", "dem.tif"),
        os.path.join("data", "dem.tif"),
        os.path.join(os.path.dirname(__file__), "..", "data", "dem.tif")
    ]
    
    dem_path = None
    for p in possible_paths:
        if os.path.exists(p):
            dem_path = p
            break

    if dem_path:
        try:
            raw_dem = tiff.imread(dem_path)
            if raw_dem.ndim > 2:
                raw_dem = raw_dem[0]
            
            step_x = max(1, raw_dem.shape[0] // grid_size)
            step_y = max(1, raw_dem.shape[1] // grid_size)
            elevation = raw_dem[::step_x, ::step_y][:grid_size, :grid_size].astype(np.float64)
            
            print(f"[DEM LOADER] Successfully loaded real DEM from {dem_path}")
            return elevation
        except Exception as e:
            print(f"[DEM LOADER Warning] Failed to parse {dem_path}: {e}. Falling back to synthetic DEM.")

    print("[DEM LOADER] Using synthetic terrain model.")
    x_coords = np.linspace(0, 5000, grid_size)
    y_coords = np.linspace(0, 5000, grid_size)
    X, Y = np.meshgrid(x_coords, y_coords)
    return 150.0 - (X * 0.015) + (np.power((Y - 2500) / 500.0, 2) * 1.5)

def evaluate_settlements(water_depth_matrix: np.ndarray, db: Session = None) -> List[SettlementAlert]:
    """
    Evaluates risk status for downstream settlements fetched from Database or JSON fallback.
    """
    alerts = []
    settlements = []

    # Attempt fetching settlement data directly from PostgreSQL / Neon DB
    if db:
        try:
            db_settlements = db.query(models.Settlement).all()
            if db_settlements:
                for idx, s in enumerate(db_settlements):
                    # Map locations across simulated grid space
                    settlements.append({
                        "name": s.name,
                        "population": s.population or 1000,
                        "grid_x": (idx * 2) % water_depth_matrix.shape[0],
                        "grid_y": (idx * 3) % water_depth_matrix.shape[1],
                        "critical_depth_m": 1.0
                    })
        except Exception as e:
            # Rollback to prevent transaction poisoning across simulation frames
            db.rollback()
            print(f"[DB SETTLEMENT FETCH WARNING] Transaction rolled back: {e}")

    # Fallback to local villages.json if DB query fails or returns empty
    if not settlements:
        possible_village_paths = [
            os.path.join("..", "data", "villages.json"),
            os.path.join("data", "villages.json"),
            os.path.join(os.path.dirname(__file__), "..", "data", "villages.json")
        ]
        for vp in possible_village_paths:
            if os.path.exists(vp):
                try:
                    with open(vp, "r") as f:
                        settlements = json.load(f)
                    break
                except Exception:
                    pass

    N = water_depth_matrix.shape[0]
    for s in settlements:
        gx = min(s.get("grid_x", 0), N - 1)
        gy = min(s.get("grid_y", 0), N - 1)
        depth = round(float(water_depth_matrix[gx, gy]), 2)
        
        crit_depth = s.get("critical_depth_m", 1.0)
        if depth == 0.0:
            status = "SAFE"
        elif depth < crit_depth:
            status = "WARNING"
        else:
            status = "EVACUATE"

        alerts.append(SettlementAlert(
            name=s.get("name", "Settlement"),
            population=s.get("population", 0),
            water_depth_m=depth,
            risk_level=status
        ))

    return alerts

# --- HYDRODYNAMIC CALCULATIONS & NUMERICAL SOLVER ---

def calculate_froehlich_breach(hb: float, Vw_m3: float, failure_type: str):
    ko = 1.3 if failure_type.lower() == 'overtopping' else 1.0
    b_avg = 0.27 * ko * (Vw_m3 ** 0.32) * (hb ** 0.28)
    t_f_sec = 0.011 * (Vw_m3 ** 0.47) * (hb ** -0.90) * 3600.0
    q_peak = 3.1 * b_avg * (hb ** 1.5)
    return b_avg, t_f_sec, q_peak

def solve_shallow_water_2d(req: DamBreachRequest, db: Session = None):
    N = req.grid_size
    Vw_m3 = req.reservoir_volume * 1e6
    hb = req.dam_height
    
    b_avg, t_f_sec, q_peak = calculate_froehlich_breach(hb, Vw_m3, req.failure_type)
    dx = 5000.0 / N
    
    bed_elevation = load_dem_grid(N)

    water_depth = np.zeros((N, N), dtype=np.float64)
    dam_col = max(2, int(N * 0.15))
    water_depth[:, :dam_col] = hb

    total_seconds = int(req.simulation_hours * 3600)
    target_frames = 60
    sample_interval_sec = max(10, total_seconds // target_frames)

    frames = []
    time_elapsed = 0.0
    last_sampled_time = -sample_interval_sec

    while time_elapsed < total_seconds:
        max_h = max(np.max(water_depth), 0.1)
        cfl_dt = min(1.0, 0.4 * dx / np.sqrt(9.81 * max_h))
        dt = cfl_dt

        if time_elapsed <= t_f_sec:
            breach_ratio = max(0.01, time_elapsed / t_f_sec)
        else:
            breach_ratio = np.exp(-(time_elapsed - t_f_sec) / 7200.0)

        eta = bed_elevation + water_depth

        laplacian_eta = np.zeros_like(eta)
        laplacian_eta[1:-1, 1:-1] = (
            eta[2:, 1:-1] + eta[:-2, 1:-1] +
            eta[1:-1, 2:] + eta[1:-1, :-2] - 4.0 * eta[1:-1, 1:-1]
        )

        h_safe = np.maximum(water_depth, 0.001)
        diffusivity = (np.power(h_safe, 5/3) / req.manning_n) * 0.05 * breach_ratio
        diffusivity = np.clip(diffusivity, 0.0, 80.0)

        dh = (diffusivity * laplacian_eta / (dx ** 2)) * dt
        water_depth = np.maximum(0.0, water_depth + dh)

        if time_elapsed < t_f_sec:
            water_depth[:, :dam_col] = np.maximum(
                water_depth[:, :dam_col], 
                hb * (1.0 - 0.4 * breach_ratio)
            )

        if (time_elapsed - last_sampled_time) >= sample_interval_sec:
            downstream_grid = water_depth[:, dam_col:]
            alerts = evaluate_settlements(water_depth, db)
            
            frames.append(FrameData(
                time_min=round(time_elapsed / 60.0, 1),
                max_depth=round(float(np.max(downstream_grid)), 2),
                inundation_grid=np.round(water_depth, 2).tolist(),
                settlement_alerts=alerts
            ))
            last_sampled_time = time_elapsed

        time_elapsed += dt

    total_flooded_km2 = round((np.sum(water_depth > 0.1) * (dx * dx)) / 1e6, 2)

    summary = SimulationSummary(
        breach_width_m=round(b_avg, 2),
        formation_time_min=round(t_f_sec / 60.0, 2),
        peak_discharge_m3s=round(q_peak, 2),
        total_flooded_area_km2=total_flooded_km2
    )

    return DamBreachResponse(summary=summary, frames=frames)

# --- API ENDPOINTS ---

@app.get("/")
def read_root():
    return {
        "status": "Online",
        "project": "HydroGuard AI Dam Break Engine",
        "version": "1.3.0"
    }

@app.post("/api/simulate", response_model=DamBreachResponse)
def run_dam_break_simulation(payload: DamBreachRequest, db: Session = Depends(get_db)):
    try:
        response = solve_shallow_water_2d(payload, db)

        # Log simulation run to Neon DB
        try:
            sim_record = models.SimulationRun(
                failure_type=payload.failure_type,
                peak_discharge_m3s=response.summary.peak_discharge_m3s,
                formation_time_min=response.summary.formation_time_min,
                breach_width_m=response.summary.breach_width_m
            )
            db.add(sim_record)
            db.commit()
            print("[DB SUCCESS] Logged simulation run to Neon DB.")
        except Exception as db_err:
            db.rollback()
            print(f"[DB LOG WARNING] {db_err}")

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation Solver Error: {str(e)}")

@app.post("/api/generate-pdf-report")
def download_pdf_report(payload: DamBreachRequest, db: Session = Depends(get_db)):
    if generate_pdf_report is None:
        raise HTTPException(status_code=500, detail="pdf_report.py module missing in backend directory.")
    try:
        res = solve_shallow_water_2d(payload, db)
        
        final_alerts = []
        if res.frames and res.frames[-1].settlement_alerts:
            final_alerts = [a.dict() for a in res.frames[-1].settlement_alerts]

        summary_payload = {
            "dam_name": "Tehri Dam",
            "state": "Uttarakhand",
            "river": "Bhagirathi",
            "breach_width_m": res.summary.breach_width_m,
            "formation_time_min": res.summary.formation_time_min,
            "peak_discharge_m3s": res.summary.peak_discharge_m3s,
            "total_flooded_area_km2": res.summary.total_flooded_area_km2,
            "simulation_hours": payload.simulation_hours,
            "grid_resolution": f"{payload.grid_size} x {payload.grid_size}",
            "risk_summary": final_alerts
        }
        
        pdf_filename = "Dam_Break_Inundation_Report.pdf"
        generate_pdf_report(summary_payload, pdf_filename)
        
        return FileResponse(
            path=pdf_filename,
            filename=pdf_filename,
            media_type="application/pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF Generation Error: {str(e)}")

@app.get("/api/export-geojson")
def export_geojson_boundary():
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"hazard_level": "High Risk", "max_depth_m": 4.5},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [78.0322, 30.3165],
                        [78.0450, 30.3200],
                        [78.0500, 30.3100],
                        [78.0322, 30.3165]
                    ]]
                }
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)