import os
import json
from pathlib import Path

# アプリケーションID
APP_ID = 'dock.ams.f5.si'

# --- デフォルト設定 ---
DEFAULT_CONFIG = {
    "DOCK_HEIGHT": 60,
    "RADIUS_RATIO": 0.5,
    "WIDTH_RATIO": 1.0,
    "CONTROL_RATIO": 0.8,
    "LAUNCHER_CMD": "rofi -show drun",
    "ANIMATION_ENABLED": True,
    "ANIMATION_DURATION": 800,
    "ANIMATION_EASING": "ease_out_back",
    "COLORS": {
        "light": {
            "bg": "rgba(255, 255, 255, 0.85)",
            "text": "#333333",
            "hover": "rgba(0,0,0,0.05)"
        },
        "dark": {
            "bg": "rgba(35, 35, 35, 0.9)",
            "text": "#ffffff",
            "hover": "rgba(255,255,255,0.1)"
        }
    }
}

# 設定ファイルの保存先 (~/.config/gtk-shelf-x11/config.json)
CONFIG_DIR = Path.home() / ".config" / "gtk-shelf-x11"
CONFIG_FILE = CONFIG_DIR / "config.json"

def load_config():
    """設定ファイルを読み込む。無ければデフォルト値を返す。"""
    config_data = DEFAULT_CONFIG.copy()
    
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                
                # デフォルト設定をユーザー設定で上書き
                for key, value in user_config.items():
                    # COLORSみたいなネストした辞書の処理
                    if isinstance(value, dict) and key in config_data and isinstance(config_data[key], dict):
                        config_data[key].update(value)
                    else:
                        config_data[key] = value
        except Exception as e:
            print(f"設定ファイルの読み込みに失敗したよ: {e}")
            print("デフォルト設定を使うね。")
    else:
        # ファイルがない場合は初回起動とみなしてファイルを作成
        save_config(config_data)
        
    return config_data

def save_config(config_data):
    """設定をJSONファイルとして保存する"""
    try:
        # ディレクトリが無ければ作る
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"設定ファイルの保存に失敗したよ: {e}")

# モジュール読み込み時に設定を展開する
# こうすることで、他のファイルから `config.DOCK_HEIGHT` のようにアクセスできるよ！
_current_config = load_config()
for key, value in _current_config.items():
    globals()[key] = value