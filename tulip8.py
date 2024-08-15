import random, time, math, os, sys
import tulip, amy, music
import array

# chip 8 imports
import machine

# local modules
from chip8 import Chip8

chip8_program = "programs/slipperyslope.ch8"

# Tulip 8 - A Chip 8 Simulator for Tulip CC


class Tulip8(tulip.Game):
    def __init__(self, initial_rom_path=None):

        self.KEY_P = [112, 80]
        self.KEY_ESC = [27]

        self.KEY_1 = [49]
        self.KEY_2 = [50]
        self.KEY_3 = [51]
        self.KEY_4 = [52]

        self.KEY_Q = [113, 81]
        self.KEY_W = [119, 87]
        self.KEY_E = [101, 69]
        self.KEY_R = [114, 82]

        self.KEY_A = [97, 65]
        self.KEY_S = [115, 83]
        self.KEY_D = [100, 68]
        self.KEY_F = [102, 70]

        self.KEY_Z = [122, 90]
        self.KEY_X = [120, 88]
        self.KEY_C = [99, 67]
        self.KEY_V = [118, 86]

        (self.SCREEN_WIDTH, self.SCREEN_HEIGHT) = tulip.screen_size()

        self.initial_rom_path = initial_rom_path

        self.HALF_SCREEN_WIDTH = self.SCREEN_WIDTH / 2
        self.HALF_SCREEN_HEIGHT = self.SCREEN_HEIGHT / 2

        # self.background_color = tulip.color(0, 0, 0)  # rgb(0, 0, 0)
        self.background_color = tulip.color(0, 73, 85)  # rgb(0, 0, 0)
        self.foreground_color = tulip.color(255, 255, 255)  # rgb(255 255 255)

        self.display_scale = 2.0

        self.render_filled = True
        self.play_game = False

        self.sleep_ms = 600

        tulip.gpu_reset()

        # start CHIP-8 emulator
        self.chip8 = Chip8(
            self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.draw_pixel, self.play_beep
        )
        self.chip8.set_use_color_mode(False)

        int_pixel_scale = int(self.chip8.scale)

        tulip.bg_rect(
            1025,
            int_pixel_scale,
            int_pixel_scale,
            int_pixel_scale,
            self.background_color,
            self.render_filled,
        )
        tulip.bg_rect(
            1025,
            0,
            int_pixel_scale,
            int_pixel_scale,
            self.foreground_color,
            self.render_filled,
        )

        # If scanning key codes in a program, you may want to turn on "key scan" mode so that
        # keys are not sent to the underlying python process
        tulip.key_scan(1)
        # tulip.key_scan(0) # remember to turn it back off or you won't be able to type into the REPL

        # specify keyboard callback
        tulip.keyboard_callback(self.keyboard_event_callback)

        # game loop callback (runs every frame)
        tulip.frame_callback(self.main_loop)

        self.load_rom(self.initial_rom_path)

        pass

    def load_rom(self, rom_path):

        if self.chip8:
            self.chip8.load_external_program(self.initial_rom_path)
        pass

    def async_chip8_tick(self):
        pass

    def main_loop(self, g):
        self.chip8.cycle()

    def play_beep(self, play=False):
        if play:
            amy.send(wave=amy.PULSE, osc=100, note=60, vel=1)
        else:
            amy.reset()

    def draw_pixel(self, x, y, pixel_scale, pixel_on=True):

        int_pixel_scale = int(pixel_scale)

        if pixel_on:
            # copy white bitmap from offscreen (1024, 0)
            tulip.bg_blit(
                1025,
                0,
                int_pixel_scale,
                int_pixel_scale,
                int(x) * int_pixel_scale,
                int(y) * int_pixel_scale,
            )
            # tulip.bg_rect(int(x) * int_pixel_scale, int(y) * int_pixel_scale, int_pixel_scale, int_pixel_scale, self.foreground_color, self.render_filled)  # x and y are the center

        else:
            # copy black bitmap from offscreen (1024, pixel_scale)
            tulip.bg_blit(
                1025,
                int_pixel_scale,
                int_pixel_scale,
                int_pixel_scale,
                int(x) * int_pixel_scale,
                int(y) * int_pixel_scale,
            )
            # tulip.bg_rect(int(x) * int_pixel_scale, int(y) * int_pixel_scale, int_pixel_scale, int_pixel_scale, self.background_color, self.render_filled)  # x and y are the center

    def keyboard_event_callback(self, key):
        # print("got key: %d" % (key))

        if self.chip8:

            if key in self.KEY_1:
                self.chip8.key_press("1")

            if key in self.KEY_2:
                self.chip8.key_press("2")

            if key in self.KEY_3:
                self.chip8.key_press("3")

            if key in self.KEY_4:
                self.chip8.key_press("4")

            if key in self.KEY_Q:
                self.chip8.key_press("Q")

            if key in self.KEY_W:
                self.chip8.key_press("W")

            if key in self.KEY_E:
                self.chip8.key_press("E")

            if key in self.KEY_R:
                self.chip8.key_press("R")

            if key in self.KEY_A:
                self.chip8.key_press("A")

            if key in self.KEY_S:
                self.chip8.key_press("S")

            if key in self.KEY_D:
                self.chip8.key_press("D")

            if key in self.KEY_F:
                self.chip8.key_press("F")

            if key in self.KEY_Z:
                self.chip8.key_press("Z")

            if key in self.KEY_X:
                self.chip8.key_press("X")

            if key in self.KEY_C:
                self.chip8.key_press("C")

            if key in self.KEY_V:
                self.chip8.key_press("V")

            pass

        if key in self.KEY_ESC:
            self.quit_app()

        elif key in self.KEY_P:
            # print(f"self.chip8.use_color_mode: {self.chip8.use_color_mode}")
            # self.chip8.set_use_color_mode(not self.chip8.use_color_mode)
            pass

    def start_app(self):
        self.play_game = True

    def stop_game(self):
        self.play_game = False

    def quit_app(self):
        # your quit callback gets a screen object, use it to shut down
        self.stop_game()
        tulip.keyboard_callback()

        self.chip8.reset()

        amy.reset()
        tulip.key_scan(0)
        tulip.frame_callback()
        tulip.bg_scroll()
        tulip.bg_clear()
        tulip.sprite_clear()

        tulip.gpu_reset()

        # restart the text framebuffer
        tulip.tfb_start()

        print("stopping Tulip8, press ENTER")


def quit(chip8=None):

    if chip8 != None:
        chip8.reset()

    # your quit callback gets a screen object, use it to shut down
    tulip.keyboard_callback()

    # amy.reset()
    tulip.key_scan(0)
    tulip.frame_callback()
    tulip.bg_scroll()
    tulip.bg_clear()
    tulip.sprite_clear()

    tulip.gpu_reset()

    # restart the text framebuffer
    tulip.tfb_start()

    tulip.display_restart()

    print("stopping Tulip8, press ENTER")


try:
    tulip8 = Tulip8(chip8_program)
    pass
except KeyboardInterrupt:
    quit()
