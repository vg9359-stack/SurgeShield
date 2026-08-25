import numpy as np

class BreachEngine:
    def __init__(self, mode: str = "overtopping"):
        # Ko = 1.3 for overtopping failure, 1.0 for piping failure
        self.Ko = 1.3 if mode.lower() == "overtopping" else 1.0

    def compute_froehlich_parameters(self, height_m: float, volume_m3: float):
        """
        Calculates peak discharge, breach width, and failure time using Froehlich (2008).
        """
        g = 9.81
        h_w = height_m
        V_w = volume_m3

        # Froehlich empirical formulas
        b_avg = 0.27 * self.Ko * (V_w ** 0.32) * (h_w ** 0.19)
        t_f_seconds = 3600.0 * 63.2 * np.sqrt(V_w / (g * (h_w ** 2)))
        
        # Ensure minimum failure time threshold (e.g., 5 mins) to prevent division errors
        t_f_seconds = max(300.0, t_f_seconds)

        q_peak = 0.607 * (V_w ** 0.295) * (h_w ** 1.24)

        return {
            "q_peak_m3s": float(q_peak),
            "b_avg_m": float(b_avg),
            "t_failure_sec": float(t_f_seconds),
            "t_failure_min": float(t_f_seconds / 60.0)
        }

    def generate_triangular_hydrograph(self, q_peak: float, t_failure_sec: float, total_sim_time_sec: float, dt: float):
        """
        Generates a time-series inflow hydrograph Q(t) using a triangular hydrograph shape:
        - Linear rise to Q_peak at t = t_failure
        - Exponential recession curve back to zero baseflow
        """
        time_steps = np.arange(0, total_sim_time_sec + dt, dt)
        hydrograph = np.zeros_like(time_steps)

        for i, t in enumerate(time_steps):
            if t <= t_failure_sec:
                # Linear ramp up to peak discharge
                hydrograph[i] = (t / t_failure_sec) * q_peak
            else:
                # Exponential recession decay post-breach
                decay_rate = 3.0 / (t_failure_sec * 2)
                hydrograph[i] = q_peak * np.exp(-decay_rate * (t - t_failure_sec))

        return time_steps, hydrograph


# Quick test
if __name__ == "__main__":
    engine = BreachEngine(mode="overtopping")
    
    # Test parameters: Dam height = 30 meters, Reservoir volume = 15 million m³
    params = engine.compute_froehlich_parameters(height_m=30.0, volume_m3=15e6)
    
    print(f"[Breach Engine] Froehlich Breach Output:")
    print(f"  - Peak Discharge (Q_peak): {params['q_peak_m3s']:.2f} m³/s")
    print(f"  - Failure Time (t_f): {params['t_failure_min']:.2f} minutes")
    print(f"  - Average Breach Width: {params['b_avg_m']:.2f} meters")

    t, Q = engine.generate_triangular_hydrograph(
        q_peak=params['q_peak_m3s'], 
        t_failure_sec=params['t_failure_sec'], 
        total_sim_time_sec=7200, 
        dt=1.0
    )
    print(f"  - Hydrograph array created: {len(Q)} time steps generated.")