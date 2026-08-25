import numpy as np
import tifffile as tiff
import os

class TerrainEngine:
    def __init__(self, grid_size: int = 100):
        self.grid_size = grid_size

    def process_dem(self, dem_file_path: str) -> np.ndarray:
        """
        Ingests real GeoTIFF DEM, downsamples to grid_size x grid_size,
        and enforces meter-scale elevation matrices.
        """
        if os.path.exists(dem_file_path):
            try:
                raw_dem = tiff.imread(dem_file_path)
                if raw_dem.ndim > 2:
                    raw_dem = raw_dem[0]  # Extract single elevation channel
                
                # Calculate downsampling stride
                step_x = max(1, raw_dem.shape[0] // self.grid_size)
                step_y = max(1, raw_dem.shape[1] // self.grid_size)
                
                # Slice and slice to standard N x N matrix
                elevation_grid = raw_dem[::step_x, ::step_y][:self.grid_size, :self.grid_size].astype(np.float64)
                
                # Handle invalid nodata values (e.g., negative background fills)
                elevation_grid[elevation_grid < -100] = np.nanmin(elevation_grid[elevation_grid > -100])
                
                print(f"[GIS Engine] Loaded DEM grid: {elevation_grid.shape} (Min: {np.min(elevation_grid):.1f}m, Max: {np.max(elevation_grid):.1f}m)")
                return elevation_grid
            
            except Exception as e:
                print(f"[GIS Engine Warning] DEM parse failed: {e}. Generating hydro-enforced synthetic terrain.")
        
        return self._generate_synthetic_valley()

    def _generate_synthetic_valley(self) -> np.ndarray:
        """
        Generates a synthetic river valley with downstream slope and V-shaped channel.
        """
        x = np.linspace(0, 10000, self.grid_size)  # 10 km domain
        y = np.linspace(0, 10000, self.grid_size)
        X, Y = np.meshgrid(x, y)
        
        # Longitudinal slope (150m down to 50m over 10km)
        downstream_slope = 150.0 - (X * 0.01)
        
        # Cross-sectional river valley parabolic shape centered at Y = 5000m
        valley_shape = np.power((Y - 5000.0) / 1000.0, 2) * 8.0
        
        elevation = downstream_slope + valley_shape
        return elevation

# Quick test
if __name__ == "__main__":
    engine = TerrainEngine(grid_size=50)
    dem = engine.process_dem("data/dem.tif")