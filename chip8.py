import random, time

import array



class Chip8:
    """
    Emulates a Chip-8 virtual machine.

    This class encapsulates the logic for running Chip-8 programs. It handles opcode interpretation,
    memory management, CPU registers, display, keyboard input, and timers.

    Main Attributes:
        memory (bytearray): The main memory of the Chip-8 system.
        v (list): The general-purpose registers.
        i (int): The index register.
        sp (int): The stack pointer.
        stack (list): The stack for subroutine calls.
        pc (int): The program counter.
        delay_timer (int): The delay timer.
        sound_timer (int): The sound timer.
        screen (bytearray): The display buffer.
        keypad (list): The keypad state.
        display_dirty (bool): Flag indicating if the display needs to be updated.
        key_map (dict): Mapping of physical keys to Chip-8 key codes.
    """

    def __init__(
        self,
        screen_width,
        screen_height,
        draw_pixel_callback=None,
        play_audio_callback=None,
    ):

        self.experimental_optimization = True

        # host device settings
        self.width = screen_width
        self.height = screen_height
        self.scale = min(self.width // 64, self.height // 32)

        # Memory and registers
        self.memory = bytearray(4096)
        self.v = [0] * 16
        self.i = 0
        self.pc = 0x200

        # Stack and timers
        self.stack = [0] * 16
        self.sp = 0
        self.delay_timer = 0
        self.sound_timer = 0

        # Display
        self.screen = self.get_clear_screen_bytes()

        # Keypad
        self.keypad = [False] * 16
        self.key_timestamps = [0] * 16
        self.key_delay = 200  # key release delay in milliseconds

        self.display_dirty = False

        # Sample fontset
        self.fontset = [
            0xF0,
            0x90,
            0x90,
            0xF0,  # 0
            0x20,
            0x60,
            0x20,
            0x20,  # 1
            0xF0,
            0x10,
            0xF0,
            0x80,  # 2
            0xF0,
            0x10,
            0xF0,
            0x10,  # 3
            0x90,
            0x90,
            0xF0,
            0x10,  # 4
            0xF0,
            0x80,
            0xF0,
            0x10,  # 5
            0xF0,
            0x80,
            0xF0,
            0x90,  # 6
            0xF0,
            0x10,
            0x20,
            0x00,  # 7
            0xF0,
            0x90,
            0xF0,
            0x90,  # 8
            0xF0,
            0x90,
            0xF0,
            0x10,  # 9
            0xF0,
            0x90,
            0xF0,
            0x90,  # A
            0xE0,
            0x90,
            0xE0,
            0x90,  # B
            0xF0,
            0x80,
            0x80,
            0xF0,  # C
            0xE0,
            0x90,
            0xE0,
            0x90,  # D
            0xF0,
            0x80,
            0xF0,
            0x00,  # E
            0xF0,
            0x80,
            0xE0,
            0x00,  # F
        ]

        self.key_map = {
            "1": 0x1,
            "2": 0x2,
            "3": 0x3,
            "4": 0xC,
            "Q": 0x4,
            "W": 0x5,
            "E": 0x6,
            "R": 0xD,
            "A": 0x7,
            "S": 0x8,
            "D": 0x9,
            "F": 0xA,
            "Z": 0x0,
            "X": 0xB,
            "C": 0xF,
            "V": 0xE,
        }

        self.is_sound_playing = False

        self.clock_cycle_interval = 1

        self.draw_pixel_callback = draw_pixel_callback

        self.play_audio_callback = play_audio_callback

        self.set_use_color_mode(False)

        self.reset()

    def reset(self):

        # Memory and registers
        self.memory = bytearray(4096)
        self.v = [0] * 16
        self.i = 0
        self.pc = 0x200

        # Stack and timers
        self.stack = [0] * 16
        self.sp = 0
        self.delay_timer = 0
        self.sound_timer = 0

        # Display
        self.screen = self.get_clear_screen_bytes()

        # Keypad
        self.keypad = [False] * 16
        self.key_timestamps = [0] * 16
        self.key_delay = 200  # key release delay in milliseconds

        # Load fontset into memory
        for i, char in enumerate(self.fontset):
            self.memory[i + 0x50] = char

        self.display_dirty = False

        self.next_cycle_run_time = time.ticks_ms()

        self.stop()

        pass

    def key_press(self, key):
        mapped_key = self.key_map[key]

        self.keypad[mapped_key] = True
        self.key_timestamps[mapped_key] = time.ticks_ms()

        pass

    def key_release(self, key):
        mapped_key = self.key_map[key]

        self.keypad[mapped_key] = False
        pass

    def check_keypress_timestamps(self):
        current_time = time.ticks_ms()
        for i in range(16):
            if (
                self.keypad[i]
                and current_time - self.key_timestamps[i] >= self.key_delay
            ):
                self.keypad[i] = False
        pass

    def load_rom(self, rom):
        print(f"Loading ROM")
        for i, byte in enumerate(rom, start=0x200):
            # print(f"byte: {byte}")
            self.memory[i] = byte

    def load_external_program(self, filename):
        """Loads a Chip-8 ROM file into the emulator's memory."""

        with open(filename, "rb") as f:
            rom_data = bytearray(f.read())

        self.reset()
        self.load_rom(rom_data)
        self.start()


    def set_use_color_mode(self, use_color_mode):
        self.use_color_mode = use_color_mode

    def get_clear_screen_bytes(self):
        return bytearray(self.width * self.height)

    def start(self):

        self.running = True
        self.next_cycle_run_time = time.ticks_ms() + self.clock_cycle_interval
        pass

    def stop(self):
        self.running = False
        pass

    def cycle(self):

        if self.running:

            self.check_keypress_timestamps()

            # Fetch opcode
            opcode = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]
            self.pc += 2

            # Decode and execute opcode
            x = (opcode & 0x0F00) >> 8
            y = (opcode & 0x00F0) >> 4
            n = opcode & 0x000F
            nn = opcode & 0x00FF
            nnn = opcode & 0xFFF

            if opcode & 0xF000 == 0x0000:
                if opcode == 0x00E0:  # Clear screen
                    # self.screen.clear()
                    self.screen = self.get_clear_screen_bytes()
                    self.display_dirty = True
                elif opcode == 0x00EE:  # Return from subroutine
                    self.sp -= 1
                    self.pc = self.stack[self.sp]
                else:
                    print(f"Unknown opcode: {hex(opcode)}")
            elif opcode & 0xF000 == 0x1000:  # Jump to address nnn
                self.pc = opcode & 0xFFF
            elif opcode & 0xF000 == 0x2000:  # Call subroutine
                self.stack[self.sp] = self.pc
                self.sp += 1
                self.pc = opcode & 0xFFF
            elif opcode & 0xF000 == 0x3000:  # Skip next instruction if VX == NN
                vx = (opcode & 0x0F00) >> 8
                nn = opcode & 0x00FF
                if self.v[vx] == nn:
                    self.pc += 2
            elif opcode & 0xF000 == 0x4000:  # Skip next instruction if VX != NN
                vx = (opcode & 0x0F00) >> 8
                nn = opcode & 0x00FF
                if self.v[vx] != nn:
                    self.pc += 2
            elif opcode & 0xF000 == 0x5000:  # Skip next instruction if VX == VY
                vx = (opcode & 0x0F00) >> 8
                vy = (opcode & 0x00F0) >> 4
                if self.v[vx] == self.v[vy]:
                    self.pc += 2
            elif opcode & 0xF000 == 0x6000:  # Set VX to NN
                vx = (opcode & 0x0F00) >> 8
                nn = opcode & 0x00FF
                self.v[vx] = nn
            elif opcode & 0xF000 == 0x7000:  # Add NN to VX
                vx = (opcode & 0x0F00) >> 8
                nn = opcode & 0x00FF
                self.v[vx] += nn
                self.v[vx] &= 0xFF  # Carry flag
            elif opcode & 0xF000 == 0x8000:  # Mathematical and logical operations
                vx = (opcode & 0x0F00) >> 8
                vy = (opcode & 0x00F0) >> 4
                switch_case = opcode & 0x000F
                if switch_case == 0x0:  # Set VX to VY
                    self.v[vx] = self.v[vy]
                elif switch_case == 0x1:  # Set VX to VX OR VY
                    self.v[vx] |= self.v[vy]
                elif switch_case == 0x2:  # Set VX to VX AND VY
                    self.v[vx] &= self.v[vy]
                elif switch_case == 0x3:  # Set VX to VX XOR VY
                    self.v[vx] ^= self.v[vy]
                elif switch_case == 0x4:  # Add VY to VX. VF is set to 1 if carry
                    self.v[vx] += self.v[vy]
                    self.v[0xF] = 1 if self.v[vx] > 0xFF else 0
                    self.v[vx] &= 0xFF
                elif (
                    switch_case == 0x5
                ):  # Subtract VY from VX. VF is set to 0 if borrow
                    self.v[0xF] = 1 if self.v[vx] > self.v[vy] else 0
                    self.v[vx] -= self.v[vy]
                    self.v[vx] &= 0xFF
                elif (
                    switch_case == 0x6
                ):  # Shift VX right by one. VF is set to the least significant bit of VX
                    self.v[0xF] = self.v[vx] & 0x1
                    self.v[vx] >>= 1
                elif switch_case == 0x7:  # Set VX to VY - VX. VF is set to 0 if borrow
                    self.v[0xF] = 1 if self.v[vy] > self.v[vx] else 0
                    self.v[vx] = self.v[vy] - self.v[vx]
                    self.v[vx] &= 0xFF
                elif (
                    switch_case == 0xE
                ):  # Shift VX left by one. VF is set to the most significant bit of VX
                    self.v[0xF] = (self.v[vx] & 0x80) >> 7
                    self.v[vx] <<= 1
                    self.v[vx] &= 0xFF
                else:
                    print(f"Unknown opcode: {hex(opcode)}")
            elif opcode & 0xF000 == 0x9000:  # Skip next instruction if VX != VY
                vx = (opcode & 0x0F00) >> 8
                vy = (opcode & 0x00F0) >> 4
                if self.v[vx] != self.v[vy]:
                    self.pc += 2
            elif opcode & 0xF000 == 0xA000:  # Set I to nnn
                self.i = opcode & 0xFFF
            elif opcode & 0xF000 == 0xB000:  # Jump to address nnn + V0
                self.pc = (opcode & 0xFFF) + self.v[0]
            elif opcode & 0xF000 == 0xC000:  # Set VX to random number AND NN
                vx = (opcode & 0x0F00) >> 8
                nn = opcode & 0x00FF
                self.v[vx] = random.randint(0, 255) & nn
            elif opcode & 0xF000 == 0xD000:
                # Draw sprite
                vx = (opcode & 0x0F00) >> 8
                vy = (opcode & 0x00F0) >> 4
                height = opcode & 0x000F
                self.v[0xF] = 0  # Clear VF register
                for row in range(height):
                    sprite_byte = self.memory[self.i + row]

                    if self.experimental_optimization:
                        for col in range(0, 8, 2):
                            pixel0 = (sprite_byte >> (7 - col)) & 1
                            pixel1 = (sprite_byte >> (6 - col)) & 1
                            screen_x = (self.v[vx] + col) % 64
                            screen_y = self.v[vy] + row
                            index0 = screen_y * 64 + screen_x
                            index1 = screen_y * 64 + screen_x + 1
                            if pixel0 and self.screen[index0]:
                                self.v[0xF] = 1
                            self.screen[index0] ^= pixel0
                            if pixel1 and self.screen[index1]:
                                self.v[0xF] = 1
                            self.screen[index1] ^= pixel1

                    else:
                        for col in range(8):
                            # pixel = (sprite_byte & (0x80 >> col)) != 0
                            pixel = (sprite_byte >> (7 - col)) & 1
                            screen_x = (self.v[vx] + col) % 64
                            screen_y = (self.v[vy] + row) % 32
                            index = screen_y * 64 + screen_x

                            # Check for collision before XOR
                            if pixel and self.screen[index]:
                                self.v[0xF] = 1

                            # apply XOR to all pixels in the sprite's bounding box
                            self.screen[index] ^= pixel

                        pass

                self.display_dirty = True

            elif opcode & 0xF000 == 0xE000:
                vx = (opcode & 0x0F00) >> 8
                if (
                    opcode & 0x00FF == 0x009E
                ):  # Skip next instruction if key with the value of VX is pressed
                    key = self.v[vx]
                    if self.keypad[key]:
                        self.pc += 2
                elif (
                    opcode & 0x00FF == 0x00A1
                ):  # Skip next instruction if key with the value of VX is not pressed
                    key = self.v[vx]
                    if not self.keypad[key]:
                        self.pc += 2
            elif opcode & 0xF000 == 0xF000:
                vx = (opcode & 0x0F00) >> 8
                if opcode & 0x00FF == 0x0007:  # Set VX to delay timer value
                    self.v[vx] = self.delay_timer
                elif (
                    opcode & 0x00FF == 0x000A
                ):  # Wait for a key press and store the value in VX
                    # Implement key press handling
                    pass
                elif opcode & 0x00FF == 0x0015:  # Set delay timer to VX
                    self.delay_timer = self.v[vx]
                elif opcode & 0x00FF == 0x0018:  # Set sound timer to VX
                    self.sound_timer = self.v[vx]
                elif opcode & 0x00FF == 0x001E:  # Add VX to I
                    self.i += self.v[vx]
                    self.i &= 0xFFFF
                elif (
                    opcode & 0x00FF == 0x0029
                ):  # Set I to the location of the sprite for the character in VX
                    # Implement sprite lookup
                    self.i = self.v[vx] * 5 + 0x50
                    pass
                elif (
                    opcode & 0x00FF == 0x0033
                ):  # Store the binary-coded decimal representation of VX in I, I+1, and I+2
                    # Implement BCD conversion
                    digit = self.v[vx]
                    self.memory[self.i] = digit // 100
                    self.memory[self.i + 1] = (digit % 100) // 10
                    self.memory[self.i + 2] = digit % 10
                    pass
                elif (
                    opcode & 0x00FF == 0x0055
                ):  # Store registers V0 to VX in memory starting at location I
                    for i in range(vx + 1):
                        self.memory[self.i + i] = self.v[i]
                    self.i += vx + 1
                elif (
                    opcode & 0x00FF == 0x0065
                ):  # Read registers V0 to VX from memory starting at location I
                    for i in range(vx + 1):
                        self.v[i] = self.memory[self.i + i]
                    self.i += vx + 1
                else:
                    print(f"Unknown opcode: {hex(opcode)}")

            # Update timers
            if self.delay_timer > 0:
                self.delay_timer -= 1

            if self.sound_timer > 0:

                if not self.is_sound_playing:
                    self.is_sound_playing = True
                    if self.play_audio_callback:
                        self.play_audio_callback(self.is_sound_playing)

                self.sound_timer -= 1

                if self.sound_timer == 0:
                    self.is_sound_playing = False
                    self.play_audio_callback(self.is_sound_playing)

            else:
                # stop the sound
                # self.play_audio_callback(False)
                pass

            if self.display_dirty:
                self.draw_screen()
                self.display_dirty = False

    # Convert screen buffer to display format (replace with your specific implementation)
    def draw_screen(self):

        for y in range(32):
            row_start = y * 64
            for x in range(64):
                # index = y * 64 + x
                pixel_value = self.screen[row_start + x]

                if pixel_value == 1:

                    # if self.use_color_mode:
                    #     (r, g, b) = (
                    #         random.getrandbits(8),
                    #         random.getrandbits(8),
                    #         random.getrandbits(8),
                    #     )
                    # else:
                    #     (r, g, b) = 255, 255, 255

                    self.draw_pixel_callback(x, y, self.scale, True)
                elif pixel_value == 0:
                    # (r, g, b) = 0, 0, 0

                    self.draw_pixel_callback(x, y, self.scale, False)
