import config

from utils_logstdout import logfile
from utils_timebase import tb
from utils_log import LogfileTags

try:
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from mod_hardware import Hardware
        from mod_sensoren import Sensoren
except ImportError:
    pass

WHY_FORWARD = "User Button: Forward to next state"


class Statemachine:
    PREFIX_STATE = "_state_"
    PREFIX_ENTRY = "_entry_"

    def __init__(self, hardware: Hardware, sensoren: Sensoren):
        self._hw = hardware
        self._start_ms = 0
        self._sensoren = sensoren

        self._regenrate_last_fanon_ms = 0
        self._dryfan_list_dew_C = []
        self._dryfan_next_ms = 0
        self._forward_to_next_state = False
        self.statechange_cb = lambda state, new_state, why: state
        # Attention: The three following lines have to match the same state
        self.state_name = "cooldown"
        self.state = self._state_cooldown
        self._entry_cooldown()

    def set_forward_to_next_state(self) -> None:
        self._forward_to_next_state = True
        self.state()

    @property
    def forward_to_next_state(self) -> bool:
        if self._forward_to_next_state:
            self._forward_to_next_state = False
            return True
        return False

    @property
    def duration_ms(self) -> int:
        return tb.now_ms - self._start_ms

    def switch_by_name(self, new_state: str) -> None:
        state_name = f"_state_{new_state}"
        print(f"state_name: '{state_name}'")
        try:
            state_func = getattr(self, state_name)
        except AttributeError as e:
            print(f"WARNING: Unexisting state '{state_name}'!")
            return
        self._switch(state_func, "MQTT intervention")

    def _switch(self, new_state, why: str) -> None:
        assert new_state.__name__.startswith(self.PREFIX_STATE)
        new_state_name = new_state.__name__.replace(self.PREFIX_STATE, "")
        if self.state_name == new_state_name:
            return
        msg = f"'{self.state_name}' -> '{new_state_name}' {why}"
        logfile.log(LogfileTags.SM_STATE, msg, stdout=True)
        self.statechange_cb(self.state_name, new_state_name, why)
        self.state_name = new_state_name
        self.state = new_state
        self._start_ms = tb.now_ms

        new_entry_name = self.PREFIX_ENTRY + new_state_name
        f_entry = getattr(self, new_entry_name)
        f_entry()

    # State: OFF
    def _entry_off(self) -> None:
        self._hw.PIN_GPIO_FAN_AMBIENT.off()
        self._hw.PIN_GPIO_FAN_SILICAGEL.off()
        self._hw.heater.set_power(False)

        self._hw.PIN_GPIO_LED_GREEN.value(1)
        self._hw.PIN_GPIO_LED_RED.value(1)
        self._hw.PIN_GPIO_LED_WHITE.value(1)

    def _state_off(self) -> None:
        if self.forward_to_next_state:
            self._switch(self._state_regenerate, WHY_FORWARD)

    # State: REGENERATE
    def _entry_regenerate(self) -> None:
        self._regenrate_last_fanon_ms = 0
        self._hw.PIN_GPIO_FAN_AMBIENT.off()
        self._hw.PIN_GPIO_FAN_SILICAGEL.off()
        self._hw.heater.set_power(True)

        self._hw.PIN_GPIO_LED_GREEN.value(0)
        self._hw.PIN_GPIO_LED_RED.value(1)
        self._hw.PIN_GPIO_LED_WHITE.value(0)

    def _state_regenerate(self) -> None:
        if self.forward_to_next_state:
            self._switch(self._state_cooldown, WHY_FORWARD)
            return

        # Controller for the fan
        diff_dew_C = self._sensoren.heater_dew_C - self._sensoren.ambient_dew_C
        fan_on = diff_dew_C > config.SM_REGENERATE_DIFF_DEW_C
        self._hw.PIN_GPIO_FAN_AMBIENT.value(fan_on)

        if fan_on:
            self._regenrate_last_fanon_ms = tb.now_ms
            return

        # Do state change if fan was off for a 'long' time.
        if self._sensoren.heater_C < config.SM_REGENERATE_HOT_C:
            self._regenrate_last_fanon_ms = tb.now_ms
            return

        duration_fan_off_ms = tb.now_ms - self._regenrate_last_fanon_ms
        assert duration_fan_off_ms >= 0
        if duration_fan_off_ms > config.SM_REGENERATE_NOFAN_MS:
            why = f"duration_fan_off_ms {duration_fan_off_ms}ms > SM_REGENERATE_NOFAN_MS {config.SM_REGENERATE_NOFAN_MS}ms"
            self._switch(self._state_cooldown, why)

    # State: COOL DOWN
    def _entry_cooldown(self) -> None:
        self._hw.PIN_GPIO_FAN_SILICAGEL.off()
        self._hw.PIN_GPIO_FAN_AMBIENT.off()
        self._hw.heater.set_power(False)

        self._hw.PIN_GPIO_LED_GREEN.value(0)
        self._hw.PIN_GPIO_LED_RED.value(1)
        self._hw.PIN_GPIO_LED_WHITE.value(1)

    def _state_cooldown(self) -> None:
        if self.forward_to_next_state:
            self._switch(self._state_dryfan, WHY_FORWARD)
            return

        heater_C = self._sensoren.heater_C
        if heater_C < config.SM_COOLDOWN_TEMPERATURE_HEATER_C:
            self._switch(
                self._state_dryfan,
                f"heater_C {heater_C:0.1f}C < SM_COOLDOWN_TEMPERATURE_HEATER_C {config.SM_COOLDOWN_TEMPERATURE_HEATER_C:0.1f}C",
            )

    # State: DRY FAN
    def _entry_dryfan(self) -> None:
        self._hw.PIN_GPIO_FAN_SILICAGEL.on()
        self._hw.PIN_GPIO_FAN_AMBIENT.off()
        self._hw.heater.set_power(False)
        self._dryfan_list_dew_C = []
        self._dryfan_next_ms = tb.now_ms

        self._hw.PIN_GPIO_LED_GREEN.value(0)
        self._hw.PIN_GPIO_LED_RED.value(0)
        self._hw.PIN_GPIO_LED_WHITE.value(1)

    def _state_dryfan(self) -> None:
        if self.forward_to_next_state:
            self._switch(self._state_drywait, WHY_FORWARD)
            return

        if tb.now_ms >= self._dryfan_next_ms:
            logfile.log(
                LogfileTags.LOG_INFO,
                f"len={len(self._dryfan_list_dew_C)}, append({self._sensoren.filament_dew_C})",
                stdout=True,
            )
            self._dryfan_next_ms += config.SM_DRYFAN_NEXT_MS
            self._dryfan_list_dew_C.insert(0, self._sensoren.filament_dew_C)

            if len(self._dryfan_list_dew_C) > config.SM_DRYFAN_ELEMENTS:
                reduction_dew_C = (
                    self._dryfan_list_dew_C[-1] - self._dryfan_list_dew_C[0]
                )
                logfile.log(
                    LogfileTags.LOG_INFO,
                    f"reduction_dew_C={reduction_dew_C:0.1f}",
                    stdout=True,
                )
                self._dryfan_list_dew_C.pop()
                if reduction_dew_C < config.SM_DRYFAN_DIFF_DEW_C:
                    why = f"reduction_dew_C {reduction_dew_C:0.1f}C < SM_DRYFAN_DIFF_DEW_C {config.SM_DRYFAN_DIFF_DEW_C:0.1f}C AND filament_dew_C {self._sensoren.filament_dew_C:0.1f}C > SM_DRYFAN_DEW_SET_C {config.SM_DRYFAN_DEW_SET_C:0.1f}C"
                    if self._sensoren.filament_dew_C > config.SM_DRYFAN_DEW_SET_C:
                        self._switch(self._state_regenerate, why)
                        return
                    self._switch(
                        self._state_drywait,
                        why.replace(
                            "C > SM_DRYFAN_DEW_SET_C", "C <= SM_DRYFAN_DEW_SET_C"
                        ),
                    )

    # State: DRY WAIT
    def _entry_drywait(self) -> None:
        self._hw.PIN_GPIO_FAN_SILICAGEL.off()
        self._hw.PIN_GPIO_FAN_AMBIENT.off()
        self._hw.heater.set_power(False)
        self._dry_wait_filament_dew_C = self._sensoren.filament_dew_C

        self._hw.PIN_GPIO_LED_GREEN.value(1)
        self._hw.PIN_GPIO_LED_RED.value(0)
        self._hw.PIN_GPIO_LED_WHITE.value(0)

    def _state_drywait(self) -> None:
        if self.forward_to_next_state:
            self._switch(self._state_off, WHY_FORWARD)
            return

        # diff_dew_C ist positiv wenn der Taupunkt zunimmt
        diff_dew_C = self._sensoren.filament_dew_C - self._dry_wait_filament_dew_C
        switch_to_fan_on = diff_dew_C > config.SM_DRYWAIT_DIFF_DEW_C

        if switch_to_fan_on:
            self._switch(
                self._state_dryfan, f"dew filament increased by {diff_dew_C:0.1f}C"
            )
