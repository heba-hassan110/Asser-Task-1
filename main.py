import json
import os
from dataclasses import dataclass
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
import tkinter as tk
from tkinter import font
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen


API_URL = "https://api.weatherapi.com/v1/current.json"
ENV_FILE = Path(__file__).with_name(".env")
BACKGROUND = "#0d1928"
PANEL = "#16283c"
SURFACE = "#1e344b"
TEXT = "#f4f8ff"
MUTED = "#acbfd4"
ACCENT = "#9fe8dd"


@dataclass(frozen=True)
class Weather:
    city: str
    country: str
    temperature: float
    condition: str
    feels_like: float
    humidity: int
    wind: float
    updated: str

    @classmethod
    def from_json(cls, data):
        location = data["location"]
        current = data["current"]
        return cls(
            city=location["name"],
            country=location["country"],
            temperature=current["temp_c"],
            condition=current["condition"]["text"],
            feels_like=current["feelslike_c"],
            humidity=current["humidity"],
            wind=current["wind_kph"],
            updated=current["last_updated"],
        )

    def summary(self):
        return (
            f"{self.city}, {self.country}\n"
            f"Conditions:    {self.condition}\n"
            f"Temperature:   {self.temperature:g} °C\n"
            f"Feels like:    {self.feels_like:g} °C\n"
            f"Humidity:      {self.humidity}%\n"
            f"Wind:          {self.wind:g} km/h\n"
            f"Updated:       {self.updated} (local time)"
        )


class WeatherError(Exception):
    pass


def load_api_key():
    # Read the project's single .env setting, with precedence for the shell.
    if not os.getenv("WEATHER_API_KEY", "").strip() and ENV_FILE.is_file():
        try:
            for line in ENV_FILE.read_text(encoding="utf-8-sig").splitlines():
                name, _, value = line.partition("=")
                if name.strip() == "WEATHER_API_KEY":
                    os.environ["WEATHER_API_KEY"] = value.strip().strip("\"'")
                    break
        except (OSError, UnicodeError):
            raise WeatherError("Could not read the .env file. Save it as UTF-8.") from None

    key = os.getenv("WEATHER_API_KEY", "").strip()
    if not key:
        raise WeatherError("Add your WeatherAPI key to .env as WEATHER_API_KEY.")
    return key


def fetch_weather(city):
    query = urlencode({"key": load_api_key(), "q": city})
    try:
        with urlopen(f"{API_URL}?{query}", timeout=10) as response:
            return Weather.from_json(json.load(response))
    except HTTPError as error:
        with error:
            try:
                code = json.load(error)["error"]["code"]
            except (OSError, ValueError, KeyError, TypeError):
                code = None
        messages = {
            1006: "City not found. Try a city and country, such as Cairo, Egypt.",
            2006: "The WeatherAPI key is invalid. Check the value in .env.",
            2007: "Your WeatherAPI account has reached its monthly limit.",
            2008: "Your WeatherAPI key is disabled. Check your account.",
        }
        raise WeatherError(messages.get(code, f"WeatherAPI returned HTTP {error.code}.")) from None
    except OSError:
        raise WeatherError("Could not reach WeatherAPI. Check your connection and try again.") from None
    except (ValueError, KeyError, TypeError, AttributeError):
        raise WeatherError("WeatherAPI returned an unexpected response.") from None


class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.results = Queue()
        self.font_family = "Inter" if "Inter" in font.families(root) else "Segoe UI"
        root.title("Current Weather")
        root.geometry("640x548")
        root.minsize(520, 548)
        root.configure(bg=BACKGROUND)

        content = tk.Frame(root, bg=BACKGROUND)
        content.pack(fill="both", expand=True, padx=30, pady=22)
        self.label(content, "Current weather", size=27, bold=True).pack(anchor="w")
        self.label(content, "City", color=MUTED).pack(anchor="w", pady=(12, 6))

        search = tk.Frame(content, bg=BACKGROUND)
        search.pack(fill="x")
        self.city = tk.StringVar(value="Cairo")
        entry = tk.Entry(
            search, textvariable=self.city, font=(self.font_family, 13),
            bg=SURFACE, fg=TEXT, insertbackground=TEXT, relief="flat",
            highlightthickness=1, highlightbackground=SURFACE, highlightcolor=ACCENT,
        )
        entry.pack(side="left", fill="x", expand=True, ipady=8)
        self.button = tk.Button(
            search, text="Get weather", command=self.search, font=(self.font_family, 11, "bold"),
            bg=ACCENT, fg=BACKGROUND, activebackground="#bcf4eb", activeforeground=BACKGROUND,
            disabledforeground="#315b61", relief="flat", padx=16, cursor="hand2",
        )
        self.button.pack(side="left", fill="y", padx=(10, 0))
        root.bind("<Return>", self.search)
        entry.focus_set()

        self.status = self.label(content, "Enter a city to look up its current conditions.", color=MUTED)
        self.status.pack(anchor="w", pady=(8, 12))

        card = tk.Frame(content, bg=PANEL, padx=18, pady=12)
        card.pack(fill="x")
        self.location = self.label(card, "Location", size=16, bold=True, bg=PANEL)
        self.location.pack(anchor="w")
        self.temperature = self.label(card, "— °C", size=42, bold=True, bg=PANEL, color=ACCENT)
        self.temperature.pack(anchor="w")
        self.condition = self.label(card, "—", size=13, bg=PANEL)
        self.condition.pack(anchor="w", pady=(0, 12))

        metrics = tk.Frame(card, bg=PANEL)
        metrics.pack(fill="x")
        self.metric_values = []
        for column, title in enumerate(("Feels like", "Humidity", "Wind")):
            metrics.columnconfigure(column, weight=1, uniform="metrics")
            tile = tk.Frame(metrics, bg=SURFACE, padx=8, pady=6)
            tile.grid(row=0, column=column, sticky="ew", padx=(0, 8 if column < 2 else 0))
            self.label(tile, title, bg=SURFACE, color=MUTED).pack(anchor="w")
            value = self.label(tile, "—", size=15, bold=True, bg=SURFACE)
            value.pack(anchor="w")
            self.metric_values.append(value)

        self.updated = self.label(card, "", bg=PANEL, color=MUTED)
        self.updated.pack(anchor="w", pady=(10, 0))
        self.label(content, "Data from WeatherAPI.com", color=MUTED).pack(anchor="w", pady=(9, 0))

    def label(self, parent, text, size=10, bold=False, bg=BACKGROUND, color=TEXT):
        return tk.Label(
            parent, text=text, font=(self.font_family, size, "bold" if bold else "normal"),
            bg=bg, fg=color, anchor="w", padx=0,
        )

    def search(self, event=None):
        if self.button["state"] == "disabled":
            return
        city = self.city.get().strip()
        if not city:
            self.status.configure(text="Enter a city name.", fg="#ffb8ae")
            return
        self.button.configure(state="disabled")
        self.status.configure(text="Loading current weather…", fg=MUTED)
        Thread(target=self.lookup, args=(city,), daemon=True).start()
        self.root.after(60, self.show_result)

    def lookup(self, city):
        try:
            self.results.put(fetch_weather(city))
        except WeatherError as error:
            self.results.put(error)

    def show_result(self):
        try:
            result = self.results.get_nowait()
        except Empty:
            self.root.after(60, self.show_result)
            return
        self.button.configure(state="normal")
        if isinstance(result, WeatherError):
            self.status.configure(text=str(result), fg="#ffb8ae")
            return

        self.status.configure(text="Current conditions loaded.", fg=MUTED)
        self.location.configure(text=f"{result.city}, {result.country}")
        self.temperature.configure(text=f"{result.temperature:g} °C")
        self.condition.configure(text=result.condition)
        values = (f"{result.feels_like:g} °C", f"{result.humidity}%", f"{result.wind:g} km/h")
        for label, value in zip(self.metric_values, values):
            label.configure(text=value)
        self.updated.configure(text=f"Updated {result.updated} (local time)")
        print(f"\n{result.summary()}", flush=True)


if __name__ == "__main__":
    window = tk.Tk()
    WeatherApp(window)
    window.mainloop()
