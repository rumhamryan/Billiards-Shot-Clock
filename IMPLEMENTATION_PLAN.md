# Refactoring Plan: Event-Driven Billiards Shot Clock

This document outlines the plan to refactor the current `main.py` from a procedural, nested-loop architecture to a robust, event-driven `asyncio` architecture. This will improve responsiveness, maintainability, and power efficiency.

## 1. Architectural Overview

### Current vs. New Approach
*   **Current (Modal Loops):** The code enters `while True` loops for each state (e.g., `shot_clock()`, `game_menu()`). This blocks execution and makes handling global events (like power-off or interrupts) difficult.
*   **New (Event-Driven):** A single main `asyncio` loop. 
    *   **Inputs:** Trigger async events/callbacks.
    *   **Logic:** A central `handle_input(button)` function determines action based on the current `State_Machine` state.
    *   **Timer:** Runs as a purely background task, updating the model.
    *   **Display:** Updates reactively when the model changes.

## 2. Phase 1: Data Model & State Enhancement

We must ensure that **no state is trapped in local variables**. All persistent data (cursor positions, selected profiles, temporary menu values) must live in `Game_Stats` or `State_Machine`.

### Tasks:
- [ ] **Audit `Game_Stats`**:
    - Add `menu_cursor_index` (int) to track menu position.
    - Add `profile_selection_index` (int) to track the profile selection screen.
    - Add `temp_setting_value` (var) to track values being edited before confirmation.
- [ ] **Audit `State_Machine`**:
    - Verify all necessary states exist: `PROFILE_SELECT`, `IDLE`, `RUNNING`, `PAUSED`, `MENU`, `EDITING_VALUE`.

## 3. Phase 2: Input Handling (The "Driver")

Remove polling (`if button.value():`) inside loops. Use hardware interrupts (`IRQ`) to trigger `asyncio.Event` or callbacks.

### Tasks:
- [ ] **Create `AsyncButton` class**:
    - **Constructor**: Takes Pin ID and a callback function.
    - **IRQ Handler**: Triggers on falling edge, handles minimal debounce logic.
    - **Async Method**: Awaits the debounce, checks state, then calls the specific callback (e.g., `on_make_press`).
- [ ] **Global Input Map**:
    - Map physical buttons to abstract actions: `Action_Primary` (Make), `Action_Up`, `Action_Down`, `Action_Secondary` (Miss).

## 4. Phase 3: The Central Logic Dispatcher

Instead of functions defining the flow, the State defines the flow.

### Tasks:
- [ ] **Create `handle_input(button_type)`**:
    - **Switch on `state_machine.state`**:
        - **If `PROFILE_SELECT`**: Up/Down changes `profile_selection_index`. Make confirms.
        - **If `IDLE`**: Make starts `RUNNING`. Miss opens `MENU`.
        - **If `RUNNING`**: Make resets to `IDLE`. Up adds extension. Miss switches turn.
        - **If `MENU`**: Up/Down moves cursor. Make enters edit mode.
- [ ] **Refactor `timer_worker`**:
    - Ensure it only decrements when state is `RUNNING`.
    - Handle "Time Expired" logic (beep/flash) autonomously.

## 5. Phase 4: Implementation Steps

### Step 4.1: Setup & Initialization
- Initialize `OLED`, `State_Machine`, `Game_Stats`.
- Initialize `AsyncButton` instances linked to the dispatcher.

### Step 4.2: Profile Selection Migration
- **Render**: Create `render_profile_select()`. Call it once on startup and whenever Up/Down is pressed in this state.
- **Logic**: Update `profile_selection_index` in the dispatcher.

### Step 4.3: Main Game Loop Migration (Idle & Running)
- **Render**: Create `render_game_state()`.
- **Logic**:
    - `handle_make`: IDLE -> RUNNING. RUNNING -> IDLE (Reset).
    - `handle_miss`: RUNNING -> IDLE (Switch Player). IDLE -> MENU.
    - `handle_up`: RUNNING -> Add Extension.

### Step 4.4: Menu System Migration
- **Render**: Create `render_menu()`.
- **Logic**:
    - Ensure entering/exiting menu restores the previous game state correctly.

## 6. Phase 5: Testing & Verification

### Tasks:
- [ ] **Debounce Test**: Ensure rapid button presses don't trigger double actions.
- [ ] **State Transition Test**: 
    - Verify `IDLE` -> `RUNNING` -> `IDLE` cycle works repeatedly.
    - Verify `RUNNING` -> `MENU` -> `RUNNING` (Resume) works if applicable, or `IDLE` -> `MENU` -> `IDLE`.
- [ ] **Concurrency Test**: Ensure the timer beeps/flashes even while the user is pressing buttons (non-blocking).
