"""通知和声音管理"""

import subprocess
import os

SOUND_DIR = "/System/Library/Sounds"

SOUNDS = [
    "None",
    "Basso",
    "Bottle",
    "Frog",
    "Funk",
    "Glass",
    "Hero",
    "Morse",
    "Ping",
    "Pop",
    "Purr",
    "Sosumi",
    "Submarine",
    "Tink",
]


def play_sound(name: str):
    """播放 macOS 系统声音"""
    if name == "None":
        return
    path = os.path.join(SOUND_DIR, f"{name}.aiff")
    if os.path.exists(path):
        subprocess.Popen(
            ["afplay", path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def send_banner(title: str, message: str):
    """通过 osascript 发送系统横幅通知（右上角）"""
    # 转义引号避免 AppleScript 注入
    safe_title = title.replace('"', '\\"')
    safe_message = message.replace('"', '\\"')
    script = f'display notification "{safe_message}" with title "{safe_title}"'
    subprocess.Popen(
        ["osascript", "-e", script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
