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
- **APA Match Scoring**: Integrated scoring for APA 9-Ball and 8-Ball. Features skill level selection, victory threshold calculation via `lib/rules.json`, and victory notifications.
- **Dedicated Audio**: Audio processing is offloaded to **Core 1** via `_thread` to ensure glitch-free beeps without affecting the UI.
- **Async Interrupts**: Hardware interrupts trigger async tasks, eliminating wasteful polling loops.

---

## How to Use

1. **Profile Selection**: On boot, use **Up/Down** to cycle through profiles (APA, WNT, BCA, Timeouts). Press **Make** to select.
   - **APA**: After selection, use **Up/Down** and **Make** to set the Skill Level for Player 1 and then Player 2. Victory targets are calculated automatically.
2. **Shot Clock**:
   - **Make**: Stops the timer and resets it for the next shot. In **APA** mode, this also increments the shooting player's score.
   - **Up**: Uses an extension (if available for the selected profile).
   - **Miss**: Ends the current turn and switches the shooting player.
   - **Make + Miss (Simultaneous)**: Starts a new rack. This increments the rack counter and resets the clock to the "break shot" duration.
3. **Game Menu**: Press **Miss** while the clock is idle to access settings:
   - **Adjust Score/Inning**: Manually edit Player 1 (Inning) or Player 2 (Rack) values.
   - **Toggle Mute**: Enable/Disable the speaker.
   - **Exit Match**: Return to the profile selection screen.

---

## Victory
When a player reaches their calculated point target in **APA** mode, the screen will flash "VICTORY!" along with the winning player's number. Press **Make** to return to the profile selection menu.

---

## Development & Installation

### Prerequisites
- **MicroPython**: This project requires a specific forked version of MicroPython that includes optimized framebuf support. You can find it here: [micropython-framebuf-fork](https://github.com/rumhamryan/micropython-framebuf-fork).
- All files from the `lib/` folder must be uploaded to the Pico's `/lib` directory.
- `beep.wav` must be uploaded to the root directory.

### Installation
1. Clone this repository.
2. Copy all `.py` files and `lib/` directory to your Pico using Thonny or `rshell`.
3. The Pico will run `main.py` automatically on boot.

### Debugging
The system prints button events and state transitions to the REPL for easy troubleshooting during assembly.
