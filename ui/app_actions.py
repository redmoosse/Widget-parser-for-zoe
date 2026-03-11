import os
import threading
from datetime import datetime
from PyQt6.QtWidgets import QColorDialog, QFileDialog
from PyQt6.QtCore import QDate, QTimer
from PyQt6.QtGui import QColor

from config import LOG_FILE
from core.audio import play_alert_sound
from core.tuya_api import TuyaAPI
from core.zoe_parser import run_zoe_parser

class ActionsMixin:
    def load_logs(self):
        if os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for line in lines[-50:]: 
                        self.log_display.append(line.strip())
                self.log_display.append("-" * 30)
            except Exception:
                pass

    def log_message(self, msg, alert=False):
        now = datetime.now()
        date_str = now.strftime('%d.%m %H:%M:%S')
        full_msg = f"[{date_str}] {msg}"
        self.log_display.append(full_msg)
        self.log_display.verticalScrollBar().setValue(self.log_display.verticalScrollBar().maximum())
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(full_msg + "\n")
        except Exception: pass

    def choose_bg_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Background Image", "", "Images (*.png *.jpg *.jpeg);;All Files (*)")
        if file_path:
            self.custom_bg_path = file_path
            self.le_bg_path.setText(os.path.basename(file_path))
            self.update_styles()
            self.save_settings()

    def clear_bg_file(self):
        self.custom_bg_path = ""
        self.le_bg_path.setText("")
        self.update_styles()
        self.save_settings()
        
    def trigger_alert_bg(self):
        if self.cb_bg_alert_only.isChecked() and getattr(self, 'custom_bg_path', ''):
            self.is_alerting_bg = True
            self.update_styles()
            QTimer.singleShot(3000, self.hide_alert_bg)

    def hide_alert_bg(self):
        self.is_alerting_bg = False
        self.update_styles()

    def choose_sound_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Alert Sound", "", "Audio Files (*.wav *.mp3);;All Files (*)")
        if file_path:
            self.custom_sound_path = file_path
            self.le_sound_path.setText(os.path.basename(file_path))
            self.save_settings()
            self.play_sound("time") 

    def clear_sound_file(self):
        self.custom_sound_path = ""
        self.le_sound_path.setText("")
        self.save_settings()

    def play_sound(self, sound_type):
        QTimer.singleShot(0, self.trigger_alert_bg)
        play_alert_sound(self.custom_sound_path, sound_type, self.signals.log)

    def _trigger_queue_debounce(self):
        if getattr(self, '_updating', True): return
        self.btn_fetch.setText("Updating...")
        self.queue_debounce_timer.start()

    def _auto_fetch_on_type(self):
        if self._updating: return
        self.save_settings()
        self.fetch_zoe_schedule(silent=True)

    def auto_fetch_zoe(self):
        if getattr(self, 'auto_update_zoe', False) and getattr(self, 'zoe_queue', '').strip():
            self.fetch_zoe_schedule(silent=True)

    def fetch_zoe_schedule(self, silent=False):
        queue = self.le_queue.text().strip()
        if not queue:
            if not silent: self.log_message("Enter the outage queue number.")
            return
            
        if not silent:
            self.btn_fetch.setEnabled(False)
            self.btn_fetch.setText("Wait...")
            self.btn_save.setEnabled(False)
            
        self.current_fetch_id += 1
        fetch_id = self.current_fetch_id
        threading.Thread(target=run_zoe_parser, args=(queue, silent, fetch_id, self.signals), daemon=True).start()

    def _apply_zoe_result(self, date_str, result_str, silent, fetch_id):
        if self.current_fetch_id != fetch_id: return
        
        if date_str == datetime.now().strftime('%Y-%m-%d'):
            fetched_qdate = QDate.fromString(date_str, 'yyyy-MM-dd')
            if self.custom_date_edit.date() != fetched_qdate:
                self._updating = True
                self.custom_date_edit.setDate(fetched_qdate)
                self._updating = False
            
        old_sched = self.custom_schedules.get(date_str, {}).get("text", "")
        old_enabled = self.custom_schedules.get(date_str, {}).get("enabled", False)
        
        self._updating = True
        
        if old_sched == result_str and old_enabled:
            if not silent: self.log_message(f"The outages on {date_str} has not changed.")
        else:
            if result_str == "":
                self.log_message(f"Outages not found on {date_str} (light!)")
            else:
                self.log_message(f"Updated {date_str}: {result_str}")
                
            self.custom_schedules[date_str] = {"enabled": True, "text": result_str}
            
        if self.custom_date_edit.date().toString('yyyy-MM-dd') == date_str:
            self.cb_custom.setChecked(True)
            self.le_custom.setText(result_str)
                
        self._updating = False
                
        self.save_settings()
        self.update_daily_schedule()
        self.update_live_timer()
            
        self.btn_fetch.setEnabled(True)
        self.btn_fetch.setText("Update now")
        self.btn_save.setEnabled(True)

    def _fail_zoe_result(self, msg, silent, fetch_id):
        if self.current_fetch_id != fetch_id: return
        
        self._updating = True
        self.le_custom.setText("Not found")
        self._updating = False
        
        if not silent:
            self.log_message(msg)
            
        self.btn_fetch.setEnabled(True)
        self.btn_fetch.setText("Update now")
        self.btn_save.setEnabled(True)

    def refresh_tuya_stats(self):
        if not getattr(self, 'tuya_enabled', False) or not self.tuya_id or not self.tuya_secret or not self.tuya_device:
            self.tuya_data_label.hide()
            self.tuya_time_label.hide()
            return
            
        self.tuya_data_label.show()
        self.tuya_time_label.show()
        
        try:
            if not self.tuya_token:
                r = TuyaAPI.get_token(self.tuya_region, self.tuya_id, self.tuya_secret)
                if r.get("success"): 
                    self.tuya_token = r["result"]["access_token"]
                    self.tuya_error_logged = False
                else: 
                    self.tuya_data_label.setText("API Auth Error")
                    if not self.tuya_error_logged:
                        self.log_message(f"Tuya Auth Error: {r.get('msg', 'Invalid keys')}")
                        self.tuya_error_logged = True
                    return

            r = TuyaAPI.get_status(self.tuya_region, self.tuya_id, self.tuya_secret, self.tuya_device, self.tuya_token)

            if r.get("success"):
                current_v, current_w = 0, 0
                for item in r["result"]:
                    if item["code"] in ["cur_voltage", "voltage"]: 
                        current_v = item["value"] / 10.0
                    if item["code"] in ["cur_power", "power", "active_power"]: 
                        current_w = item["value"] / 10.0
                
                if current_v != self.last_tuya_v or current_w != self.last_tuya_w:
                    self.last_tuya_v = current_v
                    self.last_tuya_w = current_w
                    
                    now_str = datetime.now().strftime("%H:%M:%S")
                    self.tuya_data_label.setText(f"Voltage: {current_v} V  |  Power: {current_w} W")
                    self.tuya_time_label.setText(f"Last Updated: {now_str}")
                    
                    log_msg = f"V: {current_v}V | P: {current_w}W"
                    
                    if current_v > 0 and (current_v < 180 or current_v > 270):
                        log_msg += " ⚠️ OUT OF BOUNDS!"
                        if not self.alerted_voltage:
                            self.play_sound("voltage")
                            self.alerted_voltage = True
                    else:
                        self.alerted_voltage = False
                        
                    self.log_message(log_msg)
            else:
                if r.get("code") == 1010:
                    self.tuya_token = None
        except Exception:
            pass 

    def choose_text_color(self):
        color = QColorDialog.getColor(QColor(self.text_color), self, "Choose Text Color")
        if color.isValid():
            self.text_color = color.name()
            self.update_styles()

    def toggle_tuya_container(self):
        self.tuya_expanded = not self.tuya_expanded
        self.tuya_container.setVisible(self.tuya_expanded)
        self.btn_tuya_toggle.setText("▼ Smart Plug (Tuya)" if self.tuya_expanded else "▶ Smart Plug (Tuya)")
        self.save_settings()

    def on_calendar_selection_changed(self):
        self.update_daily_schedule()

    def on_settings_date_changed(self):
        if getattr(self, '_updating', False): return
        self._updating = True
        selected_date_str = self.custom_date_edit.date().toString('yyyy-MM-dd')
        sched = self.custom_schedules.get(selected_date_str, {})
        self.cb_custom.setChecked(sched.get("enabled", False))
        self.le_custom.setText(sched.get("text", ""))
        self._updating = False

    def apply_settings_to_ui(self):
        self._updating = True
        self.slider_opacity.setValue(self.opacity_val)
        self.spin_font.setValue(self.font_size)
        self.spin_off.setValue(self.off_hours)
        self.spin_on.setValue(self.on_hours)
        self.dt_edit.setDateTime(self.start_point)
        
        if hasattr(self, 'custom_sound_path') and self.custom_sound_path:
            self.le_sound_path.setText(os.path.basename(self.custom_sound_path))
        else:
            self.le_sound_path.setText("")
            
        if hasattr(self, 'custom_bg_path') and self.custom_bg_path:
            self.le_bg_path.setText(os.path.basename(self.custom_bg_path))
        else:
            self.le_bg_path.setText("")
            
        if hasattr(self, 'bg_alert_only'):
            self.cb_bg_alert_only.setChecked(self.bg_alert_only)
            
        if hasattr(self, 'cb_use_math_mode'):
            self.cb_use_math_mode.setChecked(self.use_math_mode)
            
        self.cb_auto_zoe.setChecked(self.auto_update_zoe)
        self.spin_auto_interval.setValue(self.auto_update_interval)
        self.le_queue.setText(self.zoe_queue)
        
        self.cb_tuya.setChecked(self.tuya_enabled)
        self.le_tuya_region.setText(self.tuya_region)
        self.le_tuya_id.setText(self.tuya_id)
        self.le_tuya_secret.setText(self.tuya_secret)
        self.le_tuya_device.setText(self.tuya_device)
        self.btn_tuya_toggle.setText("▼ Smart Plug (Tuya)" if self.tuya_expanded else "▶ Smart Plug (Tuya)")
        self.tuya_container.setVisible(self.tuya_expanded)
        
        self.custom_date_edit.setDate(QDate.currentDate())
        
        self._updating = False
        self.on_settings_date_changed()
        self.on_calendar_selection_changed()

    def live_setting_update(self):
        if getattr(self, '_updating', True): return
        self.opacity_val = self.slider_opacity.value()
        self.font_size = self.spin_font.value()
        self.bg_alert_only = self.cb_bg_alert_only.isChecked()
        self.use_math_mode = self.cb_use_math_mode.isChecked()
        self.update_styles()
        self.update_daily_schedule()
        self.update_live_timer()

    def live_custom_update(self):
        if getattr(self, '_updating', True): return
        selected_date_str = self.custom_date_edit.date().toString('yyyy-MM-dd')
        self.custom_schedules[selected_date_str] = {
            "enabled": self.cb_custom.isChecked(),
            "text": self.le_custom.text()
        }
        self.update_daily_schedule()
        self.update_live_timer()

    def _trigger_debounce_save(self):
        if getattr(self, '_updating', True): return
        self.debounce_timer.start()

    def _apply_auto_update_changes(self):
        if self._updating: return
        self.auto_update_zoe = self.cb_auto_zoe.isChecked()
        self.auto_update_interval = self.spin_auto_interval.value()
        
        if self.auto_update_zoe:
            self.zoe_auto_timer.start(self.auto_update_interval * 60000)
        else:
            self.zoe_auto_timer.stop()
            
        self.save_settings()
        self.log_message(f"Auto-update set to {self.auto_update_interval} min.")