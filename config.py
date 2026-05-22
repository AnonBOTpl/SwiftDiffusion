import logging
import configparser
import os
import json

# --- LOGGING CONFIG ---
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger("SD-Controller")

class SettingsManager:
    def __init__(self, filename="settings.ini"):
        self.filename = filename
        self.is_first_run = not os.path.exists(self.filename)
        self.config = configparser.ConfigParser()
        self.load()

    def load(self):
        if self.is_first_run:
            self.set_defaults()
            self.save()
        else:
            self.config.read(self.filename, encoding="utf-8")

    def set_defaults(self):
        self.config['Paths'] = {
            'models_sd': 'models/stable_diffusion',
            'models_lora': 'models/lora',
            'models_controlnet': 'models/controlnet',
            'models_inpaint': 'models/inpaint',
            'models_upscalers': 'models/upscalers',
            'output_txt2img': 'output/txt2img',
            'output_inpaint': 'output/inpaint',
            'output_controlnet': 'output/controlnet',
            'output_upscaled': 'output/upscaled',
            'docs': 'docs'
        }
        self.config['UI'] = {
            'theme': 'dark',
            'accent_color': '#00d4ff',
            'language': 'pl'
        }
        self.config['Generation'] = {
            'default_sampler': 'DPM++ 2M',
            'default_scheduler': 'Normal'
        }
        self.config['Performance'] = {
            'vram_slicing': 'False',
            'attention_slicing': 'False',
            'cpu_offload': 'False',
            'auto_clear_vram': 'False'
        }

    def save(self):
        with open(self.filename, 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)

    def get(self, section, key, fallback=None):
        return self.config.get(section, key, fallback=fallback)

    def get_bool(self, section, key, fallback=False):
        return self.config.getboolean(section, key, fallback=fallback)

    def set(self, section, key, value):
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = str(value)

    def export_settings(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            self.config.write(f)

    def import_settings(self, path):
        self.config.read(path, encoding="utf-8")
        self.save()

# Global settings instance
settings = SettingsManager()

class Translator:
    def __init__(self):
        self.data = {}
        self.load()

    def load(self):
        lang = settings.get('UI', 'language', fallback='pl')
        path = f"locales/{lang}.json"
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except Exception as e:
                logger.error(f"[SYSTEM] Błąd ładowania języka {lang}: {e}")
                self.data = {}
        else:
            self.data = {}

    def tr(self, key):
        return self.data.get(key, key)

translator = Translator()
tr = translator.tr

def get_style(accent_color="#00d4ff", is_dark_mode=True):
    if is_dark_mode:
        bg = "#121212"
        sidebar_bg = "#1e1e1e"
        control_bg = "#252525"
        text_color = "#e0e0e0"
        sec_text = "#888"
        border = "#333333"
        hover = "#444444"
        view_bg = "#1a1a1a"
        combo_view_bg = "#252525"
    else:
        bg = "#f5f5f5"
        sidebar_bg = "#e0e0e0"
        control_bg = "#ffffff"
        text_color = "#121212"
        sec_text = "#555"
        border = "#cccccc"
        hover = "#dddddd"
        view_bg = "#e8e8e8"
        combo_view_bg = "#ffffff"

    return f"""
    QMainWindow {{ background-color: {bg}; }}
    QTabWidget::pane {{ border: none; background-color: {bg}; }}
    QTabBar::tab {{ background: {sidebar_bg}; color: {sec_text}; padding: 12px 40px; font-weight: bold; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; font-size: 14px; }}
    QTabBar::tab:selected {{ background: {bg}; color: {accent_color}; border-bottom: 2px solid {accent_color}; }}
    QTabBar::tab:hover {{ background: {hover}; }}
    QWidget {{ color: {text_color}; font-family: 'Segoe UI', sans-serif; font-size: 13px; }}
    QFrame#Sidebar {{ background-color: {sidebar_bg}; border-right: 1px solid {border}; min-width: 300px; max-width: 300px; }}
    QLabel#Header {{ font-size: 16px; font-weight: bold; color: {accent_color}; margin-top: 10px; margin-bottom: 5px; }}
    QLineEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{ background-color: {control_bg}; border: 1px solid {border}; border-radius: 4px; padding: 6px; selection-background-color: {accent_color}; }}
    QLineEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{ border: 1px solid {accent_color}; }}
    QSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{ width: 0px; background: transparent; }}
    QPushButton {{ background-color: {hover}; border: 1px solid {border}; border-radius: 4px; padding: 8px; font-weight: bold; }}
    QPushButton:hover {{ background-color: {hover}; border-color: {accent_color}; }}
    QPushButton#GenerateBtn {{ background-color: {accent_color}; color: #121212; font-size: 15px; margin-top: 5px; }}
    QPushButton#SecondaryBtn {{ background-color: transparent; border: 1px solid {border}; color: {accent_color}; font-size: 11px; padding: 4px; }}
    QPushButton#ActionBtn {{ background-color: {sidebar_bg}; border: 1px solid {accent_color}; color: {accent_color}; padding: 8px 20px; font-size: 12px; font-weight: bold; }}
    QPushButton#ActionBtn:hover {{ background-color: {accent_color}; color: #121212; }}
    QPushButton#CopyBtn {{ background-color: transparent; border: none; color: {accent_color}; font-size: 11px; text-decoration: underline; padding: 2px; }}
    QCheckBox::indicator {{ width: 16px; height: 16px; background-color: {control_bg}; border: 1px solid {border}; border-radius: 3px; }}
    QCheckBox::indicator:checked {{ background-color: {accent_color}; }}
    QSlider::groove:horizontal {{ border: 1px solid {border}; height: 4px; background: {control_bg}; margin: 2px 0; border-radius: 2px; }}
    QSlider::handle:horizontal {{ background: {accent_color}; border: 1px solid {accent_color}; width: 12px; height: 12px; margin: -4px 0; border-radius: 6px; }}
    QProgressBar {{ background-color: {sidebar_bg}; border: none; height: 4px; text-align: center; }}
    QProgressBar::chunk {{ background-color: {accent_color}; }}
    QListWidget {{ background-color: {control_bg}; border-radius: 8px; }}
    QScrollArea {{ background-color: {view_bg}; border: none; }}
    QLabel#PreviewArea {{ background-color: {view_bg}; border-radius: 12px; }}
    QComboBox QAbstractItemView {{ background-color: {combo_view_bg}; color: {text_color}; border: none; selection-background-color: {accent_color}; }}
    """

# derive FOLDERS from settings for initialization
def get_folders():
    return list(settings.config['Paths'].values())

FOLDERS = get_folders()
