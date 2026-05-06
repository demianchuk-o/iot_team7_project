import asyncio
import os
import threading
import time
import tkinter as tk

from shared.road_classifier import classify_road

import tkintermapview
from PIL import ImageTk

from datasource import Datasource
from file_datasource import FileDatasource
from marker_factory import (
    make_circle, make_diamond, make_triangle, make_car, COLORS,
)


# === Registry для типів сенсорів ============================================

SENSOR_HANDLERS = {}


def register_handler(sensor_type):
    def deco(fn):
        SENSOR_HANDLERS[sensor_type] = fn
        return fn
    return deco


@register_handler("road")
def handle_road(app, item):
    payload = item.get("payload") or {}
    state = payload.get("road_state") or "normal"
    app.handle_road_point(item["latitude"], item["longitude"], state, source="store")


@register_handler("parking")
def handle_parking(app, item):
    if not app.layers["parking"].get():
        return
    payload = item.get("payload") or {}
    app.set_parking_marker(
        item["latitude"], item["longitude"],
        bool(payload.get("is_occupied")),
        payload.get("total_spots"),
        item.get("sensor_id"),
    )


@register_handler("traffic_light")
def handle_traffic_light(app, item):
    if not app.layers["traffic_light"].get():
        return
    payload = item.get("payload") or {}
    app.set_traffic_light_marker(
        item["latitude"], item["longitude"],
        payload.get("current_state"),
        payload.get("car_count"),
        item.get("sensor_id"),
    )


# === MapView App =============================================================

class MapViewApp:
    MAX_PATH_POINTS    = 200
    MAX_EVENT_MARKERS  = 50
    EVENT_DEDUP_RADIUS = 0.0001
    UPDATE_INTERVAL_MS = 200
    STICKY_DURATION_S  = 5.0

    BG_DARK    = "#0f172a"
    BG_PANEL   = "#1e293b"
    FG_LIGHT   = "#e2e8f0"
    FG_MUTED   = "#94a3b8"
    FG_STICKY  = "#fbbf24"
    PATH_FILE  = "#6b7280"
    PATH_STORE = "#3b82f6"

    def __init__(self, user_id: int):
        self.root = tk.Tk()
        self.root.geometry("1200x800")
        self.root.title("IoT Road Monitor")
        self.root.configure(bg=self.BG_DARK)

        self.layers = {
            "parking":       tk.BooleanVar(value=True),
            "traffic_light": tk.BooleanVar(value=True),
            "events":        tk.BooleanVar(value=True),
            "path":          tk.BooleanVar(value=True),
        }

        self.car_marker = None
        self.path_file = []
        self.path_store = []
        self.file_path_line = None
        self.store_path_line = None
        self.active_parkings = {}
        self.active_traffic_lights = {}
        self.event_markers = []
        self.event_positions = []

        self._sticky_until = 0.0

        self._init_marker_images()

        self._build_toolbar()
        self._build_map()
        self._build_status_bar()

        data_csv = os.path.join(os.path.dirname(__file__), "data.csv")
        self.file_datasource = FileDatasource(data_csv)
        self.store_datasource = Datasource(user_id)

        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self._start_async_loop, daemon=True).start()

        self.root.after(1000, self.update)

    # -------------------------------------------------------------------------
    # UI construction
    # -------------------------------------------------------------------------

    def _init_marker_images(self):
        pil_images = {
            "car":           make_car(COLORS["car"], size=22),
            "parking_free":  make_circle(COLORS["parking_free"], size=14),
            "parking_busy":  make_circle(COLORS["parking_busy"], size=14),
            "tl_red":        make_diamond(COLORS["tl_red"], size=14),
            "tl_yellow":     make_diamond(COLORS["tl_yellow"], size=14),
            "tl_green":      make_diamond(COLORS["tl_green"], size=14),
            "tl_unknown":    make_diamond(COLORS["tl_unknown"], size=14),
            "pothole":       make_triangle(COLORS["pothole"], size=16),
            "bump":          make_triangle(COLORS["bump"], size=12),
        }
        self.tk_images = {k: ImageTk.PhotoImage(v) for k, v in pil_images.items()}

    def _build_toolbar(self):
        bar = tk.Frame(self.root, bg=self.BG_PANEL, padx=12, pady=10)
        bar.pack(fill="x")

        tk.Label(
            bar, text="Шари:",
            bg=self.BG_PANEL, fg=self.FG_LIGHT,
            font=("Helvetica", 11, "bold"),
        ).pack(side="left", padx=(0, 14))

        for layer_name, label in [
            ("parking",       "🅿  Парковки"),
            ("traffic_light", "🚦 Світлофори"),
            ("events",        "⚠  Дорожні події"),
            ("path",          "─  Маршрут"),
        ]:
            tk.Checkbutton(
                bar, text=label,
                variable=self.layers[layer_name],
                bg=self.BG_PANEL, fg=self.FG_LIGHT,
                selectcolor=self.BG_DARK,
                activebackground=self.BG_PANEL, activeforeground=self.FG_LIGHT,
                font=("Helvetica", 10),
                command=lambda l=layer_name: self._on_layer_toggled(l),
                borderwidth=0, highlightthickness=0,
            ).pack(side="left", padx=8)

        tk.Button(
            bar, text="Очистити мапу",
            command=self._reset_all,
            bg="#475569", fg="white",
            activebackground="#64748b", activeforeground="white",
            font=("Helvetica", 10),
            relief="flat", padx=12, pady=2,
            borderwidth=0, highlightthickness=0,
        ).pack(side="left", padx=(20, 0))

        self.stats_var = tk.StringVar(value="")
        tk.Label(
            bar, textvariable=self.stats_var,
            bg=self.BG_PANEL, fg=self.FG_MUTED,
            font=("Helvetica", 10, "italic"),
        ).pack(side="right")

    def _build_map(self):
        self.map_widget = tkintermapview.TkinterMapView(
            self.root, width=1200, height=720, corner_radius=0,
        )
        self.map_widget.pack(fill="both", expand=True)
        self.map_widget.set_position(50.4501, 30.5234)
        self.map_widget.set_zoom(15)

    def _build_status_bar(self):
        self.status_var = tk.StringVar(value="Initializing...")
        self.status_label = tk.Label(
            self.root, textvariable=self.status_var,
            bg=self.BG_DARK, fg=self.FG_LIGHT,
            anchor="w", padx=12, pady=8,
            font=("Helvetica", 10),
        )
        self.status_label.pack(side="bottom", fill="x")

    # -------------------------------------------------------------------------
    # Async/event handling
    # -------------------------------------------------------------------------

    def _start_async_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self.store_datasource.connect_to_server())
        self.loop.run_forever()

    def _on_layer_toggled(self, layer_name):
        if self.layers[layer_name].get():
            return

        if layer_name == "parking":
            for m in self.active_parkings.values():
                m.delete()
            self.active_parkings.clear()
        elif layer_name == "traffic_light":
            for m in self.active_traffic_lights.values():
                m.delete()
            self.active_traffic_lights.clear()
        elif layer_name == "events":
            for m in self.event_markers:
                m.delete()
            self.event_markers.clear()
            self.event_positions.clear()
        elif layer_name == "path":
            if self.file_path_line:
                self.file_path_line.delete()
                self.file_path_line = None
            if self.store_path_line:
                self.store_path_line.delete()
                self.store_path_line = None

    def _reset_all(self):
        for m in self.active_parkings.values():
            m.delete()
        self.active_parkings.clear()
        for m in self.active_traffic_lights.values():
            m.delete()
        self.active_traffic_lights.clear()
        for m in self.event_markers:
            m.delete()
        self.event_markers.clear()
        self.event_positions.clear()
        if self.file_path_line:
            self.file_path_line.delete()
            self.file_path_line = None
        if self.store_path_line:
            self.store_path_line.delete()
            self.store_path_line = None
        self.path_file.clear()
        self.path_store.clear()

        self._set_sticky_status("Карту очищено")

    def _is_sticky(self) -> bool:
        return time.monotonic() < self._sticky_until

    def _set_default_status(self, msg: str):
        if self._is_sticky():
            return
        self.status_var.set(msg)
        self.status_label.config(fg=self.FG_LIGHT)

    def _set_sticky_status(self, msg: str, duration: float = None):
        duration = duration if duration is not None else self.STICKY_DURATION_S
        self._sticky_until = time.monotonic() + duration
        self.status_var.set(msg)
        self.status_label.config(fg=self.FG_STICKY)  # жовтий → візуальний сигнал

    # -------------------------------------------------------------------------
    # Main loop
    # -------------------------------------------------------------------------

    def update(self):
        self._set_default_status(
            f"WebSocket: {self.store_datasource.connection_status}  •  "
            f"Натисни на маркер для деталей"
        )
        self._update_stats()

        for lat, lon, z in self.file_datasource.get_new_points(batch_size=1):
            road_state = classify_road(z)
            self.handle_road_point(lat, lon, road_state, source="file")

        for item in self.store_datasource.get_new_points(max_points=20):
            sensor_type = item.get("sensor_type", "unknown")
            handler = SENSOR_HANDLERS.get(sensor_type)
            if handler:
                handler(self, item)

        self.root.after(self.UPDATE_INTERVAL_MS, self.update)

    def _update_stats(self):
        self.stats_var.set(
            f"P: {len(self.active_parkings)}  "
            f"TL: {len(self.active_traffic_lights)}  "
            f"Events: {len(self.event_markers)}"
        )

    # -------------------------------------------------------------------------
    # Road handler
    # -------------------------------------------------------------------------

    def handle_road_point(self, lat, lon, road_state, source="store"):
        state = (road_state or "").lower().strip()
        if self.layers["events"].get():
            if state in ("small pits", "bump", "small_pit"):
                self._add_event_marker(lat, lon, "bump", "Невелика яма")
            elif state in ("large pits", "pothole", "large_pit"):
                self._add_event_marker(lat, lon, "pothole", "Велика яма")

        if source == "store":
            self._update_car_marker(lat, lon, focus=True)

        self._add_to_path(lat, lon, source)

    def _update_car_marker(self, lat, lon, focus=True):
        if self.car_marker:
            self.car_marker.set_position(lat, lon)
        else:
            self.car_marker = self.map_widget.set_marker(
                lat, lon,
                icon=self.tk_images["car"],
                command=lambda m: self._set_sticky_status(
                    f"🚗 Машина: ({m.position[0]:.5f}, {m.position[1]:.5f})"
                ),
            )
        if focus and not self._is_sticky():
            self.map_widget.set_position(lat, lon)

    def _add_to_path(self, lat, lon, source):
        if not self.layers["path"].get():
            return
        if source == "file":
            self.path_file.append((lat, lon))
            self.path_file = self.path_file[-self.MAX_PATH_POINTS:]
            if len(self.path_file) > 1:
                if self.file_path_line:
                    self.file_path_line.delete()
                self.file_path_line = self.map_widget.set_path(
                    self.path_file, color=self.PATH_FILE, width=2,
                )
        else:
            self.path_store.append((lat, lon))
            self.path_store = self.path_store[-self.MAX_PATH_POINTS:]
            if len(self.path_store) > 1:
                if self.store_path_line:
                    self.store_path_line.delete()
                self.store_path_line = self.map_widget.set_path(
                    self.path_store, color=self.PATH_STORE, width=3,
                )

    def _add_event_marker(self, lat, lon, kind, label):
        for plat, plon in self.event_positions[-50:]:
            if (abs(plat - lat) < self.EVENT_DEDUP_RADIUS
                    and abs(plon - lon) < self.EVENT_DEDUP_RADIUS):
                return

        marker = self.map_widget.set_marker(
            lat, lon,
            icon=self.tk_images[kind],
            command=lambda m, l=label, lt=lat, ln=lon: self._set_sticky_status(
                f"⚠ {l}: ({lt:.5f}, {ln:.5f})"
            ),
        )
        self.event_markers.append(marker)
        self.event_positions.append((lat, lon))

        if len(self.event_markers) > self.MAX_EVENT_MARKERS:
            self.event_markers.pop(0).delete()
            self.event_positions.pop(0)

    # -------------------------------------------------------------------------
    # Parking & Traffic Light markers
    # -------------------------------------------------------------------------

    def set_parking_marker(self, lat, lon, is_occupied, total_spots, parking_id):
        icon_key = "parking_busy" if is_occupied else "parking_free"
        if parking_id in self.active_parkings:
            self.active_parkings[parking_id].delete()
        marker = self.map_widget.set_marker(
            lat, lon,
            icon=self.tk_images[icon_key],
            command=lambda m, pid=parking_id, occ=is_occupied, ts=total_spots:
                self._set_sticky_status(
                    f"🅿 {pid}: {'ЗАЙНЯТО' if occ else f'Вільно (до {ts} місць)'}"
                ),
        )
        self.active_parkings[parking_id] = marker

    def set_traffic_light_marker(self, lat, lon, state, car_count, light_id):
        icon_key = {
            "red":    "tl_red",
            "yellow": "tl_yellow",
            "green":  "tl_green",
        }.get(state, "tl_unknown")
        if light_id in self.active_traffic_lights:
            self.active_traffic_lights[light_id].delete()
        marker = self.map_widget.set_marker(
            lat, lon,
            icon=self.tk_images[icon_key],
            command=lambda m, lid=light_id, st=state, cc=car_count:
                self._set_sticky_status(
                    f"🚦 {lid}: "
                    f"{ {'red':'ЧЕРВОНИЙ','yellow':'ЖОВТИЙ','green':'ЗЕЛЕНИЙ'}.get(st, st.upper()) }"
                    f"  •  {cc} авто"
                ),
        )
        self.active_traffic_lights[light_id] = marker

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = MapViewApp(user_id=1)
    app.run()