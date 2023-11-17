from utils_constants import DURATION_MIN_MS, DURATION_S_MS

MEASURE_INTERVAL_MS = const(10000)

HEATER_BOARD_MAX_C = const(110.0)

# Statemachine
SM_REGENERATE_DIFF_ABS_G_KG = const(10.0)
SM_REGENERATE_HOT_C = HEATER_BOARD_MAX_C - 5.0
SM_REGENERATE_NOFAN_MS = 15 * DURATION_S_MS
SM_REGENERATE_MAX_DEW_C_ABOVE_AMBIENT_C = 5.0

SM_COOLDOWN_TEMPERATURE_HEATER_C = HEATER_BOARD_MAX_C - 50.0

SM_DRYWAIT_DIFF_ABS_G_KG = const(0.5)
SM_DRYWAIT_ABS_G_KG = 4.0 # auf diesen Feuchtigkeitslevel wird getrocknet, 4.0 g/kg entspricht ca. dewpoint 0.0 C

# Nach dem dryfan steigt im drywait die Filamentfeuchte wieder an falls das Silikagel vorher noch getrocknet hat. 
# Es ist Sinnvoll erst dann zu regenerieren, falls nicht mehr getrocknet wurde. Falls der Anstieg der Feuchte langsamer ist 
# als temp_minslope_regenerate_g_kg_ms, so wird in regenerate gewechselt.
temp_minslope_regenerate_g_kg_ms = 0.25 / (10.0 * DURATION_MIN_MS) # kann hier eingestellt werden
SM_DRYWAIT_MINTIME_BACK_REGENERATE_MS =  int( SM_DRYWAIT_DIFF_ABS_G_KG / temp_minslope_regenerate_g_kg_ms)
#SM_DRYWAIT_MINTIME_BACK_REGENERATE_MS = 10 * DURATION_MIN_MS

SM_DRYFAN_NEXT_MS = 2 * DURATION_MIN_MS  # Interval of elements in list
SM_DRYFAN_ELEMENTS = const(10)  # 20min = 10 * 2min
SM_DRYFAN_DIFF_ABS_G_KG = 0.0

 