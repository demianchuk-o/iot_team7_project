import tkinter
import tkintermapview
from datasource import Datasource
from file_datasource import FileDatasource
import threading
import asyncio
from PIL import Image, ImageTk
import os


class MapViewApp:
    def __init__(self, user_id: int):
        self.root = tkinter.Tk()
        self.root.geometry(f"{1000}x{750}")
        self.root.title("IoT Road Monitor")
        
        self.car_marker = None
        self.path_file = []
        self.path_store = []

        self.image_path = os.path.join(os.path.dirname(__file__), "images")
        self.pothole_image = Image.open(os.path.join(self.image_path, "pothole.png")).resize((30, 30))
        self.bump_image = Image.open(os.path.join(self.image_path, "bump.png")).resize((30, 30))
        self.car_image = Image.open(os.path.join(self.image_path, "car.png")).resize((40, 40))

        self.map_widget = tkintermapview.TkinterMapView(
            self.root, width=1000, height=700, corner_radius=0
        )
        self.map_widget.pack(fill="both", expand=True)

        # Status Label
        self.status_var = tkinter.StringVar(value="Status: Initializing...")
        self.status_label = tkinter.Label(self.root, textvariable=self.status_var, bd=1, relief=tkinter.SUNKEN, anchor=tkinter.W)
        self.status_label.pack(side=tkinter.BOTTOM, fill=tkinter.X)

        self.map_widget.set_position(50.4501, 30.5234)
        self.map_widget.set_zoom(15)

        data_csv_path = os.path.join(os.path.dirname(__file__), "data.csv")
        self.file_datasource = FileDatasource(data_csv_path)
        self.store_datasource = Datasource(user_id)
        
        # Start background event loop for websockets
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.start_async_loop, daemon=True).start()

        self.root.after(1000, self.update)

    def start_async_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self.store_datasource.connect_to_server())
        self.loop.run_forever()

    def update(self):
        # Update status bar
        status = f"WebSocket: {self.store_datasource.connection_status}"
        self.status_var.set(f"Status: {status}")
        
        # Pull limited points from File (batch_size=5 for smoothness)
        file_points = self.file_datasource.get_new_points(batch_size=5)
        if file_points:
            for lat, lon, road_state in file_points:
                self.handle_point(lat, lon, road_state, source="file", focus=False)
        
        # Pull new points from Store
        store_points = self.store_datasource.get_new_points()
        if store_points:
            for lat, lon, road_state in store_points:
                self.handle_point(lat, lon, road_state, source="store", focus=True)
        
        self.root.after(300, self.update)

    def handle_point(self, lat, lon, road_state, source="store", focus=True):
        state = road_state.lower().strip()
        if state in ["small pits", "bump", "small_pit"]:
            self.set_bump_marker(lat, lon)
        elif state in ["large pits", "pothole", "large_pit"]:
            self.set_pothole_marker(lat, lon)
        
        self.update_car_marker(lat, lon, focus=focus)
        self.add_to_path(lat, lon, source)

    def update_car_marker(self, lat, lon, focus=True):
        if self.car_marker:
            self.car_marker.set_position(lat, lon)
        else:
            self.car_marker = self.map_widget.set_marker(
                lat, lon, icon=ImageTk.PhotoImage(self.car_image)
            )
        if focus:
            self.map_widget.set_position(lat, lon)

    def add_to_path(self, lat, lon, source):
        if source == "file":
            self.path_file.append((lat, lon))
            if len(self.path_file) > 1:
                self.map_widget.set_path(self.path_file, color="gray", width=2)
        else:
            self.path_store.append((lat, lon))
            if len(self.path_store) > 1:
                self.map_widget.set_path(self.path_store, color="blue", width=2)

    def set_pothole_marker(self, lat, lon):
        self.map_widget.set_marker(
            lat, lon, icon=ImageTk.PhotoImage(self.pothole_image)
        )
        self.ensure_car_on_top()

    def set_bump_marker(self, lat, lon):
        self.map_widget.set_marker(
            lat, lon, icon=ImageTk.PhotoImage(self.bump_image)
        )
        self.ensure_car_on_top()

    def ensure_car_on_top(self):
        """Re-creates the car marker so it stays on top of road events."""
        if self.car_marker:
            cur_pos = self.car_marker.position
            self.car_marker.delete()
            self.car_marker = self.map_widget.set_marker(
                cur_pos[0], cur_pos[1], icon=ImageTk.PhotoImage(self.car_image)
            )

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = MapViewApp(user_id=1)
    app.run()
