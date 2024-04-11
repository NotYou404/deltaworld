import time

import arcade


class Window(arcade.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.draws = 0
        self.updates = 0
        self.set_vsync(True)
        self.set_draw_rate(1 / 60)
        self.set_update_rate(1 / 60)

    def on_draw(self):
        self.draws += 1

    def on_update(self, dt):
        self.updates += 1


if __name__ == "__main__":
    win = Window()
    print(f"Draw rate:   {win._draw_rate}")
    print(f"Update rate: {win._update_rate}")
    start = time.time()
    try:
        arcade.run()
    except KeyboardInterrupt:
        print(f"Ran for {time.time() - start} seconds")
        print(f"Draw calls:   {win.draws}")
        print(f"Update calls: {win.updates}")
