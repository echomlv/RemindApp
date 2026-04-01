"""通知和声音管理"""

import subprocess
import os
import re

# TTS 音色列表（macOS 内置，适合中文提示语）
TTS_VOICES = [
    ("Tingting", "婷婷 · 普通话"),   # 亲切女声，推荐
    ("Meijia",   "美佳 · 台湾"),     # 台湾腔女声
    ("Sinji",    "新智 · 粤语"),     # 粤语女声
]
TTS_VOICE_KEYS = [v[0] for v in TTS_VOICES]

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


_EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002700-\U000027BF"
    "\U0001F900-\U0001F9FF"
    "]+",
    flags=re.UNICODE,
)


def speak_text(text: str, voice: str = "Tingting"):
    """用 macOS say 命令 TTS 播放提示语（可爱俏皮音色）"""
    # 去除 emoji，say 命令会把 emoji 读成英文单词，体验差
    clean = _EMOJI_RE.sub("", text).strip()
    if not clean:
        clean = text
    subprocess.Popen(
        ["say", "-v", voice, "-r", "185", clean],
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
