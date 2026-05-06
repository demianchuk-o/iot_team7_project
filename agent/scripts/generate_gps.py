"""Генерує gps.csv як траєкторію по реальному маршруту з route.json."""
import csv
import json
from pathlib import Path

N_POINTS = 1000


def main():
    project_root = Path(__file__).resolve().parent.parent.parent
    route_path = project_root / "MapView" / "route.json"
    out_path = project_root / "agent" / "src" / "data" / "gps.csv"

    if not route_path.exists():
        print(f"ERROR: {route_path} not found. Run generate_route.py first.")
        return

    with route_path.open() as f:
        geo = json.load(f)
    coords = geo["coordinates"]

    # Інтерполюємо рівномірно
    n_segs = len(coords) - 1
    rows = []
    for i in range(N_POINTS):
        progress = i / (N_POINTS - 1)
        seg_float = progress * n_segs
        seg_idx = min(int(seg_float), n_segs - 1)
        t = seg_float - seg_idx
        lon1, lat1 = coords[seg_idx]
        lon2, lat2 = coords[seg_idx + 1]
        lat = lat1 + (lat2 - lat1) * t
        lon = lon1 + (lon2 - lon1) * t
        rows.append((lat, lon))

    with out_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["latitude", "longitude"])
        writer.writerows(rows)

    print(f"Wrote {len(rows)} GPS points to {out_path}")


if __name__ == "__main__":
    main()