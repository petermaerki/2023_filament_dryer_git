from utils_constants import DURATION_MIN_MS, DURATION_S_MS

MEASURE_INTERVAL_MS = const(10000)

HEATER_BOARD_MAX = 110.0

# Statemachine
SM_REGENERATE_DIFF_DEW_C = const(10.0)
SM_REGENERATE_HOT_C = HEATER_BOARD_MAX - 5.0
SM_REGENERATE_NOFAN_MS = 17 * DURATION_S_MS # was 30 before

SM_COOLDOWN_TEMPERATURE_HEATER_C = const(60.0)

SM_DRYWAIT_DIFF_DEW_C = const(1.0)

SM_DRYFAN_NEXT_MS = 2 * DURATION_MIN_MS  # Interval of elements in list
SM_DRYFAN_ELEMENTS = const(10)  # 20min = 10 * 2min
SM_DRYFAN_DIFF_DEW_C = 0.0
SM_DRYFAN_DEW_SET_C = -2.0
 