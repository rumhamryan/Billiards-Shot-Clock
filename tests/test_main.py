import asyncio
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# --- Global Mocks ---
# These must be in place before importing main
sys.modules["machine"] = MagicMock()
sys.modules["framebuf"] = MagicMock()
sys.modules["uasyncio"] = MagicMock()
sys.modules["utime"] = MagicMock()
sys.modules["_thread"] = MagicMock()  # Mock threading to prevent spawning
sys.modules["lib.Pico_OLED_242"] = MagicMock()

# We need to ensure we can import main without side effects executing hard
# main.py creates OLED instance at top level.
with patch("lib.Pico_OLED_242.OLED_2inch42"):
    import main


class TestMain(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Reset globals in main for each test
        main.state_machine.state = main.State_Machine.PROFILE_SELECTION
        main.game = main.Game_Stats()
        # Mock dependencies
        main.audio = MagicMock()
        main.display = MagicMock()
        main.ui = MagicMock()  # Mock UI module

        main.display.draw_text_in_region = MagicMock()
        main.display.display_clear = MagicMock()
        main.display.process_timer_duration = MagicMock(return_value="10")

        # Async methods need AsyncMock or MagicMock(side_effect=coro)
        # Using side_effect with an async function silences "never awaited" warnings.
        async def mock_coro(*args, **kwargs):
            return None

        # UI Mocks
        main.ui.enter_idle_mode = MagicMock(side_effect=mock_coro)
        main.ui.enter_shot_clock = MagicMock(side_effect=mock_coro)
        main.ui.update_timer_display = MagicMock(side_effect=mock_coro)
        main.ui.render_profile_selection = MagicMock(side_effect=mock_coro)
        main.ui.render_menu = MagicMock(side_effect=mock_coro)
        main.ui.render_victory = MagicMock(side_effect=mock_coro)
        main.ui.render_exit_confirmation = MagicMock(side_effect=mock_coro)
        main.ui.render_skill_level_selection = MagicMock(side_effect=mock_coro)
        main.ui.render_game_type_selection = MagicMock(side_effect=mock_coro)
        main.ui.render_wnt_target_selection = MagicMock(side_effect=mock_coro)
        main.ui.render_message = MagicMock(side_effect=mock_coro)

    async def test_timer_worker_countdown(self):
        # Setup state
        main.state_machine.update_state(main.State_Machine.COUNTDOWN_IN_PROGRESS)
        main.game.countdown = 10

        import contextlib

        # Patch the asyncio that main uses
        with (
            patch("main.asyncio.sleep_ms", side_effect=asyncio.CancelledError),
            patch("main.utime.ticks_ms", side_effect=[0, 1500, 3000, 4000, 5000]),
            patch("main.utime.ticks_diff", side_effect=lambda a, b: a - b),
            contextlib.suppress(asyncio.CancelledError),
        ):
            await main.timer_worker()

        # Check if countdown decreased (1500 - 0 > 1000, so yes)
        self.assertEqual(main.game.countdown, 9)
        # Check display update
        main.display.draw_text_in_region.assert_called()  # type: ignore

    async def test_timer_worker_ultimate_pool_match_timer(self):
        # Setup state: Match timer running but SHOT CLOCK IDLE
        main.state_machine.update_state(main.State_Machine.SHOT_CLOCK_IDLE)
        main.game.selected_profile = "Ultimate Pool"
        main.game.match_countdown = 1800
        main.game.match_timer_running = True
        main.game.countdown = 30

        import contextlib

        # Patch the asyncio that main uses
        # Ensure enough ticks_ms side effects
        ticks = [0, 1500, 1500, 1500, 1500, 1500, 1500, 1500]
        with (
            patch("main.asyncio.sleep_ms", side_effect=asyncio.CancelledError),
            patch("main.utime.ticks_ms", side_effect=ticks),
            patch("main.utime.ticks_diff", side_effect=lambda a, b: a - b),
            contextlib.suppress(asyncio.CancelledError),
        ):
            await main.timer_worker()

        # Match timer should decrement
        self.assertLess(main.game.match_countdown, 1800)
        main.ui.update_timer_display.assert_called()  # type: ignore

    async def test_timer_worker_flash(self):
        main.state_machine.update_state(main.State_Machine.COUNTDOWN_COMPLETE)
        main.game.countdown = 0

        import contextlib

        with (
            patch("main.asyncio.sleep_ms", side_effect=asyncio.CancelledError),
            patch("main.utime.ticks_diff", return_value=500),
            patch("main.utime.ticks_ms", return_value=1000),
            contextlib.suppress(asyncio.CancelledError),
        ):
            await main.timer_worker()

        self.assertTrue(
            main.display.draw_text_in_region.called or main.display.display_clear.called  # type: ignore
        )

    async def test_timer_worker_blink(self):
        main.state_machine.update_state(main.State_Machine.PROFILE_SELECTION)

        import contextlib

        with (
            patch("main.asyncio.sleep_ms", side_effect=asyncio.CancelledError),
            patch("main.utime.ticks_diff", return_value=600),
            patch("main.utime.ticks_ms", return_value=1000),
            contextlib.suppress(asyncio.CancelledError),
        ):
            await main.timer_worker()

        # Should call display logic
        self.assertTrue(
            main.display.display_clear.called  # type: ignore
            or main.ui.render_profile_selection.called  # type: ignore
        )

    async def test_main_function(self):
        import contextlib

        with (
            patch("main.asyncio.sleep", side_effect=asyncio.CancelledError),
            patch("main.asyncio.create_task") as mock_task,
            patch("main.timer_worker") as mock_worker,
            contextlib.suppress(asyncio.CancelledError),
        ):
            await main.main()

        main.ui.render_profile_selection.assert_called_once()  # type: ignore
        mock_task.assert_called_once()
        mock_worker.assert_called_once()

    async def test_callbacks(self):
        # Mock logic handler
        with (
            patch("lib.button_logic.handle_make", new_callable=AsyncMock) as mock_make,
            patch("lib.button_logic.handle_up", new_callable=AsyncMock) as mock_up,
            patch("lib.button_logic.handle_down", new_callable=AsyncMock) as mock_down,
            patch("lib.button_logic.handle_miss", new_callable=AsyncMock) as mock_miss,
            patch("machine.Pin") as mock_pin,
        ):
            # Mock pin value to 0 (no simultaneous press)
            mock_pin.return_value.value.return_value = 0

            await main.on_make()
            mock_make.assert_called_once()

            await main.on_up()
            mock_up.assert_called_once()

            await main.on_down()
            mock_down.assert_called_once()

            await main.on_miss()
            mock_miss.assert_called_once()

            # Inactivity check should update
            self.assertIsNotNone(main.inactivity_check)

        async def test_on_make_simultaneous(self):
            with (
                patch(
                    "lib.button_logic.handle_new_rack", new_callable=AsyncMock
                ) as mock_new_rack,
                patch("machine.Pin") as mock_pin,
            ):
                # Mock Pin(MISS_PIN).value() = 1
                mock_pin.return_value.value.return_value = 1
                await main.on_make()

                mock_new_rack.assert_called_once()

                # Releasing miss should now do nothing
                with patch(
                    "lib.button_logic.handle_miss", new_callable=AsyncMock
                ) as mock_miss:
                    await main.on_miss()
                    mock_miss.assert_not_called()

    async def test_hardware_wrapper(self):
        wrapper = main.hw_wrapper
        sm = main.state_machine
        g = main.game

        # Test each wrapper method calls the UI module
        await wrapper.enter_idle_mode(sm, g)
        main.ui.enter_idle_mode.assert_called_once()  # type: ignore

        await wrapper.enter_shot_clock(sm, g)
        main.ui.enter_shot_clock.assert_called_once()  # type: ignore

        await wrapper.update_timer_display(sm, g)
        main.ui.update_timer_display.assert_called_once()  # type: ignore

        await wrapper.render_profile_selection(sm, g)
        main.ui.render_profile_selection.assert_called_once()  # type: ignore

        await wrapper.render_menu(sm, g)
        main.ui.render_menu.assert_called_once()  # type: ignore


if __name__ == "__main__":
    unittest.main()
