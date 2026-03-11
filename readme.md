# ⚡ Power widget

A desktop application built with **Python** and **PyQt6** designed to monitor and manage power outage schedules. It intelligently combines real-time data scraping from local utility providers with a mathematical cyclic fallback system.

## 🚀 How to Run on System Startup (Windows)

To make the widget launch automatically every time you turn on your PC:

1. **Compile the App:** First, compile the application into a single executable file using PyInstaller, or just download last release (`PowerSchedule.exe`).
2. **Open Startup Folder:** Press `Win + R` on your keyboard to open the "Run" dialog.
3. **Enter Command:** Type `shell:startup` and press **Enter**. A file explorer window will open.
4. **Create Shortcut:** Create a shortcut of your `PowerSchedule.exe` file and move this shortcut into the opened Startup folder.

That's it! The application will now start seamlessly in the background with your customized settings upon every boot.

## 📸 Screenshots

<div align="center">
  <img width="363" height="688" alt="image" src="https://github.com/user-attachments/assets/9e185fc8-fa36-4995-b471-2e371b058c6b" />
  <img width="362" height="682" alt="image" src="https://github.com/user-attachments/assets/0b94d550-3e56-4579-b0b3-91e59b071f73" />
  <img width="352" height="675" alt="image" src="https://github.com/user-attachments/assets/ff94e5e4-5062-4a94-810b-9fc529464619" />
  <img width="371" height="689" alt="image" src="https://github.com/user-attachments/assets/24eecc4e-7902-4211-a5e9-0ae138b32368" />
  <img width="368" height="691" alt="image" src="https://github.com/user-attachments/assets/7aefd085-c559-4eea-9d99-15f12ff8d64a" />
  <img width="362" height="682" alt="image" src="https://github.com/user-attachments/assets/d21d8fba-f81a-4636-95f6-8e1f9639485a" />
  <img width="369" height="692" alt="image" src="https://github.com/user-attachments/assets/ed8cecbe-e16b-4623-a5b0-4ee4b0442f70" />
  <img width="367" height="678" alt="image" src="https://github.com/user-attachments/assets/3b7bc472-582c-411f-bf47-367a5ebc8ef5" />
  <img width="275" height="157" alt="image" src="https://github.com/user-attachments/assets/34c0747b-dfdb-48b5-b0fe-9bcdc69e9f94" />
</div>

## 🚀 Key Features

### 📅 Hybrid Scheduling System
* **Utility Parser:** Scrapes the latest stabilization schedules directly from the provider (Zaporizhzhiaoblenergo/ZOE) using an intelligent line-counting algorithm to prevent data duplication and ignore outdated posts.
* **Custom Calendar:** Manually input specific hours for specific dates.
* **Auto-Calendar:** A fallback mode that calculates recurring "OFF/ON" cycles based on a user-defined start point and durations.
* **Unified Calendar:** A clean visualization that displays exclusively **OFF** periods to reduce visual clutter.

### 🔌 Smart Home Integration (Tuya API)
* **Real-time Monitoring:** Connects to Tuya-compatible smart plugs to track voltage and power consumption.
* **Hardware Protection:** Configurable alerts for "Out of Bounds" voltage levels (e.g., `<180V` or `>270V`) to protect sensitive electronics.
* **Automated Auth:** Handles HMAC-SHA256 signature generation and token refreshing for secure API communication.

### 🎨 Advanced UI/UX
* **Compact & Expandable:** Frameless, translucent window that stays on top and can be dragged/resized.
* **Full Customization:** Adjust background opacity, font sizes, text colors, and custom background images.
* **Alert System:** Auditory (MP3/WAV/Beep) and visual notifications 5 minutes before scheduled outages.

---

## 🛠 Tech Stack
* **UI Framework:** PyQt6
* **Web Scraping:** BeautifulSoup4, Requests
* **Hardware API:** Tuya Open IoT Platform (HMAC-SHA256 Authentication)
* **Audio:** Pygame, Winsound
* **Architecture:** Modular Mixin-based design

---

## 📂 Project Structure
The project is organized into modular packages for maintainability:
```text
📁 power_schedule_app
 ├── 📄 main.py            # Entry point & Class assembly
 ├── 📄 config.py          # Path management
 ├── 📁 core               # Logic Layer
 │    ├── audio.py         # Background audio processing
 │    ├── tuya_api.py      # Secure API requests
 │    └── zoe_parser.py    # BeautifulSoup scraping logic
 └── 📁 ui                 # Interface Layer
      ├── ui_setup.py      # CSS & Widget initialization
      ├── settings.py      # IO for user preferences
      ├── schedule_logic.py# Time-math & filtering
      └── app_actions.py   # Signal handling & Mixins

power_schedule.log: Local history of your device statistics.

📝 Disclaimer
This tool is intended for personal use. It relies on scraping public websites; changes to the utility provider's website structure may require updates to the parsing logic in core/zoe_parser.py.


