import numpy as np

class SettlementRiskEngine:
    def __init__(self, settlements: list, dx: float = 100.0, dy: float = 100.0):
        """
        settlements: List of dicts with keys: name, grid_x, grid_y
        Example: [{"name": "Village A", "grid_x": 15, "grid_y": 25}]
        """
        self.settlements = settlements
        self.dx = dx
        self.dy = dy
        
        # Initialize tracking storage per settlement
        self.results = {}
        for s in self.settlements:
            self.results[s["name"]] = {
                "grid_pos": (s["grid_y"], s["grid_x"]),
                "arrival_time_min": None,
                "max_depth_m": 0.0,
                "max_velocity_ms": 0.0,
                "status": "SAFE"
            }

    def update(self, current_sim_time_sec: float, h_grid: np.ndarray, u_grid: np.ndarray, v_grid: np.ndarray):
        """
        Called after every solver iteration to evaluate local depth and velocity.
        """
        for s in self.settlements:
            name = s["name"]
            gy, gx = s["grid_y"], s["grid_x"]

            # Extract local depth and velocity magnitude
            depth = h_grid[gy, gx]
            velocity = np.sqrt(u_grid[gy, gx]**2 + v_grid[gy, gx]**2)
            
            res = self.results[name]

            # Track Maximum Depth and Velocity
            if depth > res["max_depth_m"]:
                res["max_depth_m"] = float(depth)
            if velocity > res["max_velocity_ms"]:
                res["max_velocity_ms"] = float(velocity)

            # Record First Arrival Time when water depth exceeds 0.05 meters threshold
            if depth >= 0.05 and res["arrival_time_min"] is None:
                res["arrival_time_min"] = float(current_sim_time_sec / 60.0)

            # Classify Risk Category
            hazard_factor = res["max_depth_m"] * res["max_velocity_ms"]
            
            if res["max_depth_m"] >= 1.0 or hazard_factor >= 1.5:
                res["status"] = "EVACUATE"
            elif res["max_depth_m"] >= 0.3 or res["max_velocity_ms"] >= 1.5:
                if res["status"] != "EVACUATE":
                    res["status"] = "WARNING"

    def get_summary(self) -> dict:
        return self.results


# Quick test
if __name__ == "__main__":
    targets = [
        {"name": "Downstream Village A", "grid_x": 20, "grid_y": 25},
        {"name": "Township B", "grid_x": 40, "grid_y": 25}
    ]
    
    risk_analyzer = SettlementRiskEngine(settlements=targets)

    # Mock spatial matrices (50x50 grid)
    h_mock = np.zeros((50, 50))
    u_mock = np.zeros((50, 50))
    v_mock = np.zeros((50, 50))

    # Simulate flood wave reaching Village A at t = 600s (10 min)
    h_mock[25, 20] = 1.4  # Depth 1.4m (Triggers EVACUATE)
    u_mock[25, 20] = 1.2

    risk_analyzer.update(current_sim_time_sec=600.0, h_grid=h_mock, u_grid=u_mock, v_grid=v_mock)
    
    summary = risk_analyzer.get_summary()
    print("[Risk Engine Summary]:")
    for village, metrics in summary.items():
        print(f"  - {village}: Status = {metrics['status']} | Max Depth = {metrics['max_depth_m']:.2f}m | Arrival = {metrics['arrival_time_min']} mins")