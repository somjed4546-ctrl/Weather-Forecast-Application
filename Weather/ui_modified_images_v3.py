import os
import tkinter as tk
from tkinter import messagebox
import threading
from datetime import datetime

import requests
from PIL import Image, ImageTk

# ============================================================
# JEDI WEATHER
# Image-enhanced weather dashboard
#
# Keep this Python file in the same folder as these image files:
#   Jedi.png
#   fa043464-42ad-43b4-8e1a-e3f0b83ff6ff.png   (top-right cloud)
#   weather_bg_sun.png
#   weather_bg_cloud.png
#   weather_bg_rain.png
#   weather_bg_storm.png
#   weather_bg_snow.png
#   fa-solid-900.ttf (optional Font Awesome font)
# ============================================================

BG_DARK = "#210635"
BG_PURPLE = "#420D4B"
PURPLE = "#7B337E"
BLUE_PURPLE = "#6667AB"
LIGHT = "#F5D5E0"
WHITE = "#FFFFFF"
MUTED = "#DCC7E5"

FONT_AWESOME = "Font Awesome 7 Free Solid"
FONT_AWESOME_FILE = "fa-solid-900.ttf"

FA = {
    "sun": "\uf185",
    "cloud": "\uf0c2",
    "cloud_sun": "\uf6c4",
    "cloud_rain": "\uf73d",
    "cloud_showers_heavy": "\uf740",
    "cloud_bolt": "\uf76c",
    "umbrella": "\uf0e9",
}

ASSET_FILES = {
    "sun": "weather_bg_sun.png",
    "cloud": "weather_bg_cloud.png",
    "rain": "weather_bg_rain.png",
    "storm": "weather_bg_storm.png",
    "snow": "weather_bg_snow.png",
}
CLOUD_HEADER_FILE = "fa043464-42ad-43b4-8e1a-e3f0b83ff6ff.png"
JEDI_FILE = "Jedi.png"


def find_asset(base_dir, filename):
    """Find an image beside the script or inside common asset folders."""
    candidates = (
        os.path.join(base_dir, filename),
        os.path.join(base_dir, "assets", filename),
        os.path.join(base_dir, "JediWeather_v2_assets", filename),
    )
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return candidates[0]


# ---------------------------- Weather data ----------------------------

def load_font_awesome(root):
    """Use Font Awesome if the font is installed; otherwise use symbol fallback."""
    try:
        if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), FONT_AWESOME_FILE)):
            return FONT_AWESOME
    except Exception:
        pass
    return "Segoe UI Symbol"


def weather_icon(weather_code, font_name):
    """Return the weather icon matching the WMO/Open-Meteo code."""
    if weather_code == 0:
        icon, fallback = FA["sun"], "☀"
    elif weather_code in (1, 2):
        icon, fallback = FA["cloud_sun"], "⛅"
    elif weather_code == 3:
        icon, fallback = FA["cloud"], "☁"
    elif weather_code in (45, 48):
        icon, fallback = FA["cloud"], "≋"
    elif weather_code in (51, 53, 55, 56, 57):
        icon, fallback = FA["cloud_rain"], "🌦"
    elif weather_code in (61, 63, 65, 66, 67, 80, 81, 82):
        icon, fallback = FA["cloud_showers_heavy"], "🌧"
    elif weather_code in (71, 73, 75, 77, 85, 86):
        icon, fallback = "❄", "❄"
    elif weather_code in (95, 96, 99):
        icon, fallback = FA["cloud_bolt"], "⛈"
    else:
        icon, fallback = FA["cloud"], "☁"
    return icon if font_name == FONT_AWESOME else fallback


def weather_text(code):
    names = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Fog", 48: "Depositing rime fog", 51: "Light drizzle",
        53: "Moderate drizzle", 55: "Dense drizzle", 56: "Light freezing drizzle",
        57: "Dense freezing drizzle", 61: "Slight rain", 63: "Moderate rain",
        65: "Heavy rain", 66: "Light freezing rain", 67: "Heavy freezing rain",
        71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
        77: "Snow grains", 80: "Slight rain showers", 81: "Moderate rain showers",
        82: "Violent rain showers", 85: "Slight snow showers",
        86: "Heavy snow showers", 95: "Thunderstorm",
        96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
    }
    return names.get(code, "Unknown")


def geocode_city(city):
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city, "count": 1, "language": "en", "format": "json"}
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    results = response.json().get("results", [])
    return results[0] if results else None


def get_weather(city):
    """Get current weather plus 5-day and hourly forecast."""
    location = geocode_city(city)
    if not location:
        return None

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "current": (
            "temperature_2m,relative_humidity_2m,apparent_temperature,"
            "weather_code,wind_speed_10m"
        ),
        "daily": (
            "weather_code,temperature_2m_max,temperature_2m_min,"
            "precipitation_probability_max,precipitation_sum"
        ),
        "hourly": "precipitation_probability,weather_code,temperature_2m",
        "timezone": "auto",
        "forecast_days": 5,
        "past_days": 0,
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    return {
        "name": location["name"],
        "country": location.get("country", ""),
        "current": data["current"],
        "daily": data["daily"],
        "hourly": data["hourly"],
        "timezone": data.get("timezone", ""),
    }


def weather_background_file(code):
    """Map a forecast code to a supplied illustrated weather background."""
    if code in (0,):
        key = "sun"
    elif code in (1, 2, 3, 45, 48):
        key = "cloud"
    elif code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
        key = "rain"
    elif code in (71, 73, 75, 77, 85, 86):
        key = "snow"
    elif code in (95, 96, 99):
        key = "storm"
    else:
        key = "cloud"
    return ASSET_FILES[key]


class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Jedi Weather")
        self.root.geometry("1080x760")
        self.root.minsize(900, 650)
        self.root.configure(bg=BG_DARK)

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.icon_font = load_font_awesome(root)
        self._photo_refs = []

        # Scrollable application area.
        canvas_frame = tk.Frame(root, bg=BG_DARK)
        canvas_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg=BG_DARK, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.content = tk.Frame(self.canvas, bg=BG_DARK)
        self.window_id = self.canvas.create_window(0, 0, anchor="nw", window=self.content)
        self.content.bind("<Configure>", self.update_scrollregion)
        self.canvas.bind("<Configure>", self.on_resize)
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind_all("<Button-4>", self.on_mousewheel_linux)
        self.canvas.bind_all("<Button-5>", self.on_mousewheel_linux)

        self.build_ui()

    # ---------------------------- Image helpers ----------------------------

    def asset_path(self, filename):
        return find_asset(self.base_dir, filename)

    def load_image(self, filename, max_width, max_height, contain=True):
        """Load an RGBA PNG and resize it without stretching."""
        path = self.asset_path(filename)
        if not os.path.exists(path) or max_width < 2 or max_height < 2:
            return None
        try:
            image = Image.open(path).convert("RGBA")
            ratio = min(max_width / image.width, max_height / image.height)
            size = (
                max(1, int(image.width * ratio)),
                max(1, int(image.height * ratio)),
            )
            image = image.resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(image)
        except Exception:
            return None

    def refresh_weather_art(self, card):
        """Put the forecast illustration visibly on the RIGHT side of a weather box."""
        canvas = card.weather_canvas
        width = max(canvas.winfo_width(), 400)
        height = max(canvas.winfo_height(), 260)
        photo = self.load_image(card.weather_background, int(width * 0.55), int(height * 0.92))

        canvas.delete("weather_art")
        if photo:
            canvas.create_image(
                width - 8,
                height / 2,
                anchor="e",
                image=photo,
                tags="weather_art",
            )
            canvas.tag_lower("weather_art")
            card._weather_photo = photo
        else:
            card._weather_photo = None

        # Keep text above the artwork.
        for item in card.weather_items.values():
            canvas.tag_raise(item)

    # ---------------------------- Scroll helpers ----------------------------

    def update_scrollregion(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_resize(self, event):
        self.canvas.itemconfig(self.window_id, width=event.width)
        self.update_scrollregion()

    def on_mousewheel(self, event):
        if event.delta:
            self.canvas.yview_scroll(int(-event.delta / 120), "units")

    def on_mousewheel_linux(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-3, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(3, "units")

    # ---------------------------- UI ----------------------------

    def build_ui(self):
        header = tk.Frame(self.content, bg=BG_DARK, height=125)
        header.pack(fill="x", padx=40, pady=(15, 5))
        header.pack_propagate(False)

        # Center title.
        tk.Label(
            header, text="Jedi Weather", font=("Georgia", 30),
            fg=LIGHT, bg=BG_DARK
        ).place(relx=0.5, rely=0.28, anchor="center")

        tk.Label(
            header, text="WEATHER • OPTIONAL ALTERNATIVE",
            font=("Arial", 9, "bold"), fg=MUTED, bg=BG_DARK
        ).place(relx=0.5, rely=0.60, anchor="center")

        # Supplied cloud image in the top-right corner.
        self.cloud_label = tk.Label(header, bg=BG_DARK, bd=0)
        self.cloud_label.place(relx=1.0, rely=0.0, anchor="ne")
        self.root.after_idle(self.load_header_cloud)

        search = tk.Frame(self.content, bg=PURPLE, highlightthickness=0)
        search.pack(fill="x", padx=40, pady=10)

        tk.Label(search, text="CITY", font=("Arial", 9, "bold"), fg=LIGHT, bg=PURPLE).grid(
            row=0, column=0, padx=(20, 8), pady=(16, 4), sticky="w"
        )

        self.city_entry = tk.Entry(
            search, font=("Arial", 12), width=30,
            bg="#F7EEF8", fg=BG_DARK, relief="flat"
        )
        self.city_entry.grid(row=1, column=0, padx=(20, 8), pady=(0, 18), ipady=8)
        self.city_entry.insert(0, "Bangkok")

        self.search_button = tk.Button(
            search, text="  CHECK WEATHER  ", command=self.start_weather_fetch,
            font=("Arial", 10, "bold"), bg=LIGHT, fg=BG_DARK,
            activebackground=WHITE, activeforeground=BG_DARK,
            relief="flat", cursor="hand2"
        )
        self.search_button.grid(row=1, column=1, padx=8, pady=(0, 18), ipady=7)

        self.alternative_button = tk.Button(
            search, text="  + ALTERNATIVE  ", command=self.toggle_alternative,
            font=("Arial", 10, "bold"), bg=BG_DARK, fg=LIGHT,
            activebackground=BG_PURPLE, activeforeground=WHITE,
            relief="flat", cursor="hand2"
        )
        self.alternative_button.grid(row=1, column=2, padx=(8, 20), pady=(0, 18), ipady=7)

        self.alternative_frame = tk.Frame(search, bg=PURPLE)
        self.alternative_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=20, pady=(0, 16))
        self.alternative_frame.grid_remove()

        tk.Label(
            self.alternative_frame, text="ALTERNATIVE CITY (OPTIONAL)",
            font=("Arial", 9, "bold"), fg=LIGHT, bg=PURPLE
        ).pack(side="left", padx=(0, 8))

        self.compare_entry = tk.Entry(
            self.alternative_frame, font=("Arial", 12), width=25,
            bg="#F7EEF8", fg=BG_DARK, relief="flat"
        )
        self.compare_entry.pack(side="left", ipady=7)

        self.alternative_check_button = tk.Button(
            self.alternative_frame, text="COMPARE", command=self.start_weather_fetch,
            font=("Arial", 9, "bold"), bg=LIGHT, fg=BG_DARK,
            activebackground=WHITE, activeforeground=BG_DARK,
            relief="flat", cursor="hand2"
        )
        self.alternative_check_button.pack(side="left", padx=8, ipady=5)

        search.grid_columnconfigure(0, weight=1)

        self.status = tk.Label(
            self.content,
            text="Enter one city to see its forecast. Use + ALTERNATIVE only if you want to compare another city.",
            font=("Arial", 10), fg=MUTED, bg=BG_DARK
        )
        self.status.pack(pady=(4, 8))

        # Current weather cards.
        self.cards_frame = tk.Frame(self.content, bg=BG_DARK)
        self.cards_frame.pack(fill="x", padx=40)
        self.main_card = self.make_weather_card(self.cards_frame)
        self.compare_card = self.make_weather_card(self.cards_frame)
        self.main_card.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.compare_card.grid_remove()
        self.cards_frame.grid_columnconfigure(0, weight=1)
        self.cards_frame.grid_columnconfigure(1, weight=1)

        tk.Label(
            self.content, text="5-DAY FORECAST", font=("Arial", 12, "bold"),
            fg=LIGHT, bg=BG_DARK
        ).pack(pady=(12, 8))

        self.forecast_frame = tk.Frame(self.content, bg=BG_DARK)
        self.forecast_frame.pack(fill="x", padx=40, pady=(0, 10))
        self.forecast_labels = []
        self.build_forecast_cards()

        self.rain_result = tk.Label(
            self.content, text="", font=("Arial", 13, "bold"), fg=LIGHT, bg=BG_DARK
        )
        self.rain_result.pack(pady=(0, 8))

        self.rain_time_result = tk.Label(
            self.content, text="Rainy time: --", font=("Arial", 10), fg=MUTED,
            bg=BG_DARK, justify="center"
        )
        self.rain_time_result.pack(pady=(0, 8))

        self.sleep_rain_result = tk.Label(
            self.content, text="Rainy sleep window: --", font=("Arial", 11, "bold"),
            fg=LIGHT, bg=BG_DARK, justify="center"
        )
        self.sleep_rain_result.pack(pady=(0, 12))

        # Bottom advice box: one heading, one advice text, supplied Jedi cartoon.
        advice_frame = tk.Frame(self.content, bg=PURPLE, padx=18, pady=10)
        advice_frame.pack(fill="x", padx=40, pady=(0, 25))

        advice_frame.grid_columnconfigure(0, weight=1)
        advice_frame.grid_columnconfigure(1, weight=0)

        tk.Label(
            advice_frame, text="*  JEDI WEATHER ADVICE  *",
            font=("Arial", 11, "bold"), fg=LIGHT, bg=PURPLE
        ).grid(row=0, column=0, sticky="n", pady=(0, 4))

        self.jedi_advice = tk.Label(
            advice_frame, text='* "Check the forecast, young Jedi." *',
            font=("Georgia", 12, "italic"), fg=LIGHT, bg=PURPLE,
            justify="center", wraplength=700, padx=12, pady=4
        )
        self.jedi_advice.grid(row=1, column=0, sticky="ew")

        self.jedi_image_label = tk.Label(advice_frame, bg=PURPLE, bd=0)
        self.jedi_image_label.grid(row=0, column=1, rowspan=2, padx=(12, 4))
        self.root.after_idle(self.load_jedi_image)

        self.root.after_idle(self.update_scrollregion)

    def load_header_cloud(self):
        photo = self.load_image(CLOUD_HEADER_FILE, 240, 115)
        if photo:
            self.cloud_label.config(image=photo)
            self.cloud_label.image = photo

    def load_jedi_image(self):
        path = self.asset_path(JEDI_FILE)
        if not os.path.exists(path):
            return
        try:
            image = Image.open(path).convert("RGBA")
            image.thumbnail((125, 125), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            self.jedi_image_label.config(image=photo)
            self.jedi_image_label.image = photo
        except Exception:
            pass

    def make_weather_card(self, parent):
        card = tk.Frame(parent, bg=BG_PURPLE, padx=0, pady=0, height=275)
        card.grid_propagate(False)

        canvas = tk.Canvas(card, bg=LIGHT, highlightthickness=0, bd=0)
        canvas.pack(fill="both", expand=True)
        card.weather_canvas = canvas
        card.weather_background = ASSET_FILES["cloud"]
        card.weather_code = None
        card._weather_photo = None
        card.weather_items = {
            "city": canvas.create_text(0, 30, text="CITY", font=("Georgia", 19), fill=BG_DARK),
            "country": canvas.create_text(0, 57, text="", font=("Arial", 9), fill=BG_DARK),
            "icon": canvas.create_text(0, 104, text="☁", font=(self.icon_font, 34), fill=BG_DARK),
            "temp": canvas.create_text(0, 145, text="--°C", font=("Arial", 28, "bold"), fill=BG_DARK),
            "condition": canvas.create_text(0, 177, text="Waiting for weather...", font=("Arial", 10), fill=BG_DARK),
            "details": canvas.create_text(0, 204, text="Humidity --%   •   Wind -- km/h", font=("Arial", 9), fill=BG_DARK),
            "rain": canvas.create_text(0, 232, text="Today's rain chance: --%", font=("Arial", 10, "bold"), fill=BG_DARK),
        }
        canvas.bind("<Configure>", lambda event, c=card: self.layout_weather_card(c))
        return card

    def layout_weather_card(self, card):
        canvas = card.weather_canvas
        width = max(canvas.winfo_width(), 400)
        height = max(canvas.winfo_height(), 260)
        x = int(width * 0.30)  # Text sits in the open/light portion of the artwork.
        items = card.weather_items
        canvas.coords(items["city"], x, int(height * 0.12))
        canvas.coords(items["country"], x, int(height * 0.22))
        canvas.coords(items["icon"], x, int(height * 0.38))
        canvas.coords(items["temp"], x, int(height * 0.54))
        canvas.coords(items["condition"], x, int(height * 0.66))
        canvas.coords(items["details"], x, int(height * 0.77))
        canvas.coords(items["rain"], x, int(height * 0.88))
        self.refresh_weather_art(card)

    def set_card(self, card, data):
        current = data["current"]
        daily = data["daily"]
        code = current["weather_code"]
        rain_probability = daily["precipitation_probability_max"][0] or 0
        items = card.weather_items

        canvas = card.weather_canvas
        canvas.itemconfig(items["city"], text=data["name"].upper())
        canvas.itemconfig(items["country"], text=data["country"])
        canvas.itemconfig(items["icon"], text=weather_icon(code, self.icon_font))
        canvas.itemconfig(items["temp"], text=f'{current["temperature_2m"]:.0f}°C')
        canvas.itemconfig(items["condition"], text=weather_text(code))
        canvas.itemconfig(
            items["details"],
            text=(
                f'Humidity {current["relative_humidity_2m"]:.0f}%'
                f'   •   Wind {current["wind_speed_10m"]:.0f} km/h'
            )
        )
        canvas.itemconfig(items["rain"], text=f"Today's rain chance: {rain_probability:.0f}%")

        card.weather_code = code
        card.weather_background = weather_background_file(code)
        self.layout_weather_card(card)

    def build_forecast_cards(self):
        for i in range(5):
            frame = tk.Frame(self.forecast_frame, bg=LIGHT, height=205)
            frame.grid(row=0, column=i, padx=4, sticky="nsew")
            frame.grid_propagate(False)
            self.forecast_frame.grid_columnconfigure(i, weight=1, uniform="forecast")

            canvas = tk.Canvas(frame, bg=LIGHT, highlightthickness=0, bd=0)
            canvas.pack(fill="both", expand=True)

            labels = {
                "canvas": canvas,
                "background_art": None,
                "date": canvas.create_text(0, 22, text="--", font=("Arial", 9, "bold"), fill=BG_DARK),
                "icon1": canvas.create_text(0, 60, text="☁", font=(self.icon_font, 18), fill=BG_DARK),
                "temp1": canvas.create_text(0, 92, text="--° / --°", font=("Arial", 8), fill=BG_DARK),
                "rain1": canvas.create_text(0, 112, text="--% rain", font=("Arial", 8), fill=BG_DARK),
                "icon2": canvas.create_text(0, 144, text="", font=(self.icon_font, 15), fill=BG_DARK, state="hidden"),
                "temp2": canvas.create_text(0, 165, text="", font=("Arial", 8), fill=BG_DARK, state="hidden"),
                "rain2": canvas.create_text(0, 184, text="", font=("Arial", 8), fill=BG_DARK, state="hidden"),
            }
            labels["background"] = ASSET_FILES["cloud"]
            canvas.bind("<Configure>", lambda event, item=labels: self.layout_forecast_card(item))
            self.forecast_labels.append(labels)

    def layout_forecast_card(self, labels):
        canvas = labels["canvas"]
        width = max(canvas.winfo_width(), 150)
        height = max(canvas.winfo_height(), 190)
        x = int(width * 0.32)
        c = canvas
        c.coords(labels["date"], x, height * 0.11)
        c.coords(labels["icon1"], x, height * 0.30)
        c.coords(labels["temp1"], x, height * 0.47)
        c.coords(labels["rain1"], x, height * 0.57)
        c.coords(labels["icon2"], x, height * 0.72)
        c.coords(labels["temp2"], x, height * 0.82)
        c.coords(labels["rain2"], x, height * 0.92)
        # Show the day's weather illustration prominently on the right side.
        c.delete("weather_art")
        photo = self.load_image(labels["background"], int(width * 0.62), int(height * 0.90))
        if photo:
            c.create_image(width - 4, height / 2, anchor="e", image=photo, tags="weather_art")
            c.tag_lower("weather_art")
            labels["photo"] = photo
        else:
            labels["photo"] = None
        # Keep forecast text above the artwork.
        for key in ("date", "icon1", "temp1", "rain1", "icon2", "temp2", "rain2"):
            c.tag_raise(labels[key])

    # ---------------------------- Search / comparison ----------------------------

    def toggle_alternative(self):
        if self.alternative_frame.winfo_ismapped():
            self.alternative_frame.grid_remove()
            self.compare_card.grid_remove()
            self.main_card.grid_configure(column=0, columnspan=2, padx=0)
            self.alternative_button.config(text="  + ALTERNATIVE  ")
            self.status.config(text="Alternative comparison is off. Enter one city to view its forecast.")
            self.update_forecast_heading(False)
        else:
            self.alternative_frame.grid()
            self.compare_card.grid_remove()
            self.main_card.grid_configure(column=0, columnspan=2, padx=0)
            self.alternative_button.config(text="  − ALTERNATIVE  ")
            self.status.config(text="Optional: enter another city if you want to compare it.")

    def update_forecast_heading(self, comparing=False):
        for widget in self.content.winfo_children():
            if isinstance(widget, tk.Label) and widget.cget("text") in (
                "5-DAY FORECAST", "5-DAY FORECAST • ALTERNATIVE"
            ):
                widget.config(text="5-DAY FORECAST • ALTERNATIVE" if comparing else "5-DAY FORECAST")
                break

    def start_weather_fetch(self):
        city = self.city_entry.get().strip()
        compare = self.compare_entry.get().strip() if self.alternative_frame.winfo_ismapped() else ""
        if not city:
            messagebox.showwarning("Input Error", "Please enter a city name.")
            return
        if compare and compare.lower() == city.lower():
            messagebox.showwarning("Input Error", "The alternative city should be different from the main city.")
            return

        self.search_button.config(state="disabled")
        self.alternative_check_button.config(state="disabled")
        self.status.config(text="Fetching weather and forecast...")
        self.rain_result.config(text="")
        self.rain_time_result.config(text="Rainy time: --")
        self.sleep_rain_result.config(text="Rainy sleep window: --")
        self.jedi_advice.config(text='* "Reading the skies, young Jedi..." *')

        threading.Thread(target=self.fetch_weather, args=(city, compare), daemon=True).start()

    def fetch_weather(self, city, compare=""):
        try:
            main_data = get_weather(city)
            if not main_data:
                raise ValueError(f"Could not find city: {city}")

            compare_data = None
            if compare:
                compare_data = get_weather(compare)
                if not compare_data:
                    raise ValueError(f"Could not find alternative city: {compare}")

            self.root.after(0, lambda: self.update_ui(main_data, compare_data))
        except Exception as exc:
            self.root.after(0, lambda: self.show_error(str(exc)))

    def update_ui(self, main_data, compare_data=None):
        self.set_card(self.main_card, main_data)

        if compare_data:
            self.set_card(self.compare_card, compare_data)
            self.main_card.grid_configure(column=0, columnspan=1, padx=(0, 8))
            self.compare_card.grid(row=0, column=1, padx=(8, 0), sticky="nsew")
            self.update_forecast_heading(True)
        else:
            self.compare_card.grid_remove()
            self.main_card.grid_configure(column=0, columnspan=2, padx=0)
            self.update_forecast_heading(False)

        main_daily = main_data["daily"]
        compare_daily = compare_data["daily"] if compare_data else None

        for i, labels in enumerate(self.forecast_labels):
            dt = datetime.strptime(main_daily["time"][i], "%Y-%m-%d")
            canvas = labels["canvas"]
            labels["background"] = weather_background_file(main_daily["weather_code"][i])
            canvas.itemconfig(labels["date"], text=dt.strftime("%a\n%d %b"))
            canvas.itemconfig(labels["icon1"], text=weather_icon(main_daily["weather_code"][i], self.icon_font))
            canvas.itemconfig(
                labels["temp1"],
                text=(
                    f'{main_data["name"][:10]}: '
                    f'{main_daily["temperature_2m_max"][i]:.0f}° / '
                    f'{main_daily["temperature_2m_min"][i]:.0f}°'
                )
            )
            canvas.itemconfig(
                labels["rain1"],
                text=f'{main_daily["precipitation_probability_max"][i] or 0:.0f}% rain'
            )

            if compare_data:
                canvas.itemconfig(labels["icon2"], state="normal", text=weather_icon(compare_daily["weather_code"][i], self.icon_font))
                canvas.itemconfig(labels["temp2"], state="normal", text=(
                    f'{compare_data["name"][:10]}: '
                    f'{compare_daily["temperature_2m_max"][i]:.0f}° / '
                    f'{compare_daily["temperature_2m_min"][i]:.0f}°'
                ))
                canvas.itemconfig(labels["rain2"], state="normal", text=f'{compare_daily["precipitation_probability_max"][i] or 0:.0f}% rain')
            else:
                canvas.itemconfig(labels["icon2"], state="hidden")
                canvas.itemconfig(labels["temp2"], state="hidden")
                canvas.itemconfig(labels["rain2"], state="hidden")
            self.layout_forecast_card(labels)

        p1 = main_daily["precipitation_probability_max"][0] or 0
        rain1 = self.rain_message(main_data["name"], p1)
        self.rain_result.config(text=rain1)

        if compare_data:
            p2 = compare_daily["precipitation_probability_max"][0] or 0
            self.rain_result.config(text=f"{rain1}    •    {self.rain_message(compare_data['name'], p2)}")
            self.update_rain_times(main_data, compare_data)
            self.update_sleep_rain_window(main_data, compare_data)
            self.update_jedi_advice(main_data, compare_data)
            self.status.config(text=f'Showing {main_data["name"]} with alternative: {compare_data["name"]}')
        else:
            self.update_rain_times(main_data)
            self.update_sleep_rain_window(main_data)
            self.update_jedi_advice(main_data)
            self.status.config(text=f'Forecast for {main_data["name"]}. Use + ALTERNATIVE if you want to compare another city.')

        self.search_button.config(state="normal")
        self.alternative_check_button.config(state="normal")
        self.root.after_idle(self.update_scrollregion)

    # ---------------------------- Rain / sleep / advice ----------------------------

    @staticmethod
    def rain_message(city, probability):
        if probability >= 50:
            return f"🌧 {city}: Rain is likely today ({probability:.0f}%)"
        return f"☀ {city}: Rain is not expected today ({probability:.0f}%)"

    @staticmethod
    def rainy_hours(data):
        hourly = data["hourly"]
        today = data["daily"]["time"][0]
        tomorrow = data["daily"]["time"][1]
        rainy_today = []
        rainy_night = []

        for time_str, probability in zip(hourly["time"], hourly["precipitation_probability"]):
            probability = probability or 0
            date_part = time_str[:10]
            hour = int(time_str[11:13])
            if probability < 50:
                continue
            label = datetime.strptime(time_str, "%Y-%m-%dT%H:%M").strftime("%H:%M")
            if date_part == today:
                rainy_today.append(label)
                if hour >= 18:
                    rainy_night.append(label)
            elif date_part == tomorrow and hour < 7:
                rainy_night.append(label)
        return rainy_today, rainy_night

    @staticmethod
    def rainy_sleep_window(data, threshold=50):
        hourly = data["hourly"]
        rainy = []
        for time_str, probability in zip(hourly["time"], hourly["precipitation_probability"]):
            probability = probability or 0
            hour = int(time_str[11:13])
            if (hour >= 20 or hour < 7) and probability >= threshold:
                rainy.append(datetime.strptime(time_str, "%Y-%m-%dT%H:%M"))
        if not rainy:
            return None

        periods = []
        start = prev = rainy[0]
        for current in rainy[1:]:
            if (current - prev).total_seconds() <= 3600:
                prev = current
            else:
                periods.append((start, prev))
                start = prev = current
        periods.append((start, prev))
        best_start, best_end = max(periods, key=lambda p: (p[1] - p[0]).total_seconds())

        end_time = best_end.hour + 1
        end_label = "00:00" if end_time >= 24 else f"{end_time:02d}:00"
        hours = len([dt for dt in rainy if best_start <= dt <= best_end])
        return best_start.strftime("%H:%M"), end_label, hours

    def update_sleep_rain_window(self, main_data, compare_data=None):
        def format_window(data):
            result = self.rainy_sleep_window(data)
            if not result:
                return f'{data["name"]}: No rainy sleep window forecast (20:00–07:00).'
            start, end, hours = result
            return f'{data["name"]}: Rainy sleep window → {start}–{end} ({hours} forecast hour{"s" if hours != 1 else ""})'

        text = format_window(main_data)
        if compare_data:
            text += "\n" + format_window(compare_data)
        self.sleep_rain_result.config(text=text)

    @staticmethod
    def jedi_advice_for_rain(city, probability):
        if probability >= 70:
            return f'{city}:\n"The clouds gather.\nCarry your umbrella, young Jedi."'
        if probability >= 50:
            return f'{city}:\n"The Force senses rain nearby.\nAn umbrella, you should carry."'
        if probability >= 30:
            return f'{city}:\n"Clouds may gather, young Jedi.\nKeep an eye on the sky."'
        return f'{city}:\n"The skies are calm.\nYour umbrella may rest today."'

    def update_jedi_advice(self, main_data, compare_data=None):
        p1 = main_data["daily"]["precipitation_probability_max"][0] or 0
        advice = self.jedi_advice_for_rain(main_data["name"], p1)
        if compare_data:
            p2 = compare_data["daily"]["precipitation_probability_max"][0] or 0
            advice += "\n\n" + self.jedi_advice_for_rain(compare_data["name"], p2)
        self.jedi_advice.config(text="* " + advice + " *")

    def update_rain_times(self, main_data, compare_data=None):
        city1_today, city1_night = self.rainy_hours(main_data)

        def fmt(city, today_hours, night_hours):
            rainy_text = ", ".join(today_hours) if today_hours else "No likely rainy hours"
            if night_hours:
                night_text = ", ".join(night_hours)
                sleep_text = "Rain may be present during the sleep window."
            else:
                night_text = "No likely rain from 18:00–07:00"
                sleep_text = "Dry night forecast — suitable for a quiet sleep."
            return (
                f"{city}: Rainy time → {rainy_text}\n"
                f"Bedtime / night (18:00–07:00) → {night_text}\n"
                f"{sleep_text}"
            )

        result = fmt(main_data["name"], city1_today, city1_night)
        if compare_data:
            city2_today, city2_night = self.rainy_hours(compare_data)
            result += "\n\n" + fmt(compare_data["name"], city2_today, city2_night)
        self.rain_time_result.config(text=result)

    def show_error(self, error):
        self.search_button.config(state="normal")
        self.alternative_check_button.config(state="normal")
        self.status.config(text="Unable to fetch weather.")
        messagebox.showerror("Weather Error", f"{error}\n\nCheck your internet connection and image files.")


if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherApp(root)
    root.mainloop()
