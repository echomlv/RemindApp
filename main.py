"""RemindApp 主程序 - macOS 菜单栏颈椎提醒工具"""

import random
import rumps

from config import Config
from reminder import ReminderManager
from notifier import play_sound, send_banner, SOUNDS
from templates import TEMPLATES
from overlay import show_overlay_from_thread

config = Config()


class RemindApp(rumps.App):
    def __init__(self):
        super().__init__("RemindApp", title="🔔", quit_button=None)

        self._manager = ReminderManager(on_fire=self._on_reminder_fire)
        self._build_menu()

        # 若上次退出时处于启用状态，自动恢复
        if config.get("enabled"):
            self._manager.start(
                config.get("interval_minutes"),
                config.get("recurring"),
            )

    # ──────────────────────────────────────────
    # 菜单构建
    # ──────────────────────────────────────────

    def _build_menu(self):
        self._toggle_item = rumps.MenuItem("启用提醒", callback=self._toggle_enabled)
        self._toggle_item.state = config.get("enabled")

        self._countdown_item = rumps.MenuItem("  下次提醒: 已暂停")

        self.menu = [
            self._toggle_item,
            None,
            self._countdown_item,
            None,
            self._build_interval_menu(),
            self._build_message_menu(),
            self._build_notification_menu(),
            self._build_sound_menu(),
            None,
            rumps.MenuItem("🔍 测试提醒", callback=self._test_reminder),
            None,
            rumps.MenuItem("退出", callback=rumps.quit_application),
        ]

    def _build_interval_menu(self):
        menu = rumps.MenuItem("⏰ 提醒间隔")
        menu.add(rumps.MenuItem("自定义间隔...", callback=self._set_custom_interval))
        menu.add(None)

        current = config.get("interval_minutes")
        for minutes in [5, 15, 30, 60]:
            item = rumps.MenuItem(f"{minutes} 分钟", callback=self._set_interval_preset)
            item.state = current == minutes
            menu.add(item)

        menu.add(None)
        self._single_item = rumps.MenuItem("单次提醒", callback=self._toggle_recurring)
        self._single_item.state = not config.get("recurring")
        menu.add(self._single_item)

        self._interval_menu = menu
        return menu

    def _build_message_menu(self):
        menu = rumps.MenuItem("💬 提示语")

        self._random_item = rumps.MenuItem("✨ 随机模板", callback=self._toggle_random_template)
        self._random_item.state = config.get("use_random_template")
        menu.add(self._random_item)

        # 模板子菜单
        template_menu = rumps.MenuItem("选择模板")
        current_key = config.get("selected_template_key")
        for t in TEMPLATES:
            label = f"{t['emoji']} {t['title']}"
            item = rumps.MenuItem(label, callback=self._select_template)
            item.state = t["key"] == current_key
            template_menu.add(item)
        self._template_menu = template_menu
        menu.add(template_menu)

        menu.add(rumps.MenuItem("自定义文字...", callback=self._set_custom_message))

        self._clear_custom_item = rumps.MenuItem(
            "清除自定义文字", callback=self._clear_custom_message
        )
        if config.get("custom_message"):
            menu.add(self._clear_custom_item)
        self._message_menu = menu
        return menu

    def _build_notification_menu(self):
        menu = rumps.MenuItem("🔔 通知方式")
        current = config.get("notification_type")

        self._banner_item = rumps.MenuItem(
            "横幅通知（右上角）", callback=self._set_notification_banner
        )
        self._banner_item.state = current == "banner"

        self._overlay_item = rumps.MenuItem(
            "全屏遮罩（醒目打断）", callback=self._set_notification_overlay
        )
        self._overlay_item.state = current == "overlay"

        menu.add(self._banner_item)
        menu.add(self._overlay_item)
        return menu

    def _build_sound_menu(self):
        menu = rumps.MenuItem("🔊 提示音")

        self._sound_enabled_item = rumps.MenuItem("启用声音", callback=self._toggle_sound)
        self._sound_enabled_item.state = config.get("sound_enabled")
        menu.add(self._sound_enabled_item)
        menu.add(None)

        current_sound = config.get("sound_name")
        for sound in SOUNDS:
            item = rumps.MenuItem(sound, callback=self._select_sound)
            item.state = sound == current_sound
            menu.add(item)

        self._sound_menu = menu
        return menu

    # ──────────────────────────────────────────
    # 定时器：每秒更新倒计时显示
    # ──────────────────────────────────────────

    @rumps.timer(1)
    def _update_countdown(self, _):
        seconds = self._manager.seconds_until_next()
        if seconds is not None:
            m = int(seconds) // 60
            s = int(seconds) % 60
            self._countdown_item.title = f"  下次提醒: {m:02d}:{s:02d}"
        else:
            self._countdown_item.title = "  下次提醒: 已暂停"

    # ──────────────────────────────────────────
    # 提醒触发（来自 threading.Timer 后台线程）
    # ──────────────────────────────────────────

    def _on_reminder_fire(self):
        message, emoji = self._get_current_message()

        if config.get("sound_enabled"):
            play_sound(config.get("sound_name"))

        if config.get("notification_type") == "overlay":
            show_overlay_from_thread(message, emoji)
        else:
            send_banner("该休息啦 🔔", f"{emoji} {message}")

        # 单次模式：触发后关闭定时器
        if not config.get("recurring"):
            config.set("enabled", False)
            # 在主线程更新 UI
            AppKitDispatch.run_on_main(
                lambda: setattr(self._toggle_item, "state", False)
            )

    def _get_current_message(self):
        custom = config.get("custom_message")
        if custom:
            return custom, "🔔"
        if config.get("use_random_template"):
            t = random.choice(TEMPLATES)
        else:
            key = config.get("selected_template_key")
            t = next((x for x in TEMPLATES if x["key"] == key), TEMPLATES[0])
        return t["message"], t["emoji"]

    # ──────────────────────────────────────────
    # 菜单回调
    # ──────────────────────────────────────────

    def _toggle_enabled(self, sender):
        if self._manager.is_running:
            self._manager.stop()
            config.set("enabled", False)
            sender.state = False
        else:
            self._manager.start(config.get("interval_minutes"), config.get("recurring"))
            config.set("enabled", True)
            sender.state = True

    def _set_interval_preset(self, sender):
        minutes = int(sender.title.replace(" 分钟", ""))
        config.set("interval_minutes", minutes)
        for label in ["5 分钟", "15 分钟", "30 分钟", "60 分钟"]:
            try:
                self._interval_menu[label].state = label == sender.title
            except KeyError:
                pass
        self._manager.restart(minutes, config.get("recurring"))

    def _set_custom_interval(self, _):
        w = rumps.Window(
            title="自定义提醒间隔",
            message="请输入间隔分钟数（1-480）：",
            default_text=str(int(config.get("interval_minutes"))),
            ok="确定",
            cancel="取消",
            dimensions=(200, 24),
        )
        resp = w.run()
        if resp.clicked and resp.text.strip().isdigit():
            minutes = max(1, min(480, int(resp.text.strip())))
            config.set("interval_minutes", minutes)
            for label in ["5 分钟", "15 分钟", "30 分钟", "60 分钟"]:
                try:
                    self._interval_menu[label].state = False
                except KeyError:
                    pass
            self._manager.restart(minutes, config.get("recurring"))

    def _toggle_recurring(self, sender):
        recurring = not config.get("recurring")
        config.set("recurring", recurring)
        sender.state = not recurring  # "单次提醒" 勾选 = 非循环模式
        self._manager.restart(config.get("interval_minutes"), recurring)

    def _toggle_random_template(self, sender):
        new_val = not config.get("use_random_template")
        config.set("use_random_template", new_val)
        sender.state = new_val

    def _select_template(self, sender):
        for t in TEMPLATES:
            label = f"{t['emoji']} {t['title']}"
            if label == sender.title:
                config.set("selected_template_key", t["key"])
                config.set("use_random_template", False)
                self._random_item.state = False
                break
        # 更新子菜单选中状态
        for t in TEMPLATES:
            label = f"{t['emoji']} {t['title']}"
            try:
                self._template_menu[label].state = label == sender.title
            except KeyError:
                pass

    def _set_custom_message(self, _):
        w = rumps.Window(
            title="自定义提示语",
            message="输入提示语（留空则使用模板）：",
            default_text=config.get("custom_message"),
            ok="确定",
            cancel="取消",
            dimensions=(320, 80),
        )
        resp = w.run()
        if resp.clicked:
            msg = resp.text.strip()
            config.set("custom_message", msg)
            # 显示/隐藏"清除"选项
            try:
                if msg:
                    self._message_menu.add(self._clear_custom_item)
                else:
                    del self._message_menu["清除自定义文字"]
            except Exception:
                pass

    def _clear_custom_message(self, _):
        config.set("custom_message", "")
        try:
            del self._message_menu["清除自定义文字"]
        except Exception:
            pass

    def _set_notification_banner(self, _):
        config.set("notification_type", "banner")
        self._banner_item.state = True
        self._overlay_item.state = False

    def _set_notification_overlay(self, _):
        config.set("notification_type", "overlay")
        self._banner_item.state = False
        self._overlay_item.state = True

    def _toggle_sound(self, sender):
        new_val = not config.get("sound_enabled")
        config.set("sound_enabled", new_val)
        sender.state = new_val

    def _select_sound(self, sender):
        name = sender.title
        config.set("sound_name", name)
        for sound in SOUNDS:
            try:
                self._sound_menu[sound].state = sound == name
            except KeyError:
                pass
        if name != "None":
            play_sound(name)

    def _test_reminder(self, _):
        self._on_reminder_fire()


class AppKitDispatch:
    """在主线程执行回调的工具类"""

    @staticmethod
    def run_on_main(func):
        try:
            import AppKit
            AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(func)
        except Exception:
            pass


if __name__ == "__main__":
    RemindApp().run()
