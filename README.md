[TOC]
#Plan: macOS 颈椎提醒 App（Python + rumps）

     Context

     在空目录中从零构建 macOS 菜单栏提醒 App，用户电脑有 Python 3 + Homebrew + Xcode CLT，无 Xcode。
     使用 Python + rumps（专为 macOS 菜单栏设计的库）+ pyobjc（访问原生 AppKit API）实现所有功能。

     技术栈

     - 语言: Python 3（已安装）
     - 菜单栏: rumps（macOS-only menu bar framework）
     - 原生 API: pyobjc-framework-Cocoa（用于 Overlay 窗口）
     - 横幅通知: osascript + subprocess（零依赖，无需权限申请）
     - 提示音: subprocess + afplay（macOS 内置命令行播放器）
     - 设置存储: JSON 文件（~/Library/Application Support/RemindApp/settings.json）
     - 无需 Xcode，python3 main.py 直接运行

     依赖安装

     pip3 install rumps pyobjc-framework-Cocoa

     ---
     文件结构

     remind_app/
     ├── main.py            ← rumps App 主类，菜单结构，所有回调
     ├── config.py          ← 读写 JSON 配置，提供默认值
     ├── reminder.py        ← 定时器逻辑（threading.Timer）
     ├── overlay.py         ← 全屏 Overlay 窗口（AppKit NSWindow via pyobjc）
     ├── notifier.py        ← 横幅通知（osascript）+ 声音（afplay）
     ├── templates.py       ← 7 个内置提示语模板
     ├── requirements.txt   ← rumps, pyobjc-framework-Cocoa
     └── launch.command     ← 双击即可运行的 shell 脚本（chmod +x）

     ---
     菜单结构（用户界面）

     🔔 RemindApp（菜单栏图标）
     ├── ✓ 启用提醒（toggle on/off）
     ├── ─────────────
     ├──   下次提醒: 14:32（倒计时，只读）
     ├── ─────────────
     ├── ⏰ 提醒间隔
     │   ├── 自定义间隔...（弹出输入框）
     │   ├── ─────────────
     │   ├── ● 5 分钟
     │   ├── ● 15 分钟
     │   ├── ● 30 分钟  ← 默认
     │   ├── ● 60 分钟
     │   └── ─ 单次提醒（toggle）
     ├── 💬 提示语
     │   ├── ✓ 随机模板（toggle）
     │   ├── 选择模板 ▶
     │   │   ├── 🧘 颈椎拉伸
     │   │   ├── 👁️ 眼部休息
     │   │   ├── 💧 喝水
     │   │   ├── 🚶 站起来走走
     │   │   ├── 🫁 深呼吸
     │   │   ├── 🤸 手腕拉伸
     │   │   └── 🙆 姿势检查
     │   └── 自定义文字...（弹出输入框）
     ├── 🔔 通知方式
     │   ├── ● 横幅通知（右上角）
     │   └── ○ 全屏遮罩（醒目打断）
     ├── 🔊 提示音
     │   ├── ✓ 启用声音（toggle）
     │   ├── ─────────────
     │   ├── ● Ping ← 默认
     │   ├── ○ Frog（可爱）
     │   ├── ○ Pop
     │   ├── ○ Bottle
     │   ├── ○ Tink
     │   └── ○ ... (共13个)
     ├── ─────────────
     ├── 🔍 测试提醒（立即触发一次）
     └── 退出

     ---
     关键模块实现

     config.py

     - 单例 Config 类，读写 ~/Library/Application Support/RemindApp/settings.json
     - 默认值：interval=30, recurring=True, enabled=False, notification=banner, sound=Ping, template=random

     reminder.py

     - ReminderManager 类，使用 threading.Timer 实现精确定时
     - start() / stop() / restart()
     - 单次模式：fire一次后自动停止
     - 循环模式：fire后重新 schedule 下一次
     - 通过回调函数通知 main.py 触发提醒

     notifier.py

     - 横幅通知：
     subprocess.run(['osascript', '-e',
         f'display notification "{msg}" with title "该休息啦 🔔"'])
     - 声音播放：
     subprocess.Popen(['afplay', f'/System/Library/Sounds/{name}.aiff'])

     overlay.py（关键，使用 pyobjc）

     - 创建全屏半透明 NSWindow（NSScreenSaverWindowLevel）
     - 窗口覆盖整个 NSScreen.mainScreen()
     - 内容：黑色半透明背景 + 居中白色面板（emoji + 消息文字 + "知道了"按钮）
     - 按钮点击/Escape 键关闭窗口
     - canJoinAllSpaces = True，在所有桌面可见

     main.py（rumps App）

     - RemindApp(rumps.App) 主类
     - @rumps.timer(1) 装饰器每秒更新倒计时菜单项
     - 所有菜单回调更新 Config 并调用 ReminderManager.restart()
     - 定时触发时：先播放声音，再发通知（横幅或 overlay）

     ---
     Overlay 窗口示意

     ████████████████████████████████████████
     █                                      █
     █    ┌──────────────────────────────┐  █
     █    │          🧘                  │  █  ← 大 emoji
     █    │                              │  █
     █    │   颈椎拉伸时间到了！          │  █  ← 白色大字
     █    │   慢慢左右摇头，放松一下。    │  █
     █    │                              │  █
     █    │       ╔══════════╗           │  █
     █    │       ║  知道了  ║           │  █  ← 按钮或 Esc 关闭
     █    │       ╚══════════╝           │  █
     █    └──────────────────────────────┘  █
     █                                      █  ← 黑色半透明背景
     ████████████████████████████████████████

     ---
     运行方式

     # 安装依赖
     pip3 install rumps pyobjc-framework-Cocoa

     # 运行
     python3 main.py

     # 或双击 launch.command 文件

     ---
     实现顺序

     1. requirements.txt + launch.command
     2. templates.py（纯数据，无依赖）
     3. config.py（读写 JSON）
     4. notifier.py（afplay + osascript）
     5. reminder.py（threading.Timer）
     6. overlay.py（pyobjc NSWindow）
     7. main.py（rumps App，整合所有模块）

     ---
     验证步骤

     1. pip3 install rumps pyobjc-framework-Cocoa 安装成功
     2. python3 main.py → 菜单栏出现 🔔 图标，Dock 无图标
     3. 点击图标 → 菜单展开，所有选项可见
     4. 启用提醒，设置 1 分钟间隔 → 等待横幅通知出现
     5. 切换为全屏遮罩模式 → 触发时全屏显示，点"知道了"关闭
     6. 切换不同声音 → 选择时即时预览播放
     7. 退出后重新运行 → 设置持久化（JSON 文件存在）


# 打包为 .app
使用 py2app 是最适合 rumps + pyobjc 的打包工具。

**第一步：安装 py2app**
```shell
pip3 install py2app
```

**第二步：创建 setup.py**
在你的项目根目录创建 setup.py：
```python
python from setuptools import setup

APP = ['your_app.py']  # 替换为你的主文件名
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,  # rumps 必须设为 False
    'packages': ['rumps'],
    'plist': {
        'LSUIElement': True,  # 菜单栏应用不在 Dock 显示
        'CFBundleName': '你的应用名',
        'CFBundleVersion': '1.0.0',
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
```

**第三步：执行打包**
```shell
# 开发模式（快，用于测试）
python setup.py py2app -A

# 正式打包（独立 .app，可分发）
python setup.py py2app
打包完成后 .app 在 dist/ 目录下。

```


# 打包为 .dmg
**方法一：使用 create-dmg（推荐）**

```shell
# 安装 create-dmg
brew install create-dmg

# 生成 dmg
create-dmg \
  --volname "你的应用名" \
  --window-size 500 300 \
  --icon-size 100 \
  --app-drop-link 350 150 \
  "你的应用名.dmg" \
  "dist/你的应用名.app"
```

**方法二：系统自带 hdiutil（简单）**
```shell
hdiutil create -volname "你的应用名" \
  -srcfolder dist/你的应用名.app \
  -ov -format UDZO \
  你的应用名.dmg
```

---


# 完整流程总结
```
写代码 → python setup.py py2app → dist/xxx.app
                                        ↓
                              create-dmg → xxx.dmg
                                        ↓
                                发给朋友安装使用
```
