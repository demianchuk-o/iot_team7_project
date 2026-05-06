"""
Генерує OSRM-маршрут між waypoints і зберігає у GeoJSON.
Підтримує іменовані профілі маршрутів через POI-довідник.
"""
import argparse
import json
import sys
from pathlib import Path

import requests


POI = {
    "khreshchatyk":  (30.5234, 50.4501),  # Хрещатик / Майдан Незалежності
    "sofia":         (30.5145, 50.4530),  # Софія Київська
    "andriivskyi":   (30.5170, 50.4585),  # Андріївський узвіз
    "podil":         (30.5168, 50.4660),  # Поділ / Контрактова пл.
    "lukianivska":   (30.4870, 50.4670),  # Лук'янівка
    "obolon":        (30.5005, 50.5070),  # Оболонь
    "mariinskyi":    (30.5390, 50.4470),  # Маріїнський парк
    "lavra":         (30.5570, 50.4350),  # Києво-Печерська Лавра
    "naberezhna":    (30.5400, 50.4500),  # Набережне шосе
    "olympic":       (30.5215, 50.4335),  # НСК "Олімпійський"
    "palats_sportu": (30.5235, 50.4360),  # Палац Спорту
    "demiivska":     (30.5160, 50.4090),  # Деміївська пл.
    "vdng":          (30.4940, 50.3850),  # ВДНГ
    "zhuliany":      (30.4500, 50.4040),  # Аеропорт "Київ" (Жуляни)
    "darnytsia":     (30.6320, 50.4400),  # Дарниця (лівий берег)
    "rusanivka":     (30.5810, 50.4500),  # Русанівка (через Дніпро)
}


# === Готові профілі маршрутів ================================================

ROUTE_PROFILES = {
    "center": {
        "description": "Центр: Хрещатик → Софія → Андріївський → Поділ → Хрещатик",
        "waypoints": ["khreshchatyk", "sofia", "andriivskyi", "podil", "khreshchatyk"],
    },
    "pechersk": {
        "description": "Печерськ-тур: Хрещатик → Олімпійський → Маріїнський → Лавра → Хрещатик",
        "waypoints": ["khreshchatyk", "olympic", "mariinskyi", "lavra", "khreshchatyk"],
    },
    "grand_tour": {
        "description": "Велике коло правим берегом: центр → Поділ → Оболонь → Лук'янівка → центр",
        "waypoints": ["khreshchatyk", "podil", "obolon", "lukianivska", "khreshchatyk"],
    },
    "south": {
        "description": "На південь: Хрещатик → Деміївка → ВДНГ → Жуляни → Хрещатик",
        "waypoints": ["khreshchatyk", "demiivska", "vdng", "zhuliany", "khreshchatyk"],
    },
    "naberezhna_loop": {
        "description": "Набережна-кільце: набережна → Маріїнський → Лавра → назад",
        "waypoints": ["naberezhna", "mariinskyi", "lavra", "naberezhna"],
    },
    "two_banks": {
        "description": "Через Дніпро: центр → Русанівка → Дарниця → назад",
        "waypoints": ["khreshchatyk", "rusanivka", "darnytsia", "rusanivka", "khreshchatyk"],
    },
    "compact": {
        "description": "Маленьке кільце в центрі (старий дефолт)",
        "waypoints": [
            (30.5234, 50.4501),
            (30.5400, 50.4520),
            (30.5300, 50.4580),
            (30.5234, 50.4501),
        ],
    },
    "everything": {
        "description": "Для довгих демо",
        "waypoints": [
            "khreshchatyk", "sofia", "podil", "obolon",
            "lukianivska", "lavra", "mariinskyi", "olympic",
            "khreshchatyk",
        ],
    },
}


OSRM_URL = "https://router.project-osrm.org/route/v1/driving/"

def resolve_waypoints(profile_name: str) -> tuple[list[tuple[float, float]], str]:
    """Розгортає назви POI у координати."""
    profile = ROUTE_PROFILES[profile_name]
    waypoints = []
    for w in profile["waypoints"]:
        if isinstance(w, str):
            if w not in POI:
                raise KeyError(f"POI '{w}' не знайдений у POI-довіднику")
            waypoints.append(POI[w])
        else:
            waypoints.append(tuple(w))
    return waypoints, profile["description"]


def fetch_route(waypoints: list[tuple[float, float]]) -> dict:
    coord_str = ";".join(f"{lon},{lat}" for lon, lat in waypoints)
    url = f"{OSRM_URL}{coord_str}?overview=full&geometries=geojson"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()
    if not data.get("routes"):
        raise RuntimeError("OSRM не повернув жодного маршруту")
    route = data["routes"][0]
    return {
        "geometry": route["geometry"],
        "distance_m": route["distance"],
        "duration_s": route["duration"],
    }


def list_profiles() -> None:
    print("Доступні профілі маршрутів:\n")
    for name, profile in ROUTE_PROFILES.items():
        print(f"  {name:20s} — {profile['description']}")
    print(f"\nВсього POI у довіднику: {len(POI)}")
    print(f"  {', '.join(POI.keys())}")


def main():
    parser = argparse.ArgumentParser(
        description="Генерує OSRM-маршрут між waypoints і зберігає у GeoJSON.",
    )
    parser.add_argument(
        "--profile", "-p",
        default="center",
        help=f"Назва профілю (default: center). Перелік: {', '.join(ROUTE_PROFILES)}",
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="Показати доступні профілі і вийти.",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Шлях вихідного файлу (default: MapView/route.json)",
    )
    args = parser.parse_args()

    if args.list:
        list_profiles()
        return

    if args.profile not in ROUTE_PROFILES:
        print(f"ERROR: невідомий профіль '{args.profile}'\n", file=sys.stderr)
        list_profiles()
        sys.exit(1)

    out_path = (
        Path(args.output) if args.output
        else Path(__file__).resolve().parent.parent.parent / "MapView" / "route.json"
    )

    waypoints, description = resolve_waypoints(args.profile)
    print(f"Profile: {args.profile}")
    print(f"  {description}")
    print(f"  {len(waypoints)} waypoints")

    print("Fetching route via OSRM...")
    result = fetch_route(waypoints)

    print(f"  Got {len(result['geometry']['coordinates'])} route points")
    print(f"  Distance: {result['distance_m'] / 1000:.2f} km")
    print(f"  Estimated drive time: {result['duration_s'] / 60:.1f} min")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result["geometry"], indent=2))
    print(f"Saved to {out_path}")


if __name__ == "__main__":
    try:
        main()
    except (requests.RequestException, RuntimeError, KeyError) as e:
        print(f"FATAL: {e}", file=sys.stderr)
        sys.exit(1)