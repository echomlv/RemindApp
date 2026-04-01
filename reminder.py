"""定时器管理"""

import threading
from datetime import datetime, timedelta
from typing import Optional


class ReminderManager:
    def __init__(self, on_fire):
        """
        on_fire: 定时触发时调用的回调函数（无参数）
        """
        self._on_fire = on_fire
        self._timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()
        self.next_fire_time: Optional[datetime] = None
        self.is_running = False

    def start(self, interval_minutes: float, recurring: bool):
        """启动定时器"""
        with self._lock:
            self._cancel()
            interval_seconds = interval_minutes * 60.0
            self.next_fire_time = datetime.now() + timedelta(seconds=interval_seconds)
            self.is_running = True
            self._schedule(interval_seconds, recurring)

    def stop(self):
        """停止定时器"""
        with self._lock:
            self._cancel()
            self.is_running = False
            self.next_fire_time = None

    def restart(self, interval_minutes: float, recurring: bool):
        """如果正在运行则重新启动（用于设置变更后刷新）"""
        if self.is_running:
            self.start(interval_minutes, recurring)

    def _schedule(self, interval_seconds: float, recurring: bool):
        def fire():
            self._on_fire()
            with self._lock:
                if recurring and self.is_running:
                    self.next_fire_time = datetime.now() + timedelta(
                        seconds=interval_seconds
                    )
                    self._schedule(interval_seconds, recurring)
                else:
                    self.is_running = False
                    self.next_fire_time = None

        self._timer = threading.Timer(interval_seconds, fire)
        self._timer.daemon = True
        self._timer.start()

    def _cancel(self):
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    def seconds_until_next(self) -> Optional[float]:
        """返回距离下次提醒的秒数，未运行则返回 None"""
        if self.next_fire_time is None:
            return None
        delta = (self.next_fire_time - datetime.now()).total_seconds()
        return max(0.0, delta)
