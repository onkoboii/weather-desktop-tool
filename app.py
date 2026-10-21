"""Modern desktop weather dashboard with daily hourly precipitation details."""

from __future__ import annotations

import json
import threading
import tkinter as tk
import webbrowser
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from tkinter import messagebox

import requests


APP_DIR = Path.home() / ".weather-desktop-tool"
CONFIG_FILE = APP_DIR / "config.json"
GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
SOURCE_URL = "https://open-meteo.com/"

THEMES = {
    "dark": {
        "bg": "#101722", "surface": "#182333", "card": "#1d2a3b", "raised": "#25354a",
        "text": "#f1f5fb", "muted": "#9eafc4", "accent": "#82d4ff", "accent2": "#a6e4d1",
        "line": "#34465c", "input": "#111b29", "shadow": "#0b111a", "danger": "#ff9e9e",
    },
    "light": {
        "bg": "#edf3f7", "surface": "#f8fbfd", "card": "#ffffff", "raised": "#e8f1f7",
        "text": "#1a2938", "muted": "#65788b", "accent": "#147fb5", "accent2": "#278b74",
        "line": "#d6e2eb", "input": "#ffffff", "shadow": "#dce6ed", "danger": "#b43232",
    },
}

WEATHER = {
    0: ("Ясно", "☀"), 1: ("Преимущественно ясно", "🌤"), 2: ("Переменная облачность", "⛅"),
    3: ("Облачно", "☁"), 45: ("Туман", "🌫"), 48: ("Изморозь и туман", "🌫"),
    51: ("Лёгкая морось", "🌦"), 53: ("Морось", "🌦"), 55: ("Сильная морось", "🌧"),
    56: ("Ледяная морось", "🌧"), 57: ("Сильная ледяная морось", "🌧"),
    61: ("Небольшой дождь", "🌦"), 63: ("Дождь", "🌧"), 65: ("Сильный дождь", "🌧"),
    66: ("Ледяной дождь", "🌧"), 67: ("Сильный ледяной дождь", "🌧"),
    71: ("Небольшой снег", "🌨"), 73: ("Снег", "🌨"), 75: ("Сильный снег", "❄"),
    77: ("Снежные зёрна", "❄"), 80: ("Кратковременный дождь", "🌦"),
    81: ("Ливень", "🌧"), 82: ("Сильный ливень", "⛈"), 85: ("Снегопад", "🌨"),
    86: ("Сильный снегопад", "❄"), 95: ("Гроза", "⛈"), 96: ("Гроза с небольшим градом", "⛈"),
    97: ("Сильная гроза", "⛈"),
    99: ("Сильная гроза с градом (модельный код)", "⛈"),
}


@dataclass
class Config:
    location: str = ""
    send_time: str = "08:00"
    enabled: bool = False
    latitude: float | None = None
    longitude: float | None = None
    country: str = ""
    theme: str = "dark"
    language: str = "ru"


TEXT = {
    "ru": {
        "app_title":"Aether · погода на сегодня",
        "brand":"ПОГОДА · ВАШ ДЕНЬ В ДЕТАЛЯХ", "theme_light":"☀  Светлая тема", "theme_dark":"☾  Тёмная тема",
        "place":"МЕСТО", "city_hint":"Начните вводить название — подберём город и страну", "choose_hint":"Выберите точное совпадение, чтобы загрузить прогноз",
        "search":"Показать прогноз", "refresh":"Обновить прогноз", "loading":"Загружаю…", "daily":"ЕЖЕДНЕВНАЯ СВОДКА", "time":"Время",
        "enabled":"Включить", "save":"Сохранить настройки", "open_app":"Приложение должно быть открыто", "choose_city":"Выберите город, чтобы загрузить прогноз",
        "intro":"Сегодняшняя погода и осадки по часам появятся здесь", "chart":"КАРТИНА ДНЯ", "risk":"ОСАДКИ И РИСКИ",
        "rain_loading":"Дождь: загрузите прогноз", "hail_loading":"Град: данных пока нет", "parts":"Утро · День · Вечер",
        "hourly":"ПОЧАСОВО", "hourly_hint":"Осадки · вероятность · температура", "ready":"Готово · прогноз обновляется по запросу",
        "source":"Источник данных: Open-Meteo ↗", "network_search":"Не удалось подключиться к поиску городов", "no_cities":"Совпадений не найдено — попробуйте другое написание",
        "select_hint":"Выберите город из списка подсказок", "saved":"Настройки сохранены · ежедневная сводка {time}",
        "bad_time":"Введите время в формате ЧЧ:ММ, например 08:30", "loading_status":"Получаю свежий почасовой прогноз…",
        "network_status":"Не удалось обновить прогноз · проверьте интернет", "error_title":"Не удалось загрузить погоду",
        "format_error":"Неожиданный формат прогноза: {error}", "no_hours":"Для выбранного места почасовые данные не найдены",
        "updated":"Обновлено · местное время {timezone} · источник Open-Meteo", "rain":"Дождь/осадки: {timing}\nдо {probability}% · ~{amount:.1f} мм",
        "rain_none":"Дождь: маловероятен сегодня", "hail_storm":"Гроза возможна около {time}. Код модели указывает град, но это прогнозный сигнал, а не подтверждение.",
        "hail_risk":"Высокая конвективная энергия ({cape:.0f} J/kg), но отдельной вероятности града API не даёт.",
        "hail_none":"Град: явного сигнала грозы нет. API не выдаёт отдельную вероятность града.",
        "part_wet":"{name}: {temp}° · осадки до {probability}%", "part_dry":"{name}: {temp}° · преимущественно сухо",
        "parts_empty":"Дневных часов в прогнозе не осталось", "precip_legend":"вероятность осадков", "wind":"ветер {speed} км/ч",
        "debug_title":"ПОДРОБНОСТИ · {time}", "debug_temp":"Температура: {temp}° · ощущается как {feels}°",
        "current_summary":"{icon}  {temp}° · {description} · ощущается {feels}° · ветер {wind} км/ч",
        "debug_precip":"Осадки: {amount} · вероятность {probability}%", "debug_condition":"Условия: {description}",
        "debug_wind":"Ветер: {speed} км/ч", "debug_cape":"Конвективная энергия: {cape:.0f} J/kg", "close":"Закрыть",
        "period_morning":"Утро", "period_day":"День", "period_evening":"Вечер", "weather":"Погода",
    },
    "en": {
        "app_title":"Aether · weather today",
        "brand":"WEATHER · YOUR DAY AT A GLANCE", "theme_light":"☀  Light theme", "theme_dark":"☾  Dark theme",
        "place":"LOCATION", "city_hint":"Type a place name to find cities and countries", "choose_hint":"Select a match to load its forecast",
        "search":"Show forecast", "refresh":"Refresh forecast", "loading":"Loading…", "daily":"DAILY SUMMARY", "time":"Time",
        "enabled":"Enable", "save":"Save settings", "open_app":"Keep the app open", "choose_city":"Choose a city to load its forecast",
        "intro":"Today’s weather and hourly precipitation will appear here", "chart":"DAY AT A GLANCE", "risk":"PRECIPITATION & RISKS",
        "rain_loading":"Rain: load the forecast", "hail_loading":"Hail: no data yet", "parts":"Morning · Day · Evening",
        "hourly":"HOURLY", "hourly_hint":"Precipitation · chance · temperature", "ready":"Ready · forecast updates on request",
        "source":"Weather data: Open-Meteo ↗", "network_search":"Could not connect to city search", "no_cities":"No matches found — try another spelling",
        "select_hint":"Select a city from the suggestions", "saved":"Settings saved · daily summary at {time}",
        "bad_time":"Enter time as HH:MM, for example 08:30", "loading_status":"Loading the latest hourly forecast…",
        "network_status":"Could not update forecast · check your internet", "error_title":"Could not load weather",
        "format_error":"Unexpected forecast format: {error}", "no_hours":"No hourly data found for this location",
        "updated":"Updated · local timezone {timezone} · source Open-Meteo", "rain":"Rain/precipitation: {timing}\nup to {probability}% · ~{amount:.1f} mm",
        "rain_none":"Rain: unlikely today", "hail_storm":"Thunderstorms possible around {time}. The model indicates hail, but this is a forecast signal, not confirmation.",
        "hail_risk":"High convective energy ({cape:.0f} J/kg), but the API provides no separate hail probability.",
        "hail_none":"No clear thunderstorm signal. The API provides no separate hail probability.",
        "part_wet":"{name}: {temp}° · precipitation up to {probability}%", "part_dry":"{name}: {temp}° · mostly dry",
        "parts_empty":"No daytime hours remain in the forecast", "precip_legend":"precipitation chance", "wind":"wind {speed} km/h",
        "debug_title":"DETAILS · {time}", "debug_temp":"Temperature: {temp}° · feels like {feels}°",
        "current_summary":"{icon}  {temp}° · {description} · feels like {feels}° · wind {wind} km/h",
        "debug_precip":"Precipitation: {amount} · chance {probability}%", "debug_condition":"Conditions: {description}",
        "debug_wind":"Wind: {speed} km/h", "debug_cape":"Convective energy: {cape:.0f} J/kg", "close":"Close",
        "period_morning":"Morning", "period_day":"Day", "period_evening":"Evening", "weather":"Weather",
    },
    "zh": {
        "app_title":"Aether · 今日天气",
        "brand":"天气 · 今日天气一览", "theme_light":"☀  浅色主题", "theme_dark":"☾  深色主题",
        "place":"地点", "city_hint":"输入地点名称以搜索城市和国家/地区", "choose_hint":"选择匹配地点以加载天气预报",
        "search":"查看天气", "refresh":"刷新预报", "loading":"正在加载…", "daily":"每日天气摘要", "time":"时间",
        "enabled":"启用", "save":"保存设置", "open_app":"请保持应用运行", "choose_city":"选择城市以加载天气预报",
        "intro":"今日天气和逐小时降水信息将在此显示", "chart":"今日天气概览", "risk":"降水与天气风险",
        "rain_loading":"降雨：请先加载预报", "hail_loading":"冰雹：暂无数据", "parts":"早晨 · 白天 · 晚间",
        "hourly":"逐小时预报", "hourly_hint":"降水 · 概率 · 气温", "ready":"就绪 · 点击按钮更新预报",
        "source":"天气数据：Open-Meteo ↗", "network_search":"无法连接城市搜索服务", "no_cities":"未找到匹配地点，请尝试其他拼写",
        "select_hint":"请从建议列表中选择城市", "saved":"设置已保存 · 每日摘要时间 {time}",
        "bad_time":"时间格式应为 HH:MM，例如 08:30", "loading_status":"正在获取最新逐小时预报…",
        "network_status":"无法更新天气 · 请检查网络连接", "error_title":"无法加载天气", "format_error":"天气数据格式异常：{error}",
        "no_hours":"未找到该地点的逐小时天气数据", "updated":"已更新 · 当地时区 {timezone} · 数据来源 Open-Meteo",
        "rain":"降雨/降水：{timing}\n最高 {probability}% · 约 {amount:.1f} 毫米", "rain_none":"今日降雨可能性较低",
        "hail_storm":"约 {time} 可能有雷暴。模型提示可能有冰雹，但这只是预报信号，并非确认。",
        "hail_risk":"对流能量较高（{cape:.0f} J/kg），但 API 不提供单独的冰雹概率。",
        "hail_none":"暂无明显雷暴信号。API 不提供单独的冰雹概率。",
        "part_wet":"{name}：{temp}° · 降水概率最高 {probability}%", "part_dry":"{name}：{temp}° · 大多干燥",
        "parts_empty":"预报中已无白天时段", "precip_legend":"降水概率", "wind":"风速 {speed} 公里/小时",
        "debug_title":"天气详情 · {time}", "debug_temp":"气温：{temp}° · 体感 {feels}°",
        "current_summary":"{icon}  {temp}° · {description} · 体感 {feels}° · 风速 {wind} 公里/小时",
        "debug_precip":"降水：{amount} · 概率 {probability}%", "debug_condition":"天气状况：{description}",
        "debug_wind":"风速：{speed} 公里/小时", "debug_cape":"对流能量：{cape:.0f} J/kg", "close":"关闭",
        "period_morning":"早晨", "period_day":"白天", "period_evening":"晚间", "weather":"天气",
    },
}

WEATHER_TEXT = {
    "ru": {0:"Ясно",1:"Преимущественно ясно",2:"Переменная облачность",3:"Облачно",45:"Туман",48:"Изморозь и туман",51:"Лёгкая морось",53:"Морось",55:"Сильная морось",56:"Ледяная морось",57:"Сильная ледяная морось",61:"Небольшой дождь",63:"Дождь",65:"Сильный дождь",66:"Ледяной дождь",67:"Сильный ледяной дождь",71:"Небольшой снег",73:"Снег",75:"Сильный снег",77:"Снежные зёрна",80:"Кратковременный дождь",81:"Ливень",82:"Сильный ливень",85:"Снегопад",86:"Сильный снегопад",95:"Гроза",96:"Гроза с небольшим градом",97:"Сильная гроза",99:"Гроза с крупным градом"},
    "en": {0:"Clear",1:"Mostly clear",2:"Partly cloudy",3:"Overcast",45:"Fog",48:"Rime fog",51:"Light drizzle",53:"Drizzle",55:"Heavy drizzle",56:"Freezing drizzle",57:"Heavy freezing drizzle",61:"Light rain",63:"Rain",65:"Heavy rain",66:"Freezing rain",67:"Heavy freezing rain",71:"Light snow",73:"Snow",75:"Heavy snow",77:"Snow grains",80:"Rain showers",81:"Showers",82:"Heavy showers",85:"Snow showers",86:"Heavy snow showers",95:"Thunderstorm",96:"Thunderstorm with slight hail",97:"Heavy thunderstorm",99:"Thunderstorm with heavy hail"},
    "zh": {0:"晴",1:"大致晴朗",2:"局部多云",3:"阴天",45:"雾",48:"雾凇",51:"小毛毛雨",53:"毛毛雨",55:"强毛毛雨",56:"冻毛毛雨",57:"强冻毛毛雨",61:"小雨",63:"雨",65:"大雨",66:"冻雨",67:"强冻雨",71:"小雪",73:"降雪",75:"大雪",77:"雪粒",80:"阵雨",81:"阵雨",82:"强阵雨",85:"阵雪",86:"强阵雪",95:"雷暴",96:"雷暴伴轻微冰雹",97:"强雷暴",99:"雷暴伴强冰雹"},
}


def load_config() -> Config:
    try:
        values = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        allowed = Config.__dataclass_fields__.keys()
        config = Config(**{key: value for key, value in values.items() if key in allowed})
        if config.language not in TEXT:
            config.language = "ru"
        if config.theme not in THEMES:
            config.theme = "dark"
        return config
    except (FileNotFoundError, json.JSONDecodeError, TypeError):
        return Config()


def save_config(config: Config) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(asdict(config), ensure_ascii=False, indent=2), encoding="utf-8")


def search_cities(query: str, language: str = "ru") -> list[dict]:
    response = requests.get(GEO_URL, params={"name": query, "count": 7, "language": language, "format": "json"}, timeout=12)
    response.raise_for_status()
    return response.json().get("results", [])


def get_weather(latitude: float, longitude: float) -> dict:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": "auto",
        "forecast_days": 1,
        "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m,is_day",
        "hourly": "temperature_2m,apparent_temperature,precipitation_probability,precipitation,rain,showers,snowfall,weather_code,wind_speed_10m,cape",
    }
    response = requests.get(FORECAST_URL, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()
    current = data["current"]
    hourly = data["hourly"]
    now = datetime.fromisoformat(current["time"])
    hours = []
    for index, stamp in enumerate(hourly["time"]):
        local_time = datetime.fromisoformat(stamp)
        if local_time.date() != now.date():
            continue
        code = int(hourly["weather_code"][index])
        hours.append({
            "time": local_time.strftime("%H:%M"), "hour": local_time.hour,
            "temperature": round(hourly["temperature_2m"][index]),
            "feels_like": round(hourly["apparent_temperature"][index]),
            "probability": int(hourly["precipitation_probability"][index] or 0),
            "precipitation": float(hourly["precipitation"][index] or 0),
            "rain": float(hourly["rain"][index] or 0),
            "showers": float(hourly["showers"][index] or 0),
            "snowfall": float(hourly["snowfall"][index] or 0),
            "wind": round(hourly["wind_speed_10m"][index]),
            "cape": float(hourly.get("cape", [0] * len(hourly["time"]))[index] or 0),
            "code": code,
            "icon": WEATHER.get(code, ("Переменная погода", "🌡"))[1],
        })
    return {
        "current": {
            "temperature": round(current["temperature_2m"]),
            "feels_like": round(current["apparent_temperature"]),
            "wind": round(current["wind_speed_10m"]),
            "code": int(current["weather_code"]),
        },
        "hours": hours,
        "timezone": data.get("timezone", ""),
    }


class WeatherApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.config_data = load_config()
        self.palette = THEMES.get(self.config_data.theme, THEMES["dark"])
        self.city_results: list[dict] = []
        self.location_job = None
        self.tooltip_job = None
        self.tooltip = None
        self.hovered_point = None
        self.last_sent_date: str | None = None
        self.hour_buttons: list[tk.Widget] = []
        self.current_weather: dict | None = None
        self.notify_when_loaded = False
        self.title(self.tr("app_title"))
        self.geometry("1120x820")
        self.minsize(920, 700)
        self.configure(bg=self.palette["bg"])
        try:
            self.attributes("-alpha", 0.98)
        except tk.TclError:
            pass
        self._build_ui()
        self.after(30_000, self._scheduler_tick)

    def c(self, name: str) -> str:
        return self.palette[name]

    def tr(self, key: str, **values) -> str:
        return TEXT[self.config_data.language].get(key, key).format(**values)

    def weather_description(self, code: int) -> tuple[str, str]:
        return WEATHER_TEXT[self.config_data.language].get(code, "—"), WEATHER.get(code, ("", "🌡"))[1]

    def _label(self, parent, text, *, size=10, color=None, bold=False, **kwargs):
        return tk.Label(parent, text=text, bg=kwargs.pop("bg", self.c("card")), fg=color or self.c("text"),
                        font=("Segoe UI", size, "bold" if bold else "normal"), **kwargs)

    def _card(self, parent, **kwargs):
        # Layered surfaces create a subtle glass-panel effect while staying cross-platform.
        return tk.Frame(parent, bg=self.c("card"), highlightthickness=1,
                        highlightbackground=self.c("line"), bd=0, **kwargs)

    def _build_ui(self) -> None:
        self.root = tk.Frame(self, bg=self.c("bg"), padx=28, pady=22)
        self.root.pack(fill="both", expand=True)
        top = tk.Frame(self.root, bg=self.c("bg"))
        top.pack(fill="x", pady=(0, 20))
        self._label(top, "AETHER", size=12, color=self.c("accent"), bold=True, bg=self.c("bg")).pack(side="left")
        self._label(top, self.tr("brand"), size=9, color=self.c("muted"), bg=self.c("bg")).pack(side="left", padx=(14, 0))
        self.language_button = self._button(top, {"ru":"RU ▾", "en":"EN ▾", "zh":"中文 ▾"}[self.config_data.language], self.toggle_language)
        self.language_button.pack(side="right", padx=(8, 0))
        self.theme_button = tk.Button(top, command=self.toggle_theme, relief="flat", bd=0, padx=14, pady=8,
                                      cursor="hand2", font=("Segoe UI", 9, "bold"))
        self.theme_button.pack(side="right")
        self._paint_theme_button()

        search_card = self._card(self.root)
        search_card.pack(fill="x", pady=(0, 16))
        search_inner = tk.Frame(search_card, bg=self.c("card"), padx=18, pady=14)
        search_inner.pack(fill="x")
        self._label(search_inner, self.tr("place"), size=8, color=self.c("muted"), bold=True).pack(anchor="w")
        row = tk.Frame(search_inner, bg=self.c("card"))
        row.pack(fill="x", pady=(6, 0))
        self.location_var = tk.StringVar(value=self.config_data.location)
        self.location_entry = tk.Entry(row, textvariable=self.location_var, font=("Segoe UI", 13), relief="flat", bd=0,
                                       bg=self.c("input"), fg=self.c("text"), insertbackground=self.c("accent"))
        self.location_entry.pack(side="left", fill="x", expand=True, ipady=10, padx=(0, 10))
        self.location_entry.bind("<KeyRelease>", self._on_city_key)
        self.location_entry.bind("<Down>", self._focus_suggestions)
        self.location_entry.bind("<Return>", self._select_first_suggestion)
        self.suggestion_box = tk.Listbox(self.root, height=6, font=("Segoe UI", 10), relief="flat", bd=0,
                                          activestyle="none", selectmode="single")
        self.suggestion_box.bind("<ButtonRelease-1>", self._choose_city)
        self.suggestion_box.bind("<Return>", self._choose_city)
        self.fetch_button = self._button(row, self.tr("search"), self.fetch_weather, primary=True)
        self.fetch_button.pack(side="right")
        self.location_hint = self._label(search_inner, self.tr("city_hint"), size=8, color=self.c("muted"))
        self.location_hint.pack(anchor="w", pady=(6, 0))
        schedule = tk.Frame(search_inner, bg=self.c("card"))
        schedule.pack(fill="x", pady=(12, 0))
        self._label(schedule, self.tr("daily"), size=8, color=self.c("muted"), bold=True).pack(side="left")
        self._label(schedule, self.tr("time"), size=9, color=self.c("muted")).pack(side="left", padx=(12, 5))
        self.schedule_time = tk.Entry(schedule, width=7, font=("Segoe UI", 10), justify="center", relief="flat", bd=0,
                                      bg=self.c("input"), fg=self.c("text"), insertbackground=self.c("accent"))
        self.schedule_time.insert(0, self.config_data.send_time)
        self.schedule_time.pack(side="left", padx=(12, 8), ipady=5)
        self.daily_enabled = tk.BooleanVar(value=self.config_data.enabled)
        self.daily_check = tk.Checkbutton(schedule, text=self.tr("enabled"), variable=self.daily_enabled, bg=self.c("card"), fg=self.c("text"),
                                          selectcolor=self.c("raised"), activebackground=self.c("card"), activeforeground=self.c("text"),
                                          font=("Segoe UI", 9), relief="flat", bd=0)
        self.daily_check.pack(side="left")
        self.save_button = self._button(schedule, self.tr("save"), self.save_settings)
        self.save_button.pack(side="left", padx=(10, 0))
        self._label(schedule, self.tr("open_app"), size=8, color=self.c("muted")).pack(side="right")

        self.current_card = self._card(self.root)
        self.current_card.pack(fill="x", pady=(0, 16))
        self.current_inner = tk.Frame(self.current_card, bg=self.c("card"), padx=22, pady=18)
        self.current_inner.pack(fill="x")
        self.now_location = self._label(self.current_inner, self.tr("choose_city"), size=17, bold=True)
        self.now_location.pack(anchor="w")
        self.now_summary = self._label(self.current_inner, self.tr("intro"), size=10, color=self.c("muted"))
        self.now_summary.pack(anchor="w", pady=(4, 0))

        overview = tk.Frame(self.root, bg=self.c("bg"))
        overview.pack(fill="x", pady=(0, 16))
        self.day_card = self._card(overview)
        self.day_card.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self._label(self.day_card, self.tr("chart"), size=8, color=self.c("muted"), bold=True).pack(anchor="w", padx=16, pady=(13, 4))
        self.chart = tk.Canvas(self.day_card, height=160, bg=self.c("card"), highlightthickness=0)
        self.chart.pack(fill="x", padx=10, pady=(0, 9))
        self.summary_card = self._card(overview, width=290, height=205)
        self.summary_card.pack(side="right", fill="y", padx=(8, 0))
        self.summary_card.pack_propagate(False)
        self._label(self.summary_card, self.tr("risk"), size=8, color=self.c("muted"), bold=True).pack(anchor="w", padx=16, pady=(13, 8))
        self.rain_summary = self._label(self.summary_card, self.tr("rain_loading"), size=10, bold=True, wraplength=258, justify="left")
        self.rain_summary.pack(anchor="w", padx=16, pady=5)
        self.hail_summary = self._label(self.summary_card, self.tr("hail_loading"), size=9, color=self.c("muted"), wraplength=258, justify="left")
        self.hail_summary.pack(anchor="w", padx=16, pady=5)
        self.dayparts = self._label(self.summary_card, self.tr("parts"), size=9, color=self.c("accent2"), wraplength=258, justify="left")
        self.dayparts.pack(anchor="w", padx=16, pady=(7, 12))

        forecast_card = self._card(self.root)
        forecast_card.pack(fill="both", expand=True)
        header = tk.Frame(forecast_card, bg=self.c("card"), padx=16, pady=12)
        header.pack(fill="x")
        self._label(header, self.tr("hourly"), size=9, color=self.c("muted"), bold=True).pack(side="left")
        self._label(header, self.tr("hourly_hint"), size=8, color=self.c("muted")).pack(side="right")
        self.hours_canvas = tk.Canvas(forecast_card, height=174, bg=self.c("card"), highlightthickness=0)
        self.hours_scroll = tk.Scrollbar(forecast_card, orient="horizontal", command=self.hours_canvas.xview)
        self.hours_canvas.configure(xscrollcommand=self.hours_scroll.set)
        self.hours_canvas.pack(fill="x", padx=12)
        self.hours_scroll.pack(fill="x", padx=12, pady=(0, 10))
        footer = tk.Frame(self.root, bg=self.c("bg"))
        footer.pack(fill="x", pady=(12, 0))
        self.status = self._label(footer, self.tr("ready"), size=8, color=self.c("muted"), bg=self.c("bg"))
        self.status.pack(side="left")
        source = self._label(footer, self.tr("source"), size=8, color=self.c("accent"), bg=self.c("bg"), cursor="hand2")
        source.pack(side="right")
        source.bind("<Button-1>", lambda _event: webbrowser.open(SOURCE_URL))
        if self.config_data.latitude is not None and self.config_data.longitude is not None:
            self.after(400, self.fetch_weather)

    def _button(self, parent, text, command, primary=False):
        return tk.Button(parent, text=text, command=command, relief="flat", bd=0, padx=17, pady=10,
                         cursor="hand2", font=("Segoe UI", 9, "bold"), bg=self.c("accent") if primary else self.c("raised"),
                         fg=("#10202b" if self.config_data.theme == "dark" else "#ffffff") if primary else self.c("text"),
                         activebackground=self.c("accent2"), activeforeground=self.c("text"))

    def _paint_theme_button(self):
        self.theme_button.configure(text=self.tr("theme_light") if self.config_data.theme == "dark" else self.tr("theme_dark"),
                                   bg=self.c("raised"), fg=self.c("text"), activebackground=self.c("accent"))

    def toggle_language(self):
        languages = ("ru", "en", "zh")
        self.config_data.language = languages[(languages.index(self.config_data.language) + 1) % len(languages)]
        save_config(self.config_data)
        self._rebuild()

    def toggle_theme(self):
        self.config_data.theme = "light" if self.config_data.theme == "dark" else "dark"
        self.palette = THEMES[self.config_data.theme]
        save_config(self.config_data)
        self._rebuild()

    def _rebuild(self):
        for child in self.winfo_children():
            child.destroy()
        self.configure(bg=self.c("bg"))
        self._build_ui()
        if self.current_weather:
            self.render_weather(self.current_weather)

    def _on_city_key(self, _event=None):
        if self.location_job:
            self.after_cancel(self.location_job)
        query = self.location_var.get().strip()
        if len(query) < 2:
            self._hide_suggestions()
            return
        self.location_job = self.after(350, lambda: threading.Thread(target=self._city_search_worker, args=(query,), daemon=True).start())

    def _city_search_worker(self, query: str):
        try:
            results = search_cities(query, self.config_data.language)
            self.after(0, lambda: self._show_suggestions(query, results))
        except requests.RequestException:
            self.after(0, lambda: self.location_hint.configure(text=self.tr("network_search"), fg=self.c("danger")))

    def _show_suggestions(self, query: str, results: list[dict]):
        if self.location_var.get().strip() != query:
            return
        self.city_results = results
        self.suggestion_box.delete(0, tk.END)
        for place in results:
            parts = [place.get("name", "")]
            if place.get("admin1") and place["admin1"] != place.get("name"):
                parts.append(place["admin1"])
            if place.get("country"):
                parts.append(place["country"])
            self.suggestion_box.insert(tk.END, "  ·  ".join(parts))
        if results:
            self.suggestion_box.configure(bg=self.c("surface"), fg=self.c("text"), selectbackground=self.c("accent"), selectforeground="#12202b")
            x = self.location_entry.winfo_rootx() - self.winfo_rootx()
            y = self.location_entry.winfo_rooty() - self.winfo_rooty() + self.location_entry.winfo_height() + 6
            self.suggestion_box.place(x=x, y=y, width=max(self.location_entry.winfo_width(), 430))
            self.suggestion_box.lift()
            self.location_hint.configure(text=self.tr("choose_hint"), fg=self.c("muted"))
        else:
            self._hide_suggestions()
            self.location_hint.configure(text=self.tr("no_cities"), fg=self.c("muted"))

    def _hide_suggestions(self):
        self.suggestion_box.place_forget()

    def _focus_suggestions(self, _event=None):
        if self.city_results:
            self.suggestion_box.focus_set()
            self.suggestion_box.selection_clear(0, tk.END)
            self.suggestion_box.selection_set(0)
            self.suggestion_box.activate(0)
        return "break"

    def _select_first_suggestion(self, _event=None):
        if self.city_results:
            self._select_city(self.city_results[0])
            return "break"
        return None

    def _choose_city(self, _event=None):
        selection = self.suggestion_box.curselection()
        if selection and selection[0] < len(self.city_results):
            self._select_city(self.city_results[selection[0]])

    def _select_city(self, place: dict):
        self._hide_suggestions()
        self.config_data.location = place.get("name", "")
        self.config_data.country = place.get("country", "")
        self.config_data.latitude = float(place["latitude"])
        self.config_data.longitude = float(place["longitude"])
        self.location_var.set(f"{self.config_data.location}, {self.config_data.country}".strip(", "))
        self.location_hint.configure(text=f"✓  {self.config_data.country}", fg=self.c("accent2"))
        save_config(self.config_data)
        self.fetch_weather()

    def save_settings(self):
        send_time = self.schedule_time.get().strip()
        try:
            datetime.strptime(send_time, "%H:%M")
        except ValueError:
            self.status.configure(text=self.tr("bad_time"), fg=self.c("danger"))
            return
        self.config_data.send_time = send_time
        self.config_data.enabled = self.daily_enabled.get()
        self.config_data.location = self.location_var.get().strip()
        save_config(self.config_data)
        self.status.configure(text=self.tr("saved", time=send_time), fg=self.c("accent2"))

    def fetch_weather(self):
        if self.config_data.latitude is None or self.config_data.longitude is None:
            if self.city_results:
                self._select_city(self.city_results[0])
            else:
                self.location_hint.configure(text=self.tr("select_hint"), fg=self.c("danger"))
            return
        self.fetch_button.configure(state="disabled", text=self.tr("loading"))
        self.status.configure(text=self.tr("loading_status"))
        threading.Thread(target=self._weather_worker, args=(self.config_data.latitude, self.config_data.longitude), daemon=True).start()

    def _weather_worker(self, latitude: float, longitude: float):
        try:
            payload = get_weather(latitude, longitude)
            self.after(0, lambda: self.render_weather(payload))
        except requests.RequestException as exc:
            self.after(0, lambda error=str(exc): self._show_error(error))
        except (KeyError, ValueError, TypeError) as exc:
            self.after(0, lambda error=str(exc): self._show_error(self.tr("format_error", error=error)))
        finally:
            self.after(0, lambda: self.fetch_button.configure(state="normal", text=self.tr("refresh")))

    def _show_error(self, error: str):
        self.status.configure(text=self.tr("network_status"), fg=self.c("danger"))
        messagebox.showerror(self.tr("error_title"), error)

    def render_weather(self, payload: dict):
        self.current_weather = payload
        hours = payload["hours"]
        if not hours:
            self.status.configure(text=self.tr("no_hours"), fg=self.c("danger"))
            return
        current = payload["current"]
        code = current["code"]
        description, icon = self.weather_description(code)
        self.now_location.configure(text=f"{self.config_data.location}, {self.config_data.country}".strip(", "))
        self.now_summary.configure(text=self.tr("current_summary", icon=icon, temp=current["temperature"],
                                                description=description, feels=current["feels_like"], wind=current["wind"]))
        self._draw_chart(hours)
        self._draw_hours(hours)
        rain_hours = [hour for hour in hours if hour["precipitation"] >= 0.1 or hour["probability"] >= 35]
        if rain_hours:
            total = sum(hour["precipitation"] for hour in hours)
            first = rain_hours[0]
            last = rain_hours[-1]
            timing = first["time"] if first["time"] == last["time"] else f"{first['time']}–{last['time']}"
            self.rain_summary.configure(text=self.tr("rain", timing=timing, probability=max(h["probability"] for h in rain_hours), amount=total))
        else:
            self.rain_summary.configure(text=self.tr("rain_none"))
        thunder = [h for h in hours if h["code"] in (95, 96, 97, 99)]
        if thunder:
            self.hail_summary.configure(text=self.tr("hail_storm", time=thunder[0]["time"]))
        else:
            cape_peak = max((h["cape"] for h in hours), default=0)
            self.hail_summary.configure(text=self.tr("hail_risk", cape=cape_peak) if cape_peak >= 1000 else self.tr("hail_none"))
        parts = []
        for name_key, begin, end in (("period_morning", 5, 12), ("period_day", 12, 18), ("period_evening", 18, 23)):
            name = self.tr(name_key)
            subset = [hour for hour in hours if begin <= hour["hour"] < end]
            if subset:
                wet = [hour for hour in subset if hour["probability"] >= 35 or hour["precipitation"] >= 0.1]
                max_temp = max(h["temperature"] for h in subset)
                if wet:
                    label = self.tr("part_wet", name=name, temp=max_temp, probability=max(h["probability"] for h in wet))
                else:
                    label = self.tr("part_dry", name=name, temp=max_temp)
                parts.append(label)
        self.dayparts.configure(text="\n".join(parts) or self.tr("parts_empty"))
        self.status.configure(text=self.tr("updated", timezone=payload["timezone"]), fg=self.c("muted"))
        if self.notify_when_loaded:
            self.notify_when_loaded = False
            self._show_daily_popup(payload)

    def _show_daily_popup(self, payload: dict):
        current = payload["current"]
        description, icon = self.weather_description(current["code"])
        popup = tk.Toplevel(self)
        popup.title(self.tr("weather"))
        popup.configure(bg=self.c("card"))
        popup.resizable(False, False)
        popup.attributes("-topmost", True)
        popup.geometry("360x160+80+80")
        self._label(popup, f"{self.tr('weather')} · {self.config_data.location}", size=12, bold=True).pack(anchor="w", padx=18, pady=(16, 5))
        self._label(popup, f"{icon} {description}\n{self.tr('debug_temp', temp=current['temperature'], feels=current['feels_like'])} · {self.tr('wind', speed=current['wind'])}", size=10, color=self.c("muted"), justify="left").pack(anchor="w", padx=18)
        link = self._label(popup, self.tr("hourly_hint") + " ↗", size=9, color=self.c("accent"), cursor="hand2")
        link.pack(anchor="w", padx=18, pady=(12, 10))
        link.bind("<Button-1>", lambda _event: (popup.destroy(), self.deiconify(), self.lift()))
        close = tk.Button(popup, text=self.tr("close"), command=popup.destroy, relief="flat", bd=0,
                          bg=self.c("raised"), fg=self.c("text"), padx=12, pady=5, cursor="hand2")
        close.place(relx=1, rely=1, x=-16, y=-12, anchor="se")

    def _draw_chart(self, hours: list[dict]):
        canvas = self.chart
        canvas.delete("all")
        canvas.update_idletasks()
        width = max(canvas.winfo_width(), 420)
        height = 160
        left, right, top, bottom = 24, width - 18, 15, 125
        temperatures = [hour["temperature"] for hour in hours]
        low, high = min(temperatures), max(temperatures)
        span = max(high - low, 2)
        for fraction, label in ((0, "0%"), (0.5, "50%"), (1, "100%")):
            y = bottom - fraction * 78
            canvas.create_line(left, y, right, y, fill=self.c("line"), dash=(2, 4))
            canvas.create_text(4, y, text=label, fill=self.c("muted"), anchor="w", font=("Segoe UI", 7))
        points = []
        self.chart_points = []
        count = max(len(hours), 1)
        for i, hour in enumerate(hours):
            x = left + (right - left) * i / max(count - 1, 1)
            bar_h = 58 * hour["probability"] / 100
            if bar_h > 1:
                canvas.create_rectangle(x - 7, bottom, x + 7, bottom - bar_h, fill=self.c("accent"), outline="", stipple="gray50")
            y = top + 8 + (high - hour["temperature"]) / span * 34
            points.extend((x, y))
            self.chart_points.append((x, y, hour))
        if len(points) >= 4:
            canvas.create_line(*points, fill=self.c("accent2"), width=3, smooth=True)
        for i, hour in enumerate(hours):
            x = left + (right - left) * i / max(count - 1, 1)
            y = top + 8 + (high - hour["temperature"]) / span * 34
            canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill=self.c("accent2"), outline=self.c("card"), width=1)
            if i % 3 == 0 or i == count - 1:
                canvas.create_text(x, 148, text=hour["time"], fill=self.c("muted"), font=("Segoe UI", 7))
                canvas.create_text(x, y - 10, text=f"{hour['temperature']}°", fill=self.c("text"), font=("Segoe UI", 8, "bold"))
        canvas.create_rectangle(width - 130, 5, width - 118, 11, fill=self.c("accent"), outline="")
        canvas.create_text(width - 112, 8, text=self.tr("precip_legend"), anchor="w", fill=self.c("muted"), font=("Segoe UI", 7))
        canvas.bind("<Motion>", self._chart_motion)
        canvas.bind("<Leave>", self._chart_leave)

    def _draw_hours(self, hours: list[dict]):
        canvas = self.hours_canvas
        canvas.delete("all")
        self.hour_buttons.clear()
        x = 0
        for hour in hours:
            card_w, card_h = 104, 158
            canvas.create_rectangle(x + 2, 2, x + card_w, card_h, fill=self.c("surface"), outline=self.c("line"), width=1)
            description, icon = self.weather_description(hour["code"])
            amount = self._precip_amount(hour["precipitation"])
            fields = [
                (hour["time"], 15, self.c("muted"), 9, "normal"),
                (icon, 43, self.c("text"), 23, "normal"),
                (f"{hour['temperature']}°", 70, self.c("text"), 14, "bold"),
                (f"💧 {hour['probability']}%", 91, self.c("accent"), 9, "bold"),
                (amount, 108, self.c("muted"), 8, "normal"),
                (description[:17], 130, self.c("muted"), 7, "normal"),
                (self.tr("wind", speed=hour["wind"]), 145, self.c("muted"), 7, "normal"),
            ]
            for text, y, color, size, weight in fields:
                canvas.create_text(x + card_w / 2, y, text=text, fill=color,
                                   font=("Segoe UI", size, weight), width=card_w - 8)
            x += card_w + 8
        canvas.configure(scrollregion=(0, 0, max(x, canvas.winfo_width()), 174))
        canvas.bind("<MouseWheel>", lambda event: canvas.xview_scroll(-1 if event.delta > 0 else 1, "units"))

    def _chart_motion(self, event):
        if not getattr(self, "chart_points", None):
            return
        px, py = self.chart.canvasx(event.x), self.chart.canvasy(event.y)
        nearest = min(self.chart_points, key=lambda point: (point[0] - px) ** 2 + (point[1] - py) ** 2)
        distance = (nearest[0] - px) ** 2 + (nearest[1] - py) ** 2
        if distance > 16 ** 2:
            self._hide_tooltip()
            return
        hour = nearest[2]
        if self.hovered_point == hour["time"]:
            if self.tooltip:
                self.tooltip.geometry(f"+{event.x_root + 14}+{event.y_root + 14}")
            return
        if self.tooltip_job:
            self.after_cancel(self.tooltip_job)
        self._hide_tooltip()
        self.hovered_point = hour["time"]
        self.tooltip_job = self.after(280, lambda h=hour, x=event.x_root, y=event.y_root: self._show_tooltip(h, x, y))

    def _show_tooltip(self, hour: dict, x_root: int, y_root: int):
        if self.hovered_point != hour["time"]:
            return
        popup = tk.Toplevel(self)
        self.tooltip = popup
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(bg=self.c("line"))
        frame = tk.Frame(popup, bg=self.c("card"), padx=13, pady=10)
        frame.pack(padx=1, pady=1)
        description, _icon = self.weather_description(hour["code"])
        amount = self._precip_amount(hour["precipitation"])
        details = [
            (self.tr("debug_title", time=hour["time"]), True, self.c("accent")),
            (self.tr("debug_temp", temp=hour["temperature"], feels=hour["feels_like"]), False, self.c("text")),
            (self.tr("debug_precip", amount=amount, probability=hour["probability"]), False, self.c("text")),
            (self.tr("debug_condition", description=description), False, self.c("text")),
            (self.tr("debug_wind", speed=hour["wind"]), False, self.c("muted")),
            (self.tr("debug_cape", cape=hour["cape"]), False, self.c("muted")),
        ]
        for line, bold, color in details:
            tk.Label(frame, text=line, bg=self.c("card"), fg=color, anchor="w",
                     font=("Segoe UI", 9, "bold" if bold else "normal")).pack(anchor="w", pady=1)
        popup.geometry(f"+{x_root + 14}+{y_root + 14}")

    def _hide_tooltip(self):
        if self.tooltip_job:
            self.after_cancel(self.tooltip_job)
            self.tooltip_job = None
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
        self.hovered_point = None

    def _chart_leave(self, _event=None):
        self._hide_tooltip()

    def _precip_amount(self, value: float) -> str:
        unit = {"ru": "мм", "en": "mm", "zh": "毫米"}[self.config_data.language]
        return f"{value:.1f} {unit}"

    def _scheduler_tick(self):
        config = load_config()
        now = datetime.now()
        if config.enabled and config.latitude is not None and now.strftime("%H:%M") == config.send_time and self.last_sent_date != now.date().isoformat():
            self.last_sent_date = now.date().isoformat()
            self.notify_when_loaded = True
            self.fetch_weather()
        self.after(30_000, self._scheduler_tick)


if __name__ == "__main__":
    WeatherApp().mainloop()
