# Lab 1 Python Task

This desktop app looks up current weather by city using the WeatherAPI.com REST API. `main.py` reads the JSON response into a `Weather` class, updates the Tkinter window, and prints a formatted summary in the terminal.

## Set up and run on Windows

1. Open this project folder in VS Code. Use Python 3.11 with Tkinter installed.
2. Get a free API key from [WeatherAPI.com](https://www.weatherapi.com/signup). Open `.env` and paste the key after `WEATHER_API_KEY=`. Keep that file private.
3. In the VS Code PowerShell terminal, run the commands below. Skip the first command if `.venv` is already set up.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

4. Enter a city such as `Cairo` or `Alexandria, Egypt` and click **Get weather**. The window shows the temperature, conditions, feels-like temperature, humidity, wind speed, and update time.
