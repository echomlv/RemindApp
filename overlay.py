"""全屏 Overlay 提醒窗口（使用 pyobjc AppKit）"""

import AppKit
import objc

# 模块级引用，防止被垃圾回收
_current_window = None
_current_handler = None


class _OverlayWindow(AppKit.NSWindow):
    """响应 Escape/Return 键的无边框全屏窗口"""

    def canBecomeKeyWindow(self):
        return True

    def keyDown_(self, event):
        # 53 = Escape, 36 = Return
        if event.keyCode() in (53, 36):
            _dismiss_current()
        else:
            AppKit.NSWindow.keyDown_(self, event)


class _ButtonHandler(AppKit.NSObject):
    """按钮点击事件处理器"""

    def initWithWindow_(self, window):
        self = objc.super(_ButtonHandler, self).init()
        if self is None:
            return None
        self._win = window
        return self

    def dismiss_(self, sender):
        _dismiss_current()


def _dismiss_current():
    global _current_window, _current_handler
    if _current_window is not None:
        _current_window.orderOut_(None)
        _current_window = None
        _current_handler = None


def show_overlay(message: str, emoji: str):
    """在主线程显示全屏遮罩提醒（必须在主线程调用）"""
    global _current_window, _current_handler

    # 关闭已有遮罩
    if _current_window is not None:
        _current_window.orderOut_(None)

    screen = AppKit.NSScreen.mainScreen()
    if screen is None:
        return

    frame = screen.frame()

    # 创建无边框全屏窗口
    window = _OverlayWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        frame,
        AppKit.NSWindowStyleMaskBorderless,
        AppKit.NSBackingStoreBuffered,
        False,
    )
    window.setLevel_(AppKit.NSScreenSaverWindowLevel)
    window.setBackgroundColor_(
        AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(0.0, 0.0, 0.0, 0.62)
    )
    window.setOpaque_(False)
    window.setCollectionBehavior_(
        AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces
        | AppKit.NSWindowCollectionBehaviorStationary
    )
    window.setHidesOnDeactivate_(False)
    window.setReleasedWhenClosed_(False)

    content = window.contentView()
    content.setWantsLayer_(True)

    # 居中卡片尺寸
    card_w, card_h = 480, 300
    card_x = (frame.size.width - card_w) / 2
    card_y = (frame.size.height - card_h) / 2

    # 毛玻璃卡片 —— 强制 Dark Aqua，保证深色背景下白字清晰可见
    card = AppKit.NSVisualEffectView.alloc().initWithFrame_(
        AppKit.NSMakeRect(card_x, card_y, card_w, card_h)
    )
    card.setMaterial_(AppKit.NSVisualEffectMaterialHUDWindow)
    card.setBlendingMode_(AppKit.NSVisualEffectBlendingModeBehindWindow)
    card.setState_(AppKit.NSVisualEffectStateActive)
    card.setWantsLayer_(True)
    card.layer().setCornerRadius_(22.0)
    card.layer().setMasksToBounds_(True)
    # 无论系统是浅色还是深色主题，卡片始终使用深色外观
    dark_appearance = AppKit.NSAppearance.appearanceNamed_(
        AppKit.NSAppearanceNameDarkAqua
    )
    card.setAppearance_(dark_appearance)
    content.addSubview_(card)

    # Emoji 标签（大号，卡片顶部）
    emoji_field = AppKit.NSTextField.alloc().initWithFrame_(
        AppKit.NSMakeRect(0, card_h - 100, card_w, 88)
    )
    emoji_field.setStringValue_(emoji)
    emoji_field.setFont_(AppKit.NSFont.systemFontOfSize_(58.0))
    emoji_field.setAlignment_(AppKit.NSTextAlignmentCenter)
    emoji_field.setBezeled_(False)
    emoji_field.setDrawsBackground_(False)
    emoji_field.setEditable_(False)
    emoji_field.setSelectable_(False)
    # 显式设白色，避免系统主题干扰
    emoji_field.setTextColor_(AppKit.NSColor.whiteColor())
    card.addSubview_(emoji_field)

    # 提示语文字
    msg_field = AppKit.NSTextField.alloc().initWithFrame_(
        AppKit.NSMakeRect(30, 74, card_w - 60, 116)
    )
    msg_field.setStringValue_(message)
    msg_field.setFont_(AppKit.NSFont.systemFontOfSize_(18.0))
    msg_field.setTextColor_(AppKit.NSColor.whiteColor())
    msg_field.setAlignment_(AppKit.NSTextAlignmentCenter)
    msg_field.setBezeled_(False)
    msg_field.setDrawsBackground_(False)
    msg_field.setEditable_(False)
    msg_field.setSelectable_(False)
    msg_field.setMaximumNumberOfLines_(4)
    msg_field.setLineBreakMode_(AppKit.NSLineBreakByWordWrapping)
    card.addSubview_(msg_field)

    # 知道了按钮
    handler = _ButtonHandler.alloc().initWithWindow_(window)

    btn_w, btn_h = 130, 38
    btn = AppKit.NSButton.alloc().initWithFrame_(
        AppKit.NSMakeRect((card_w - btn_w) / 2, 18, btn_w, btn_h)
    )
    btn.setTitle_("  知道了  ")
    btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
    btn.setKeyEquivalent_("\r")
    btn.setTarget_(handler)
    btn.setAction_("dismiss:")
    card.addSubview_(btn)

    # 设为默认按钮（响应 Return 键）
    window.setDefaultButtonCell_(btn.cell())

    _current_window = window
    _current_handler = handler

    window.makeKeyAndOrderFront_(None)
    AppKit.NSApp.activateIgnoringOtherApps_(True)


def show_overlay_from_thread(message: str, emoji: str):
    """线程安全版本：从任意线程调度到主线程显示遮罩"""
    AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(
        lambda: show_overlay(message, emoji)
    )
