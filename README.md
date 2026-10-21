# Weather Desktop Tool

Кроссплатформенное приложение с настраиваемой светлой и тёмной темой, поиском городов со странами и интерактивной картиной погоды на день. Данные прогноза предоставляет Open-Meteo.

## Самый простой способ для пользователя

Пользователю не нужны Python, командная строка или установка зависимостей.

1. Откройте страницу **Releases** в GitHub-репозитории.
2. Скачайте файл для своей системы:
   - Windows: `WeatherDesktopTool-windows.exe`;
   - macOS: `WeatherDesktopTool-macos.zip`;
   - Linux: `WeatherDesktopTool-linux`.
3. Запустите файл.
4. Выберите город из списка, настройте время сводки и тему.

При первом запуске приложение само создаёт файл настроек. Для ежедневной работы его нужно добавить в автозапуск ОС; отдельные инструкции приведены ниже.

Готовые файлы появляются автоматически после публикации GitHub Release. Их собирает workflow `Build release`; Python конечному пользователю не требуется.

## Автозапуск готовой версии

### Windows

1. Нажмите `Win+R`, введите `shell:startup` и нажмите Enter.
2. Создайте ярлык на `WeatherDesktopTool-windows.exe` в открывшейся папке.

### macOS

1. Распакуйте `WeatherDesktopTool-macos.zip` и переместите приложение в `Applications`.
2. Откройте **System Settings → General → Login Items**.
3. Нажмите `+` и добавьте `WeatherDesktopTool`.

### Linux

Создайте файл `~/.config/autostart/weather-desktop-tool.desktop`, заменив путь на настоящий:

```ini
[Desktop Entry]
Type=Application
Name=Weather Desktop Tool
Exec=/полный/путь/WeatherDesktopTool-linux
Terminal=false
X-GNOME-Autostart-enabled=true
```

## Возможности

- Windows, macOS и Linux (нужны Python 3.10+ и Tkinter).
- Поиск города с вариантами страны и региона.
- Переключение языка интерфейса: русский, английский и китайский.
- График температуры и вероятности осадков, почасовой прогноз, сводка на утро/день/вечер.
- Наведите курсор на точку графика, чтобы увидеть подробный прогноз на выбранный час.
- Дождь, ливни, снег и грозовые коды; предупреждение о граде помечено как модельный сигнал/оценка риска.
- Переключение тёмной и светлой темы, сохранение выбранного города и настроек.
- Ежедневная сводка во время работы приложения. Приложение должно быть открыто в установленное время.
- Сохранение настроек в домашней папке пользователя.
- Open-Meteo Geocoding API и Forecast API, без API-ключа для личного использования.

Град не имеет отдельной почасовой вероятности в используемом API. Поэтому приложение показывает грозовые коды, для которых модель указывает грозу с градом, или отдельно сообщает, что прямых данных о граде нет. Это не предупреждение метеослужбы.

## Запуск из исходников для разработчиков

Для обычных пользователей используйте готовый файл из раздела Releases. Инструкции ниже нужны разработчикам, которые запускают проект из исходников.

### Windows из исходников

1. Установите Python 3.10 или новее с сайта [python.org](https://www.python.org/downloads/). Во время установки включите **Add Python to PATH**.
2. Скачайте репозиторий через **Code → Download ZIP** и распакуйте архив.
3. Откройте PowerShell в папке проекта и выполните:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Если окно открылось, укажите город, время и нажмите «Сохранить настройки».

Для автозапуска после входа в Windows выполните в PowerShell из папки проекта:

```powershell
$project = (Get-Location).Path
$python = Join-Path $project '.venv\Scripts\pythonw.exe'
$startup = [Environment]::GetFolderPath('Startup')
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut((Join-Path $startup 'Weather Desktop Tool.lnk'))
$shortcut.TargetPath = $python
$shortcut.Arguments = "`"$project\app.py`""
$shortcut.WorkingDirectory = $project
$shortcut.Save()
```

После этого приложение будет запускаться автоматически при входе пользователя в Windows. Чтобы убрать автозапуск, удалите ярлык `Weather Desktop Tool.lnk` из папки автозагрузки.

### macOS из исходников

Установите Python 3.10 или новее с [python.org](https://www.python.org/downloads/macos/) или через Homebrew. Затем в Terminal перейдите в папку проекта и выполните:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Для автозапуска создайте LaunchAgent. Сначала замените `/полный/путь/weather-desktop-tool` в командах ниже на настоящий путь к проекту:

```bash
PROJECT="/полный/путь/weather-desktop-tool"
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$HOME/Library/LaunchAgents/com.weather.desktop.tool.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.weather.desktop.tool</string>
  <key>ProgramArguments</key><array>
    <string>$PROJECT/.venv/bin/python</string><string>$PROJECT/app.py</string>
  </array>
  <key>WorkingDirectory</key><string>$PROJECT</string>
  <key>RunAtLoad</key><true/>
</dict></plist>
EOF
launchctl load "$HOME/Library/LaunchAgents/com.weather.desktop.tool.plist"
```

### Linux из исходников

Установите Python и Tkinter. Например, в Ubuntu/Debian:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-tk
```

Затем установите и запустите приложение:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Для автозапуска через systemd user service замените `/полный/путь/weather-desktop-tool` на настоящий путь к проекту:

```bash
PROJECT="/полный/путь/weather-desktop-tool"
mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/weather-desktop-tool.service" <<EOF
[Unit]
Description=Weather Desktop Tool
After=graphical-session.target

[Service]
WorkingDirectory=$PROJECT
ExecStart=$PROJECT/.venv/bin/python $PROJECT/app.py
Restart=on-failure

[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload
systemctl --user enable --now weather-desktop-tool.service
```

Проверить состояние можно командой `systemctl --user status weather-desktop-tool.service`.

## Запуск вручную из исходников

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Оставьте приложение запущенным, чтобы ежедневное уведомление сработало. Подробные инструкции по автозапуску для Windows, macOS и Linux приведены выше.

## Публикация на GitHub

Содержимое этой папки можно загрузить в новый публичный репозиторий:

```bash
git init
git add .
git commit -m "Initial weather desktop tool"
git branch -M main
git remote add origin https://github.com/USERNAME/weather-desktop-tool.git
git push -u origin main
```

После этого создайте версию, чтобы GitHub собрал готовые файлы:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Через несколько минут файлы появятся в разделе **Releases**. После следующих изменений используйте новый тег, например `v1.0.1`.

## Лицензия

MIT — см. `LICENSE`.
