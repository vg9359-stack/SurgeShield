import numpy as np

class HydrodynamicSolver2D:
    def __init__(self, elevation_grid: np.ndarray, dx: float = 100.0, dy: float = 100.0, manning_n: float = 0.035):
        self.Z = elevation_grid.copy()
        self.ny, self.nx = self.Z.shape
        self.dx = dx
        self.dy = dy
        self.n = manning_n
        self.g = 9.81

        # State Variables: Water depth (h), Velocity X (u), Velocity Y (v)
        self.h = np.zeros((self.ny, self.nx), dtype=np.float64)
        self.u = np.zeros((self.ny, self.nx), dtype=np.float64)
        self.v = np.zeros((self.ny, self.nx), dtype=np.float64)

    def step(self, dt: float, inflow_rate: float, dam_loc: tuple = (5, 50)):
        """
        Executes a single time-step (dt) update using Diffusive Wave / Explicit Finite Difference formulation.
        dam_loc: (grid_y, grid_x) index where the breached dam discharges water.
        """
        # 1. Apply Dam Inflow Source Term to Breach Cell
        dy_idx, dx_idx = dam_loc
        cell_area = self.dx * self.dy
        self.h[dy_idx, dx_idx] += (inflow_rate / cell_area) * dt

        # 2. Compute Total Water Surface Elevation (WSE = h + Z)
        H = self.h + self.Z

        # 3. Calculate Spatial WSE Gradients
        dH_dx = np.zeros_like(H)
        dH_dy = np.zeros_like(H)

        dH_dx[:, 1:-1] = (H[:, 2:] - H[:, :-2]) / (2 * self.dx)
        dH_dy[1:-1, :] = (H[2:, :] - H[:-2, :]) / (2 * self.dy)

        # 4. Update Velocities using Gravity Gradient & Manning's Friction
        # Avoid division by zero with small eps on depth h
        eps = 1e-4
        h_safe = np.maximum(self.h, eps)

        # Diffusive wave velocity estimation
        self.u = np.where(self.h > eps, - (1.0 / self.n) * (h_safe ** (2.0 / 3.0)) * np.sign(dH_dx) * np.sqrt(np.abs(dH_dx)), 0.0)
        self.v = np.where(self.h > eps, - (1.0 / self.n) * (h_safe ** (2.0 / 3.0)) * np.sign(dH_dy) * np.sqrt(np.abs(dH_dy)), 0.0)

        # Cap velocity bounds for numerical stability
        self.u = np.clip(self.u, -15.0, 15.0)
        self.v = np.clip(self.v, -15.0, 15.0)

        # 5. Mass Balance Continuity Update (Divergence of Fluxes)
        qx = self.h * self.u
        qy = self.h * self.v

        dqx_dx = np.zeros_like(H)
        dqy_dy = np.zeros_like(H)

        dqx_dx[:, 1:-1] = (qx[:, 2:] - qx[:, :-2]) / (2 * self.dx)
        dqy_dy[1:-1, :] = (qy[2:, :] - qy[:-2, :]) / (2 * self.dy)

        # Depth update
        dh_dt = - (dqx_dx + dqy_dy)
        self.h = np.maximum(0.0, self.h + dh_dt * dt)

        # Outflow Boundary Conditions (Water leaves grid boundaries freely)
        self.h[0, :] = 0.0
        self.h[-1, :] = 0.0
        self.h[:, 0] = 0.0
        self.h[:, -1] = 0.0

        return self.h, self.u, self.v


# Quick Test
if __name__ == "__main__":
    from backend.gis_engine import TerrainEngine
    
    # 1. Load Step 1 Terrain
    terrain_engine = TerrainEngine(grid_size=50)
    Z = terrain_engine.process_dem("data/dem.tif")
    
    # 2. Init Step 3 Solver
    solver = HydrodynamicSolver2D(elevation_grid=Z, dx=200.0, dy=200.0)
    
    # 3. Simulate 10 time steps with mock inflow of 5000 m³/s
    for t_step in range(10):
        h, u, v = solver.step(dt=2.0, inflow_rate=5000.0, dam_loc=(5, 25))
        max_depth = np.max(h)
        print(f"[Solver] Step {t_step+1}: Max Water Depth = {max_depth:.2f} meters")