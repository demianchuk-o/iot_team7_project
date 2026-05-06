"""
Генерує синтетичні sensor-дані для парковок і світлофорів,
використовуючи реальні географічні координати з OpenStreetMap (Overpass API).
"""
import csv
import random
import sys
import time
from pathlib import Path
from typing import List, Tuple

import requests

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.osm.jp/api/interpreter",
]

HEADERS = {
    "User-Agent": "iot_team7_project/1.0 (KPI educational project; https://github.com/demianchuk-o/iot_team7_project)",
    "Accept": "application/json",
}

KYIV_CENTER_BBOX = (50.43, 30.50, 50.46, 30.55)  # (south, west, north, east)


def fetch_osm(query: str, max_retries: int = 3) -> List[dict]:
    """
    Виконує Overpass-запит з ротацією endpoints і повторами.
    Повертає список elements.
    """
    last_error = None

    for attempt in range(max_retries):
        for endpoint in OVERPASS_ENDPOINTS:
            try:
                print(f"  [attempt {attempt + 1}] Trying {endpoint}...", flush=True)
                response = requests.post(
                    endpoint,
                    data={"data": query},
                    headers=HEADERS,
                    timeout=60,
                )

                if response.status_code == 200:
                    print(f"  Success!", flush=True)
                    return response.json().get("elements", [])

                if response.status_code in (429, 503, 504):
                    print(f"  {endpoint} overloaded ({response.status_code}), trying next...", flush=True)
                    last_error = f"{response.status_code} from {endpoint}"
                    continue

                if response.status_code == 400:
                    raise RuntimeError(f"Bad query (400): {response.text[:200]}")

                print(f"  {endpoint} returned {response.status_code}, trying next...", flush=True)
                last_error = f"{response.status_code} from {endpoint}"

            except requests.exceptions.Timeout:
                print(f"  {endpoint} timed out, trying next...", flush=True)
                last_error = f"timeout from {endpoint}"
            except requests.exceptions.RequestException as e:
                print(f"  {endpoint} failed: {e}", flush=True)
                last_error = str(e)

        if attempt < max_retries - 1:
            wait = 5 * (attempt + 1)  # 5s, 10s, 15s
            print(f"  All endpoints failed; waiting {wait}s before retry...", flush=True)
            time.sleep(wait)

    raise RuntimeError(f"All Overpass endpoints failed. Last error: {last_error}")


def fetch_traffic_lights(bbox: Tuple[float, float, float, float]) -> List[Tuple[float, float]]:
    s, w, n, e = bbox
    query = f"""
    [out:json][timeout:25];
    node["highway"="traffic_signals"]({s},{w},{n},{e});
    out;
    """
    elements = fetch_osm(query)
    coords = [(el["lat"], el["lon"]) for el in elements if "lat" in el and "lon" in el]
    print(f"  Found {len(coords)} traffic lights", flush=True)
    return coords


def fetch_parkings(bbox: Tuple[float, float, float, float]) -> List[Tuple[float, float]]:
    s, w, n, e = bbox
    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"="parking"]({s},{w},{n},{e});
      way["amenity"="parking"]({s},{w},{n},{e});
    );
    out center;
    """
    elements = fetch_osm(query)
    coords = []
    for el in elements:
        if el.get("type") == "node":
            coords.append((el["lat"], el["lon"]))
        elif el.get("type") == "way" and "center" in el:
            coords.append((el["center"]["lat"], el["center"]["lon"]))
    print(f"  Found {len(coords)} parkings", flush=True)
    return coords


def write_traffic_lights_csv(coords, out_path: Path, n_samples: int = 1000):
    if not coords:
        print(f"  WARNING: no coordinates, skipping {out_path}")
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    states_cycle = ["green", "yellow", "red"]
    with out_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["light_id", "current_state", "car_count", "latitude", "longitude"])
        for i in range(n_samples):
            idx = i % len(coords)
            lat, lon = coords[idx]
            state = states_cycle[i % 3]
            if state == "red":
                car_count = random.randint(8, 25)
            elif state == "yellow":
                car_count = random.randint(2, 8)
            else:
                car_count = random.randint(0, 3)
            writer.writerow([f"tl_{idx + 1}", state, car_count, lat, lon])
    print(f"  Wrote {n_samples} samples to {out_path}", flush=True)


def write_parkings_csv(coords, out_path: Path, n_samples: int = 200):
    if not coords:
        print(f"  WARNING: no coordinates, skipping {out_path}")
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    parkings = [
        {"id": f"park_{i + 1}", "lat": lat, "lon": lon,
         "total_spots": random.choice([20, 50, 75, 100, 150, 200])}
        for i, (lat, lon) in enumerate(coords)
    ]
    with out_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["parking_id", "is_occupied", "total_spots", "latitude", "longitude"])
        for _ in range(n_samples):
            p = random.choice(parkings)
            is_occupied = random.choices([0, 1], weights=[0.4, 0.6])[0]
            writer.writerow([p["id"], is_occupied, p["total_spots"], p["lat"], p["lon"]])
    print(f"  Wrote {n_samples} samples to {out_path}", flush=True)


def main():
    data_dir = Path(__file__).resolve().parent.parent / "src" / "data"

    print("Fetching real-world OSM data for Kyiv center...")
    print(f"Bbox: {KYIV_CENTER_BBOX}")

    print("\n[1/2] Traffic lights:")
    tl_coords = fetch_traffic_lights(KYIV_CENTER_BBOX)
    write_traffic_lights_csv(tl_coords, data_dir / "traffic_lights.csv")

    print("\n[2/2] Parkings:")
    p_coords = fetch_parkings(KYIV_CENTER_BBOX)
    write_parkings_csv(p_coords, data_dir / "parking.csv")

    print("\nDone.")


if __name__ == "__main__":
    try:
        main()
    except (requests.exceptions.RequestException, RuntimeError) as e:
        print(f"FATAL: {e}", file=sys.stderr)
        sys.exit(1)