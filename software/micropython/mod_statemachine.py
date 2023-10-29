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
        self._dryfan_list_abs_g_kg = []
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
        self._hw.PIN_GPIO_FAN_FILAMENT.off()
        self._hw.PIN_GPIO_FAN_BOX.off()
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
        self._hw.PIN_GPIO_FAN_FILAMENT.off()
        self._hw.PIN_GPIO_FAN_BOX.off()

        self._hw.PIN_GPIO_LED_GREEN.value(0)
        self._hw.PIN_GPIO_LED_RED.value(1)
        self._hw.PIN_GPIO_LED_WHITE.value(0)

    def _state_regenerate(self) -> None:
        if self.forward_to_next_state:
            self._switch(self._state_cooldown, WHY_FORWARD)
            return

        # Controller for the fan
        diff_abs_g_kg = self._sensoren.heater_abs_g_kg - self._sensoren.ambient_abs_g_kg
        fan_on = (
            diff_abs_g_kg > config.SM_REGENERATE_DIFF_ABS_G_KG
            or self._sensoren.heater_dew_C > self._sensoren.ambient_C - 4.0
        )
        self._hw.PIN_GPIO_FAN_AMBIENT.value(fan_on)

        # Do heat if humidity in heater is not to high
        heat_power_on = self._sensoren.heater_dew_C < self._sensoren.ambient_C + 4.0
        self._hw.heater.set_power(heat_power_on)

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
        self._hw.PIN_GPIO_FAN_FILAMENT.off()
        self._hw.PIN_GPIO_FAN_BOX.off()
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
        self._hw.PIN_GPIO_FAN_FILAMENT.on()
        self._hw.PIN_GPIO_FAN_BOX.on()
        self._hw.PIN_GPIO_FAN_AMBIENT.off()
        self._hw.heater.set_power(False)
        self._dryfan_list_abs_g_kg = []
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
                f"len={len(self._dryfan_list_abs_g_kg)}, append({self._sensoren.filament_abs_g_kg})",
                stdout=True,
            )
            self._dryfan_next_ms += config.SM_DRYFAN_NEXT_MS
            self._dryfan_list_abs_g_kg.insert(0, self._sensoren.filament_abs_g_kg)

            if len(self._dryfan_list_abs_g_kg) > config.SM_DRYFAN_ELEMENTS:
                reduction_abs_g_kg = (
                    self._dryfan_list_abs_g_kg[-1] - self._dryfan_list_abs_g_kg[0]
                )
                logfile.log(
                    LogfileTags.LOG_INFO,
                    f"reduction_abs_g_kg={reduction_abs_g_kg:0.1f}",
                    stdout=True,
                )
                self._dryfan_list_abs_g_kg.pop()

                if reduction_abs_g_kg < config.SM_DRYFAN_DIFF_ABS_G_KG:
                    why = f"humidity does not sink fast enough, reduction_abs_g_kg {reduction_abs_g_kg:0.1f} g kg < SM_DRYFAN_DIFF_ABS_G_KG {config.SM_DRYFAN_DIFF_ABS_G_KG:0.1f} g kg"
                    self._switch(self._state_drywait, why)
                    return

                # if reduction_abs_g_kg < config.SM_DRYFAN_DIFF_ABS_G_KG: # humidity does not sink fast enough
                #     why = f"reduction_abs_g_kg {reduction_abs_g_kg:0.1f}C < SM_DRYFAN_DIFF_ABS_G_KG {config.SM_DRYFAN_DIFF_ABS_G_KG:0.1f}C AND sht31_board.measurement_abs_g_kg {sensor_sht31_filament.measurement_abs_g_kg.value:0.1f}C > SM_DRYFAN_ABS_G_KG {config.SM_DRYFANSET_ABS_G_KG:0.1f}C"
                #     if (
                #         sensor_sht31_filament.measurement_abs_g_kg.value
                #         > config.SM_DRYFANSET_ABS_G_KG
                #     ):
                #         self._switch(self._state_regenerate, why)
                #         return
                #     self._switch(
                #         self._state_drywait,
                #         why.replace(
                #             "g kg > SM_DRYFAN_DIFF_ABS_G_KG", "g kg <= SM_DRYFAN_DIFF_ABS_G_KG"
                #         ),
                #     )

    # State: DRY WAIT
    def _entry_drywait(self) -> None:
        self._hw.PIN_GPIO_FAN_FILAMENT.off()
        self._hw.PIN_GPIO_FAN_BOX.off()
        self._hw.PIN_GPIO_FAN_AMBIENT.off()
        self._hw.heater.set_power(False)
        self._dry_wait_filament_abs_g_kg = (
            self._sensoren.sensor_sht31_filament.measurement_abs_g_kg.value
        )
        self._entry_drywait_ms = tb.now_ms

        self._hw.PIN_GPIO_LED_GREEN.value(1)
        self._hw.PIN_GPIO_LED_RED.value(0)
        self._hw.PIN_GPIO_LED_WHITE.value(0)

    def _state_drywait(self) -> None:
        if self.forward_to_next_state:
            self._switch(self._state_off, WHY_FORWARD)
            return

        # diff_abs_g_kg ist positiv wenn der Taupunkt zunimmt
        diff_abs_g_kg = (
            self._sensoren.sensor_sht31_filament.measurement_abs_g_kg.value
            - self._dry_wait_filament_abs_g_kg
        )
        humidity_increased_to_much = diff_abs_g_kg > config.SM_DRYWAIT_DIFF_ABS_G_KG
        time_drywait_ms = tb.now_ms - self._entry_drywait_ms
        time_drywait_not_to_short = (
            time_drywait_ms > config.SM_DRYWAIT_MINTIME_BACK_REGENERATE_MS
        )
        to_humid = self._dry_wait_filament_abs_g_kg > config.SM_DRYWAIT_ABS_G_KG

        # print(f'to_humid {to_humid} time_drywait_not_to_short {time_drywait_not_to_short}')

        if (
            to_humid and time_drywait_not_to_short
        ):  # it is to humid and the humidity does not increase to fast, further dryfan is not useful therefore change to regenerate
            why = f"to humid self._dry_wait_filament_abs_g_kg {self._dry_wait_filament_abs_g_kg:0.1f} > config.SM_DRYWAIT_ABS_G_KG {config.SM_DRYWAIT_ABS_G_KG:0.1f} and drywait not to short time_drywait_ms {time_drywait_ms} > config.SM_DRYWAIT_MINTIME_BACK_REGENERATE_MS {config.SM_DRYWAIT_MINTIME_BACK_REGENERATE_MS}"
            self._switch(self._state_regenerate, why)

        if humidity_increased_to_much:
            why = f"humidity increased to much diff_abs_g_kg {diff_abs_g_kg:0.1f} > config.SM_DRYWAIT_DIFF_ABS_G_KG {config.SM_DRYWAIT_DIFF_ABS_G_KG:0.1f}"
            self._switch(self._state_dryfan, why)
