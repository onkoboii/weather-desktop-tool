"""Simple cross-platform daily weather desktop notifier."""

from __future__ import annotations

import json
import threading
import time
import tkinter as tk
import webbrowser
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk
from urllib.parse import quote

import requests


APP_DIR = Path.home() / ".weather-desktop-tool"
CONFIG_FILE = APP_DIR / "config.json"


@dataclass
class Config:
    location: str = ""
    send_time: str = "08:00"
    enabled: bool = False


def load_config() -> Config:
    try:
        return Config(**json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
    except (FileNotFoundError, json.JSONDecodeError, TypeError):
        return Config()


def save_config(config: Config) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(asdict(config), ensure_ascii=False, indent=2), encoding="utf-8")


def get_weather(location: str) -> dict:
    encoded = quote(location)
    response = requests.get(f"https://wttr.in/{encoded}?lang=ru&format=j1", timeout=20)
    response.raise_for_status()
    data = response.json()
    current = data["current_condition"][0]
    today = data["weather"][0]
    description = current.get("lang_ru", [{"value": ""}])[0]["value"]
    return {
        "location": location,
        "temperature": int(current["temp_C"]),
        "feels_like": int(current["FeelsLikeC"]),
        "description": description,
        "wind": int(current["windspeedKmph"]),
        "min": int(today["mintempC"]),
        "max": int(today["maxtempC"]),
        "source": f"https://wttr.in/{encoded}?lang=ru",
    }


class WeatherApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Weather Desktop Tool")
        self.resizable(False, False)
        self.config_data = load_config()
        self.last_sent_date: str | None = None
        self._build_ui()
        self.after(30_000, self._scheduler_tick)

    def _build_ui(self) -> None:
        frame = ttk.Frame(self, padding=20)
        frame.grid()
        ttk.Label(frame, text="Город или место:").grid(row=0, column=0, sticky="w")
        self.location = ttk.Entry(frame, width=36)
        self.location.insert(0, self.config_data.location)
        self.location.grid(row=1, column=0, columnspan=2, pady=(4, 14), sticky="ew")
        ttk.Label(frame, text="Время ежедневного прогноза (24 ч):").grid(row=2, column=0, sticky="w")
        self.send_time = ttk.Entry(frame, width=10)
        self.send_time.insert(0, self.config_data.send_time)
        self.send_time.grid(row=3, column=0, pady=(4, 14), sticky="w")
        self.enabled = tk.BooleanVar(value=self.config_data.enabled)
        ttk.Checkbutton(frame, text="Включить ежедневное уведомление", variable=self.enabled).grid(row=4, column=0, columnspan=2, sticky="w")
        ttk.Button(frame, text="Сохранить настройки", command=self.save).grid(row=5, column=0, pady=(18, 0), sticky="w")
        ttk.Button(frame, text="Проверить сейчас", command=self.test_now).grid(row=5, column=1, pady=(18, 0), padx=(8, 0), sticky="e")
        self.status = ttk.Label(frame, text="Приложение работает в этом окне.")
        self.status.grid(row=6, column=0, columnspan=2, pady=(14, 0), sticky="w")

    def read_form(self) -> Config:
        location = self.location.get().strip()
        send_time = self.send_time.get().strip()
        if not location:
            raise ValueError("Укажите город или место.")
        try:
            datetime.strptime(send_time, "%H:%M")
        except ValueError as exc:
            raise ValueError("Время должно быть в формате ЧЧ:ММ, например 08:30.") from exc
        return Config(location, send_time, self.enabled.get())

    def save(self) -> None:
        try:
            self.config_data = self.read_form()
            save_config(self.config_data)
            self.status.configure(text="Настройки сохранены.")
        except ValueError as exc:
            messagebox.showerror("Проверьте настройки", str(exc))

    def test_now(self) -> None:
        try:
            config = self.read_form()
        except ValueError as exc:
            messagebox.showerror("Проверьте настройки", str(exc))
            return
        self.status.configure(text="Получаю прогноз…")
        threading.Thread(target=self._fetch_and_show, args=(config.location,), daemon=True).start()

    def _fetch_and_show(self, location: str) -> None:
        try:
            weather = get_weather(location)
            self.after(0, lambda: self.show_weather(weather))
        except requests.RequestException as exc:
            self.after(0, lambda: messagebox.showerror("Ошибка сети", str(exc)))
        except (KeyError, ValueError) as exc:
            self.after(0, lambda: messagebox.showerror("Ошибка прогноза", str(exc)))
        finally:
            self.after(0, lambda: self.status.configure(text="Приложение работает в этом окне."))

    def show_weather(self, weather: dict) -> None:
        popup = tk.Toplevel(self)
        popup.title(f"Погода — {weather['location']}")
        popup.resizable(False, False)
        popup.attributes("-topmost", True)
        frame = ttk.Frame(popup, padding=18)
        frame.grid()
        ttk.Label(frame, text=f"Погода на сегодня: {weather['location']}", font=("TkDefaultFont", 12, "bold")).grid(sticky="w")
        text = (f"Сейчас: {weather['temperature']}°C (ощущается как {weather['feels_like']}°C)\n"
                f"{weather['description']}\n"
                f"Сегодня: от {weather['min']}°C до {weather['max']}°C; ветер {weather['wind']} км/ч")
        ttk.Label(frame, text=text, justify="left").grid(pady=(12, 12), sticky="w")
        link = ttk.Label(frame, text="Открыть источник прогноза", foreground="#1769aa", cursor="hand2")
        link.grid(sticky="w")
        link.bind("<Button-1>", lambda _event: webbrowser.open(weather["source"]))
        ttk.Button(frame, text="Закрыть", command=popup.destroy).grid(pady=(14, 0), sticky="e")

    def _scheduler_tick(self) -> None:
        config = load_config()
        now = datetime.now()
        if config.enabled and config.location and now.strftime("%H:%M") == config.send_time and self.last_sent_date != now.date().isoformat():
            self.last_sent_date = now.date().isoformat()
            threading.Thread(target=self._fetch_and_show, args=(config.location,), daemon=True).start()
        self.after(30_000, self._scheduler_tick)


if __name__ == "__main__":
    WeatherApp().mainloop()
