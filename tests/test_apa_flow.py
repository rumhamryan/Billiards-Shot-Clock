from unittest.mock import AsyncMock, MagicMock

import pytest

from lib.button_logic import handle_down, handle_make, handle_miss, handle_up
from lib.models import Game_Stats, State_Machine


@pytest.mark.asyncio
async def test_apa_flow_with_game_type_selection():
    # Setup
    state_machine = State_Machine()
    game = Game_Stats()
    hw_module = MagicMock()
    hw_module.render_profile_selection = AsyncMock()
    hw_module.render_skill_level_selection = AsyncMock()
    hw_module.render_game_type_selection = AsyncMock()
    hw_module.enter_idle_mode = AsyncMock()

    # 1. Start in Profile Selection
    state_machine.update_state(State_Machine.PROFILE_SELECTION)
    game.profile_selection_index = 0  # APA is index 0

    # Select APA
    await handle_make(state_machine, game, hw_module)
    assert state_machine.apa_skill_level_p1
    hw_module.render_skill_level_selection.assert_called_with(state_machine, game, 1)

    # 2. Select P1 Skill Level (default 3)
    await handle_make(state_machine, game, hw_module)
    assert state_machine.apa_skill_level_p2
    hw_module.render_skill_level_selection.assert_called_with(state_machine, game, 2)

    # 3. Select P2 Skill Level (default 3)
    await handle_make(state_machine, game, hw_module)

    # CHECK: Should now be in GAME_TYPE_SELECTION, not IDLE
    assert state_machine.apa_game_type_selection
    assert game.temp_setting_value == 1  # Defaults to 9-Ball (1)
    hw_module.render_game_type_selection.assert_called_with(state_machine, game)

    # 4. Toggle to 8-Ball
    await handle_up(state_machine, game, hw_module)
    assert game.temp_setting_value == 0
    await handle_down(state_machine, game, hw_module)
    assert game.temp_setting_value == 1
    await handle_up(state_machine, game, hw_module)
    assert game.temp_setting_value == 0  # 8-Ball

    # 5. Confirm 8-Ball Selection
    await handle_make(state_machine, game, hw_module)

    # CHECK: Should now be in SHOT_CLOCK_IDLE (Game On)
    assert state_machine.shot_clock_idle
    assert game.match_type == "8-Ball"
    hw_module.enter_idle_mode.assert_called_with(state_machine, game)


@pytest.mark.asyncio
async def test_apa_flow_go_back():
    # Setup
    state_machine = State_Machine()
    game = Game_Stats()
    hw_module = MagicMock()
    hw_module.render_profile_selection = AsyncMock()
    hw_module.render_skill_level_selection = AsyncMock()
    hw_module.render_game_type_selection = AsyncMock()

    # Fast forward to Game Type Selection
    state_machine.update_state(State_Machine.APA_GAME_TYPE_SELECTION)
    game.player_2_skill_level = 5  # Assume previously selected

    # Hit Miss (Back)
    await handle_miss(state_machine, game, hw_module)

    # CHECK: Should be back at P2 Skill Selection
    assert state_machine.apa_skill_level_p2
    assert game.temp_setting_value == 5  # Should restore previous value
    hw_module.render_skill_level_selection.assert_called_with(state_machine, game, 2)
