import json
import os

class ExportEngine:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def export_geojson(self, h_grid, origin_lat: float = 18.5204, origin_lon: float = 73.8567, cell_size_deg: float = 0.0009):
        features = []
        ny, nx = len(h_grid), len(h_grid[0])

        for y in range(ny):
            for x in range(nx):
                depth = float(h_grid[y][x])
                if depth >= 0.05:
                    min_lon = origin_lon + (x * cell_size_deg)
                    max_lon = min_lon + cell_size_deg
                    max_lat = origin_lat - (y * cell_size_deg)
                    min_lat = max_lat - cell_size_deg

                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[
                                [min_lon, max_lat],
                                [max_lon, max_lat],
                                [max_lon, min_lat],
                                [min_lon, min_lat],
                                [min_lon, max_lat]
                            ]]
                        },
                        "properties": {
                            "depth_m": round(depth, 2),
                            "risk_color": "#ff0000" if depth >= 1.0 else "#ff9900" if depth >= 0.3 else "#ffff00"
                        }
                    }
                    features.append(feature)

        geojson_data = {"type": "FeatureCollection", "features": features}
        file_path = os.path.join(self.output_dir, "flood_inundation.geojson")
        
        with open(file_path, "w") as f:
            json.dump(geojson_data, f, indent=2)

        print(f"[Export Engine] GeoJSON written to {file_path}")
        return file_path

    def generate_html_report(self, breach_params: dict, risk_summary: dict, filename: str = "Dam_Break_Report.html"):
        html_path = os.path.join(self.output_dir, filename)
        
        rows = ""
        for name, metrics in risk_summary.items():
            arr_time = f"{metrics['arrival_time_min']:.1f} min" if metrics['arrival_time_min'] is not None else "N/A"
            bg_color = "#fee2e2" if metrics['status'] == "EVACUATE" else "#fef3c7"
            rows += f"""
            <tr style="background-color: {bg_color};">
                <td style="padding: 10px; border: 1px solid #ddd;">{name}</td>
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">{metrics['status']}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{metrics['max_depth_m']:.2f} m</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{arr_time}</td>
            </tr>
            """

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>SurgeShield Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 30px; background-color: #f8fafc; }}
                .container {{ max-width: 700px; background: white; padding: 25px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                h1 {{ color: #0f172a; border-bottom: 2px solid #0f172a; padding-bottom: 10px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
                th {{ background-color: #1e293b; color: white; padding: 10px; text-align: left; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>SurgeShield: Dam Break Inundation Report</h1>
                <h2>1. Hydrograph Parameters</h2>
                <p><b>Peak Outflow:</b> {breach_params.get('q_peak_m3s', 0):.2f} m³/s</p>
                <p><b>Failure Time:</b> {breach_params.get('t_failure_min', 0):.2f} minutes</p>
                <p><b>Average Breach Width:</b> {breach_params.get('b_avg_m', 0):.2f} meters</p>
                
                <h2>2. Downstream Risk Matrix</h2>
                <table>
                    <thead>
                        <tr><th>Settlement</th><th>Status</th><th>Max Depth</th><th>Arrival Time</th></tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>
        </body>
        </html>
        """

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"[Export Engine] Generated HTML Report at {html_path}")
        return html_path


if __name__ == "__main__":
    exporter = ExportEngine()
    
    # Simple list matrix without numpy
    h_test = [[0.0 for _ in range(10)] for _ in range(10)]
    h_test[5][5] = 1.8
    h_test[5][6] = 0.4

    exporter.export_geojson(h_test)
    
    mock_breach = {"q_peak_m3s": 8500.0, "t_failure_min": 45.0, "b_avg_m": 120.0}
    mock_risk = {
        "Village Alpha": {"status": "EVACUATE", "max_depth_m": 2.4, "arrival_time_min": 25.0},
        "Township Beta": {"status": "WARNING", "max_depth_m": 0.6, "arrival_time_min": 60.0}
    }

    exporter.generate_html_report(mock_breach, mock_risk)