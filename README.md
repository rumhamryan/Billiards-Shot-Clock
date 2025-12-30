# Billiards Shot Clock

A high-performance, responsive shot clock for billiards (pool) designed for the Raspberry Pi Pico 2. This project features multiple game profiles (APA, WNT, BCA), a non-blocking asynchronous UI, and a modular event-driven architecture.

## Hardware Requirements

- **Microcontroller**: Raspberry Pi Pico 2
- **Display**: 2.42" OLED (SSD1309 or similar, SPI interface)
- **Audio**: MAX98357A I2S Amplifier
- **Speaker**: 4Ω speaker
- **Buttons**: 4x Momentary Push Buttons (Make, Up, Down, Miss)
- **Power**: 3.7V LiPo Battery
- **Charging**: TP4056 USB-C charging circuit

### Wiring Diagram

| Component | GPIO | Function |
| :--- | :--- | :--- |
| **OLED** | 2 | SPI SCK |
| | 3 | SPI MOSI (sometimes called SDA) |
| | 4 | Reset (RST) |
| | 5 | Chip Select (CS) |
| | 6 | Data/Command (DC) |
| **Audio** | 10 | I2S DIN (SD) |
| | 11 | I2S BCLK (SCK) |
| | 12 | I2S LRC (WS) |
| **Buttons** | 16 | **Make** (Start/Shot Made) |
| | 17 | **Up** (Extension/Navigation) |
| | 18 | **Down** (Navigation) |
| | 19 | **Miss** (End Turn/Navigation) |

---

## Software Architecture

### Key Features
- **Event-Driven Core**: Uses `uasyncio` to manage a central event loop. Logic only runs when an event (Button Press, Timer Tick) occurs, saving power and improving responsiveness.
- **Dedicated Audio**: Audio processing is offloaded to **Core 1** via `_thread` to ensure glitch-free beeps without affecting the UI.
- **Async Interrupts**: Hardware interrupts trigger async tasks, eliminating wasteful polling loops.

### Modular Codebase
The project is split into logical modules for better maintainability:
- `main.py`: The main entry point, initializing the event loop and background tasks.
- `lib/hardware_config.py`: Centralized hardware constants (Pins, OLED regions).
- `lib/models.py`: State Machine and Game Statistics data structures.
- `lib/display.py`: Hardware abstraction layer for rendering to OLED.
- `lib/audio.py`: Hardware abstraction layer for playing Audio.
- `lib/button_interrupt.py`: Handles hardware IRQs and debouncing, converting physical presses into async events.
- `lib/button_logic.py`: Pure logic layer defining game rules and state transitions.

---

## How to Use

1. **Profile Selection**: On boot, use **Up/Down** to cycle through profiles (APA, WNT, BCA, Timeouts). Press **Make** to select.
2. **Shot Clock**:
   - **Make**: Stops the timer and resets it for the next shot.
   - **Up**: Uses an extension (if available for the selected profile).
   - **Miss**: Ends the turn and increments the inning counter.
3. **Game Menu**: Press **Miss** while the clock is idle to access settings:
   - Adjust Inning Counter.
   - Adjust Rack Counter.
   - Toggle Mute (Speaker).

---

## Development & Installation

### Prerequisites
- [MicroPython](https://micropython.org/download/RPI_PICO/) installed on the Pico.
- All files from the `lib/` folder must be uploaded to the Pico's `/lib` directory.
- `beep.wav` must be uploaded to the root directory.

### Installation
1. Clone this repository.
2. Copy all `.py` files and `lib/` directory to your Pico using Thonny or `rshell`.
3. The Pico will run `main.py` automatically on boot.

### Debugging
The system prints button events and state transitions to the REPL for easy troubleshooting during assembly.
