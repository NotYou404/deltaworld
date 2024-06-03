import time
from typing import Any

import arcade


class Window(arcade.Window):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.draws = 0
        self.updates = 0
        self.set_vsync(False)
        self.set_draw_rate(1 / 1000)
        self.set_update_rate(1 / 1000)

    def on_draw(self) -> None:
        self.draws += 1

    def on_update(self, dt: float) -> None:
        print(f"Delta time fps: {1 / dt}")
        self.updates += 1


if __name__ == "__main__":
    win = Window()
    print(f"Draw rate:   {win._draw_rate}")
    print(f"Update rate: {win._update_rate}")
    start = time.time()
    try:
        arcade.run()  # type: ignore[no-untyped-call]
    except KeyboardInterrupt:
        print(f"Ran for {time.time() - start} seconds")
        print(f"Draw calls:   {win.draws}")
        print(f"Update calls: {win.updates}")
