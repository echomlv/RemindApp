"""
py2app 打包配置
使用方式:
    python3 setup.py py2app          # 构建 .app
    python3 setup.py py2app --alias  # 开发模式（快速，使用符号链接）
"""

from setuptools import setup

APP = ["main.py"]
DATA_FILES = []
OPTIONS = {
    # 菜单栏 App 不需要 argv_emulation
    "argv_emulation": False,
    # Info.plist 配置
    "plist": {
        "CFBundleName": "RemindApp",
        "CFBundleDisplayName": "RemindApp",
        "CFBundleIdentifier": "com.remindapp.app",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0",
        # 隐藏 Dock 图标（菜单栏 App 标准做法）
        "LSUIElement": True,
        # Retina 屏幕支持
        "NSHighResolutionCapable": True,
        # macOS 最低版本
        "LSMinimumSystemVersion": "10.14.0",
    },
    # 需要打包的第三方包
    "packages": ["rumps"],
    # 需要显式包含的模块（pyobjc 框架）
    "includes": [
        "AppKit",
        "Foundation",
        "objc",
        "CoreFoundation",
    ],
    # 不需要的模块（减小体积）
    "excludes": ["tkinter", "test", "unittest"],
    # False = 独立打包（包含 Python 运行时），适合分发
    "semi_standalone": False,
    "site_packages": False,
    # 不剥离调试符号（避免只读扩展模块的权限错误）
    "strip": False,
    # 应用图标
    "iconfile": "RemindApp.icns",
}

setup(
    name="RemindApp",
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
