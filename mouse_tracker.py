#!/usr/bin/env python3
"""Небольшая утилита для записи траектории мыши в формате C-массива.

Использование:
  python mouse_tracker.py --name PAINT_DEMO --interval 12

Управление:
  F8  - начать/остановить запись
  F9  - вывести результат и завершить программу
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass

from pynput import keyboard, mouse


@dataclass
class Point:
    x: int
    y: int
    dt_ms: int


class MousePathRecorder:
    def __init__(self, name: str, interval_ms: int) -> None:
        self.name = name
        self.interval_ms = interval_ms
        self.recording = False
        self.origin: tuple[int, int] | None = None
        self.last_sample_ts = 0.0
        self.points: list[Point] = []

    def toggle_recording(self) -> None:
        self.recording = not self.recording
        if self.recording:
            self.origin = None
            self.last_sample_ts = 0.0
            self.points.clear()
            print("[INFO] Запись началась. Двигайте мышь.")
        else:
            print(f"[INFO] Запись остановлена. Точек: {len(self.points)}")

    def on_move(self, x: int, y: int) -> None:
        if not self.recording:
            return

        now = time.monotonic()
        if self.last_sample_ts and (now - self.last_sample_ts) * 1000 < self.interval_ms:
            return

        if self.origin is None:
            self.origin = (x, y)

        ox, oy = self.origin
        self.points.append(Point(x - ox, y - oy, self.interval_ms))
        self.last_sample_ts = now

    def to_output(self) -> str:
        payload = ", ".join(f"{{{p.x}, {p.y}, {p.dt_ms}}}" for p in self.points)
        return f'{{"{self.name}", "[NULL]", {{{{{payload}}}}}}},\\n'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Запись траектории мыши.")
    parser.add_argument("--name", default="PAINT_DEMO", help="Имя макроса в выводе")
    parser.add_argument(
        "--interval",
        type=int,
        default=12,
        help="Интервал семплирования в миллисекундах",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.interval <= 0:
        print("[ERROR] --interval должен быть > 0", file=sys.stderr)
        return 2

    recorder = MousePathRecorder(name=args.name, interval_ms=args.interval)

    mouse_listener = mouse.Listener(on_move=recorder.on_move)

    def on_press(key: keyboard.Key | keyboard.KeyCode) -> bool | None:
        if key == keyboard.Key.f8:
            recorder.toggle_recording()
        elif key == keyboard.Key.f9:
            if recorder.recording:
                recorder.toggle_recording()
            print("\n[RESULT]")
            print(recorder.to_output())
            return False
        return None

    keyboard_listener = keyboard.Listener(on_press=on_press)

    print("Готово. F8 — старт/стоп записи, F9 — вывести и выйти.")

    mouse_listener.start()
    keyboard_listener.start()
    keyboard_listener.join()
    mouse_listener.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
