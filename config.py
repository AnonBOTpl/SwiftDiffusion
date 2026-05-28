import logging
import configparser
import os
import json

# --- LOGGING CONFIG ---
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger("SD-Controller")

class SettingsManager:
    DEFAULT_CONFIG = {
        'Paths': {
            'models_sd': 'models/stable_diffusion',
            'models_lora': 'models/lora',
            'models_controlnet': 'models/controlnet',
            'models_inpaint': 'models/inpaint',
            'models_vae': 'models/vae',
            'models_facerestore': 'models/facerestore',
            'models_facedetection': 'models/facedetection',
            'models_upscalers': 'models/upscalers',
            'models_embeddings': 'models/embeddings',
            'output_txt2img': 'output/txt2img',
            'output_inpaint': 'output/inpaint',
            'output_controlnet': 'output/controlnet',
            'output_upscaled': 'output/upscaled',
            'docs': 'docs'
        },
        'UI': {
            'theme': 'Dark',
            'accent_color': '#00d4ff',
            'language': 'pl'
        },
        'Generation': {
            'default_sampler': 'DPM++ 2M',
            'default_scheduler': 'Normal',
            'default_vae': 'Domyślne (z modelu)'
        },
        'Performance': {
            'vram_slicing': 'False',
            'attention_slicing': 'False',
            'cpu_offload': 'False',
            'auto_clear_vram': 'False',
            'tiled_vae': 'False'
        },
        'Preview': {
            'enabled': 'False',
            'interval': '5'
        },
        'Integration': {
            'hf_token': '',
            'civitai_api_key': ''
        }
    }

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
            self.config.read(self.filename, encoding="utf-8-sig")
            self.validate_and_heal()

    def set_defaults(self):
        for section, keys in self.DEFAULT_CONFIG.items():
            self.config[section] = keys

    def validate_and_heal(self):
        requires_save = False
        for section, keys in self.DEFAULT_CONFIG.items():
            if section not in self.config:
                self.config[section] = {}
                requires_save = True
            for key, value in keys.items():
                if key not in self.config[section]:
                    self.config[section][key] = value
                    requires_save = True

        if requires_save:
            logger.info(f"[SYSTEM] Detected configuration gaps. Repairing file {self.filename}...")
            self.save()

    def save(self):
        with open(self.filename, 'w', encoding='utf-8-sig') as configfile:
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
                logger.error(f"[SYSTEM] Error loading language {lang}: {e}")
                self.data = {}
        else:
            self.data = {}

    def tr(self, key):
        return self.data.get(key, key)

translator = Translator()
tr = translator.tr

THEMES = {
    "Dark": {
        "accent": "#00d4ff",
        "bg": "#121212", "sidebar_bg": "#1e1e1e", "sidebar_start": "#252525", "sidebar_end": "#1a1a1a",
        "control_bg": "#252525", "text_color": "#e0e0e0", "sec_text": "#888",
        "border": "#333333", "hover": "#444444", "view_bg": "#1a1a1a", "combo_view_bg": "#252525",
        "scroll_handle": "#444444", "scroll_hover": "#666666",
    },
    "Amber": {
        "accent": "#ff8c00",
        "bg": "#1a1510", "sidebar_bg": "#221c14", "sidebar_start": "#2a2218", "sidebar_end": "#1a1510",
        "control_bg": "#2a2218", "text_color": "#e0d5c0", "sec_text": "#8a7a60",
        "border": "#4a3a28", "hover": "#3a2e1e", "view_bg": "#221c14", "combo_view_bg": "#2a2218",
        "scroll_handle": "#4a3a28", "scroll_hover": "#6a5a48",
    },
    "Nord": {
        "accent": "#88c0d0",
        "bg": "#1e2229", "sidebar_bg": "#252a32", "sidebar_start": "#2e3440", "sidebar_end": "#232831",
        "control_bg": "#2e3440", "text_color": "#d8dee9", "sec_text": "#7b88a1",
        "border": "#3b4252", "hover": "#434c5e", "view_bg": "#252a32", "combo_view_bg": "#2e3440",
        "scroll_handle": "#3b4252", "scroll_hover": "#5e6a82",
    },
    "Dracula": {
        "accent": "#bd93f9",
        "bg": "#1e1e2e", "sidebar_bg": "#262640", "sidebar_start": "#2d2d4a", "sidebar_end": "#1e1e2e",
        "control_bg": "#2d2d4a", "text_color": "#f8f8f2", "sec_text": "#9088b8",
        "border": "#44446a", "hover": "#3a3a5a", "view_bg": "#262640", "combo_view_bg": "#2d2d4a",
        "scroll_handle": "#44446a", "scroll_hover": "#6666a0",
    },
    "Monokai": {
        "accent": "#a6e22e",
        "bg": "#1a1a1a", "sidebar_bg": "#222222", "sidebar_start": "#2d2d2d", "sidebar_end": "#1a1a1a",
        "control_bg": "#2d2d2d", "text_color": "#e6e6e6", "sec_text": "#888888",
        "border": "#444444", "hover": "#3a3a3a", "view_bg": "#222222", "combo_view_bg": "#2d2d2d",
        "scroll_handle": "#444444", "scroll_hover": "#666666",
    },
    "Forest": {
        "accent": "#4caf50",
        "bg": "#0f1a12", "sidebar_bg": "#142618", "sidebar_start": "#1a3020", "sidebar_end": "#0f1a12",
        "control_bg": "#1a3020", "text_color": "#d4e0d4", "sec_text": "#6a8a6a",
        "border": "#2a4a34", "hover": "#1e3826", "view_bg": "#142618", "combo_view_bg": "#1a3020",
        "scroll_handle": "#2a4a34", "scroll_hover": "#4a6a54",
    },
    "Ocean": {
        "accent": "#42a5f5",
        "bg": "#0d1820", "sidebar_bg": "#122230", "sidebar_start": "#183040", "sidebar_end": "#0d1820",
        "control_bg": "#183040", "text_color": "#d0e0ee", "sec_text": "#6888a0",
        "border": "#284860", "hover": "#1c3850", "view_bg": "#122230", "combo_view_bg": "#183040",
        "scroll_handle": "#284860", "scroll_hover": "#4878a0",
    },
}

def get_style(theme_name="Dark", accent_color="#00d4ff"):
    if theme_name not in THEMES:
        theme_name = "Dark"
    t = THEMES[theme_name]

    def lighten(hex_color, amount=0.3):
        r = min(255, int(int(hex_color[1:3], 16) + (255 - int(hex_color[1:3], 16)) * amount))
        g = min(255, int(int(hex_color[3:5], 16) + (255 - int(hex_color[3:5], 16)) * amount))
        b = min(255, int(int(hex_color[5:7], 16) + (255 - int(hex_color[5:7], 16)) * amount))
        return f"#{r:02x}{g:02x}{b:02x}"

    bg = t["bg"]; sidebar_bg = t["sidebar_bg"]; control_bg = t["control_bg"]
    text_color = t["text_color"]; sec_text = t["sec_text"]; border = t["border"]
    hover = t["hover"]; view_bg = t["view_bg"]; combo_view_bg = t["combo_view_bg"]
    scroll_handle = t["scroll_handle"]; scroll_hover = t["scroll_hover"]
    accent_light = lighten(accent_color)

    return f"""
    QMainWindow {{ background-color: {bg}; }}
    QTabWidget::pane {{ border: none; background-color: {bg}; }}
    QTabBar::tab {{ background: {sidebar_bg}; color: {sec_text}; padding: 12px 40px; font-weight: bold; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; font-size: 14px; }}
    QTabBar::tab:selected {{ background: {bg}; color: {accent_color}; border-bottom: 2px solid {accent_color}; }}
    QTabBar::tab:hover {{ background: {hover}; }}
    QWidget {{ color: {text_color}; font-family: 'Segoe UI', sans-serif; font-size: 13px; }}
    QFrame#Sidebar {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {t['sidebar_start']}, stop:1 {t['sidebar_end']}); border-right: 1px solid {border}; min-width: 300px; max-width: 300px; }}
    QLabel#Header {{ font-size: 16px; font-weight: bold; color: {accent_color}; margin-top: 10px; margin-bottom: 5px; }}
    QLineEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{ background-color: {control_bg}; border: 1px solid {border}; border-radius: 4px; padding: 6px; selection-background-color: {accent_color}; }}
    QLineEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{ border: 1px solid {accent_color}; }}
    QSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{ width: 0px; background: transparent; }}
    QPushButton {{ background-color: {hover}; border: 1px solid {border}; border-radius: 4px; padding: 8px; font-weight: bold; }}
    QPushButton:hover {{ background-color: {hover}; border-color: {accent_color}; }}
    QPushButton:pressed {{ background-color: {accent_color}; color: #121212; }}
    QPushButton#GenerateBtn {{ background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {accent_light}, stop:1 {accent_color}); color: #121212; font-size: 15px; margin-top: 5px; border: none; font-weight: bold; border-radius: 6px; }}
    QPushButton#GenerateBtn:hover {{ background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {accent_color}, stop:1 {accent_light}); border: 1px solid {accent_light}; }}
    QPushButton#GenerateBtn:pressed {{ background-color: {accent_light}; }}
    QPushButton#SecondaryBtn {{ background-color: transparent; border: 1px solid {border}; color: {accent_color}; font-size: 11px; padding: 4px; }}
    QPushButton#SecondaryBtn:hover {{ border-color: {accent_color}; background-color: rgba(0,0,0,0.1); }}
    QPushButton#ActionBtn {{ background-color: {sidebar_bg}; border: 1px solid {accent_color}; color: {accent_color}; padding: 8px 20px; font-size: 12px; font-weight: bold; }}
    QPushButton#ActionBtn:hover {{ background-color: {accent_color}; color: #121212; }}
    QPushButton#CopyBtn {{ background-color: transparent; border: none; color: {accent_color}; font-size: 11px; text-decoration: underline; padding: 2px; }}
    QCheckBox::indicator {{ width: 16px; height: 16px; background-color: {control_bg}; border: 1px solid {border}; border-radius: 3px; }}
    QCheckBox::indicator:checked {{ background-color: {accent_color}; }}
    QCheckBox::indicator:hover {{ border-color: {accent_color}; }}
    QSlider::groove:horizontal {{ border: 1px solid {border}; height: 4px; background: {control_bg}; margin: 2px 0; border-radius: 2px; }}
    QSlider::handle:horizontal {{ background: {accent_color}; border: 1px solid {accent_color}; width: 12px; height: 12px; margin: -4px 0; border-radius: 6px; }}
    QSlider::handle:horizontal:hover {{ background: {accent_light}; border-color: {accent_light}; }}
    QProgressBar {{ background-color: {sidebar_bg}; border: none; height: 8px; text-align: center; border-radius: 4px; }}
    QProgressBar::chunk {{ background-color: {accent_color}; border-radius: 4px; }}
    QListWidget {{ background-color: {control_bg}; border-radius: 8px; }}
    QListWidget::item:hover {{ background-color: {hover}; }}
    QScrollArea {{ background-color: {view_bg}; border: none; }}
    QLabel#PreviewArea {{ background-color: {view_bg}; border-radius: 12px; }}
    QComboBox QAbstractItemView {{ background-color: {combo_view_bg}; color: {text_color}; border: none; selection-background-color: {accent_color}; }}
    QComboBox::item:hover {{ background-color: {hover}; }}
    QScrollBar:vertical {{ background: transparent; width: 8px; margin: 0; }}
    QScrollBar::handle:vertical {{ background: {scroll_handle}; min-height: 30px; border-radius: 4px; }}
    QScrollBar::handle:vertical:hover {{ background: {scroll_hover}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar:horizontal {{ background: transparent; height: 8px; margin: 0; }}
    QScrollBar::handle:horizontal {{ background: {scroll_handle}; min-width: 30px; border-radius: 4px; }}
    QScrollBar::handle:horizontal:hover {{ background: {scroll_hover}; }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
    QTreeWidget {{ background-color: {control_bg}; border: 1px solid {border}; border-radius: 4px; }}
    QTreeWidget::item:hover {{ background-color: {hover}; }}
    QTreeWidget::item:selected {{ background-color: {accent_color}; color: #121212; }}
    """

# derive FOLDERS from settings for initialization
def get_folders():
    return list(settings.config['Paths'].values())

FOLDERS = get_folders()
