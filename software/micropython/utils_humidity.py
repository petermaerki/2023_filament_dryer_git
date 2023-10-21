def rel_to_abs(T: float, P: float, RH: float) -> float:
    """Returns absolute humidity given relative humidity.

    Inputs:
    --------
    T : float
        Absolute temperature in units Kelvin (K).
    P : float
        Total pressure in units Pascals (Pa).
    RH : float
        Relative humidity in units percent (%).

    Output:
    --------
    absolute_humidity : float
        Absolute humidity in units [kg water vapor / kg dry air].

    References:
    --------
    1. Sonntag, D. "Advancements in the field of hygrometry". 1994. https://doi.org/10.1127/metz/3/1994/51
    2. Green, D. "Perry's Chemical Engineers' Handbook" (8th Edition). Page "12-4". McGraw-Hill Professional Publishing. 2007.

    Version: 0.0.1
    Author: Steven Baltakatei Sandoval
    License: GPLv3+
    """

    import math

    # Check input types
    assert isinstance(T, float)
    assert isinstance(P, float)
    assert isinstance(RH, float)
    RH = max(0.1, RH)

    # Check input types
    T = float(T)
    P = float(P)
    RH = float(RH)

    # debug
    # print('DEBUG:Input Temperature   (K)  :' + str(T))
    # print('DEBUG:Input Pressure      (Pa) :' + str(P))
    # print('DEBUG:Input Rel. Humidity (%)  :' + str(RH))

    # Set constants and initial conversions
    epsilon = 0.62198  # (molar mass of water vapor) / (molar mass of dry air)
    t = T - 273.15  # Celsius from Kelvin
    P_hpa = P / 100  # hectoPascals (hPa) from Pascals (Pa)

    # Calculate e_w(T), saturation vapor pressure of water in a pure phase, in Pascals
    ln_e_w = (
        -6096 * T**-1
        + 21.2409642
        - 2.711193 * 10**-2 * T
        + 1.673952 * 10**-5 * T**2
        + 2.433502 * math.log(T)
    )  # Sonntag-1994 eq 7 e_w in Pascals
    e_w = math.exp(ln_e_w)
    e_w_hpa = e_w / 100  # also save e_w in hectoPascals (hPa)
    # print('DEBUG:ln_e_w:' + str(ln_e_w))
    # print('DEBUG:e_w:' + str(e_w))

    # Calculate f_w(P,T), enhancement factor for water
    f_w = 1 + (10**-4 * e_w_hpa) / (273 + t) * (
        ((38 + 173 * math.exp(-t / 43)) * (1 - (e_w_hpa / P_hpa)))
        + ((6.39 + 4.28 * math.exp(-t / 107)) * ((P_hpa / e_w_hpa) - 1))
    )  # Sonntag-1994 eq 22.
    # print('DEBUG:f_w:' + str(f_w))

    # Calculate e_prime_w(P,T), saturation vapor pressure of water in air-water mixture, in Pascals
    e_prime_w = f_w * e_w  # Sonntag-1994 eq 18
    # print('DEBUG:e_prime_w:' + str(e_prime_w))

    # Calculate e_prime, vapor pressure of water in air, in Pascals
    e_prime = (RH / 100) * e_prime_w
    # print('DEBUG:e_prime:' + str(e_prime))

    # Calculate r, the absolute humidity, in [kg water vapor / kg dry air]
    r = (epsilon * e_prime) / (P - e_prime)
    # print('DEBUG:r:' + str(r))

    return float(r)


def rel_to_vol(T: float, P: float, RH: float) -> float:
    """Returns volumetric humidity given relative humidity.

    Inputs:
    --------
    T : float
        Absolute temperature in units Kelvin (K).
    P : float
        Total pressure in units Pascals (Pa).
    RH : float
        Relative humidity in units percent (%).

    Output:
    --------
    Y_v : float
        Volumetric humidity in units [kg water vapor / m^3 moist air].

    References:
    --------
    1. Sonntag, D. "Advancements in the field of hygrometry". 1994. https://doi.org/10.1127/metz/3/1994/51
    2. Green, D. "Perry's Chemical Engineers' Handbook" (8th Edition). Page "12-4". McGraw-Hill Professional Publishing. 2007.

    Version: 0.0.1
    Author: Steven Baltakatei Sandoval
    License: GPLv3+
    """

    import math

    # Check input types
    T = float(T)
    P = float(P)
    RH = float(RH)

    # debug
    # print('DEBUG:Input Temperature   (K)  :' + str(T))
    # print('DEBUG:Input Pressure      (Pa) :' + str(P))
    # print('DEBUG:Input Rel. Humidity (%)  :' + str(RH))

    # Set constants and initial conversions
    epsilon = 0.62198  # (molar mass of water vapor) / (molar mass of dry air)
    t = T - 273.15  # Celsius from Kelvin
    P_hpa = P / 100  # hectoPascals (hPa) from Pascals (Pa)
    R_v = 461.525  # R/M_v; units: [J / (kg*K)]
    c_1 = 10**5  # [(g/m^3) / ((1/hPa)*(J/(kg*K))*(K/1))]

    # Calculate e_w(T), saturation vapor pressure of water in a pure phase, in Pascals
    ln_e_w = (
        -6096 * T**-1
        + 21.2409642
        - 2.711193 * 10**-2 * T
        + 1.673952 * 10**-5 * T**2
        + 2.433502 * math.log(T)
    )
    # Sonntag-1994 eq 7; e_w in Pascals
    e_w = math.exp(ln_e_w)
    e_w_hpa = e_w / 100  # also save e_w in hectoPascals (hPa)
    # print('DEBUG:ln_e_w:' + str(ln_e_w))
    # print('DEBUG:e_w:' + str(e_w))

    # Calculate f_w(P,T), enhancement factor for water
    f_w = 1 + (10**-4 * e_w_hpa) / (273 + t) * (
        ((38 + 173 * math.exp(-t / 43)) * (1 - (e_w_hpa / P_hpa)))
        + ((6.39 + 4.28 * math.exp(-t / 107)) * ((P_hpa / e_w_hpa) - 1))
    )
    # Sonntag-1994 eq 22.
    # print('DEBUG:f_w:' + str(f_w))

    # Calculate e_prime_w(P,T), saturation vapor pressure of water in air-water mixture, in Pascals
    e_prime_w = f_w * e_w  # Sonntag-1994 eq 18
    # print('DEBUG:e_prime_w:' + str(e_prime_w))

    # Calculate e_prime, vapor pressure of water in air, in Pascals
    e_prime = (RH / 100) * e_prime_w
    # print('DEBUG:e_prime:' + str(e_prime))

    # Calculate e_prime_hpa, vapor pressure of water in air, in hectoPascals
    e_prime_hpa = e_prime / 100
    # print('DEBUG:e_prime_hpa:' + str(e_prime_hpa))

    # Calculate Z, compressibility constant of moist air
    z_a = 1 - (70 - t) * P_hpa * 10**-8  # Sonntag-1994 eq 3
    z = z_a  # approximation
    # print('DEBUG:z:' + str(z))

    # Calculate d_v, volumetric humidity, in [g water vapor / m^3 moist air]
    d_v = (c_1 * e_prime_hpa) / (z * R_v * T)

    # Calculate Y_v, volumetric humidity, in [kg water vapor / m^3 moist air]
    Y_v = d_v / 1000

    return Y_v


def rel_to_dpt(T: float, P: float, RH: float) -> float:
    """Returns dew point temperature given relative humidity.

    Inputs:
    --------
    T : float
        Absolute temperature in units Kelvin (K).
    P : float
        Total pressure in units Pascals (Pa).
    RH : float
        Relative humidity in units percent (%).

    Output:
    --------
    T_d : float
        Dew point temperature in units Kelvin (K).

    References:
    --------
    1. Sonntag, D. "Advancements in the field of hygrometry". 1994. https://doi.org/10.1127/metz/3/1994/51
    2. Green, D. "Perry's Chemical Engineers' Handbook" (8th Edition). Page "12-4". McGraw-Hill Professional Publishing. 2007.

    Version: 0.0.1
    Author: Steven Baltakatei Sandoval
    License: GPLv3+
    """

    import math

    # Check input types
    assert isinstance(T, float)
    assert isinstance(P, float)
    assert isinstance(RH, float)
    RH = max(0.1, RH)

    # debug
    # print('DEBUG:Input Temperature   (K)  :' + str(T))
    # print('DEBUG:Input Pressure      (Pa) :' + str(P))
    # print('DEBUG:Input Rel. Humidity (%)  :' + str(RH))

    # Set constants and initial conversions
    epsilon = 0.62198  # (molar mass of water vapor) / (molar mass of dry air)
    t = T - 273.15  # Celsius from Kelvin
    P_hpa = P / 100  # hectoPascals (hPa) from Pascals (Pa)

    # Calculate e_w(T), saturation vapor pressure of water in a pure phase, in Pascals
    ln_e_w = (
        -6096 * T**-1
        + 21.2409642
        - 2.711193 * 10**-2 * T
        + 1.673952 * 10**-5 * T**2
        + 2.433502 * math.log(T)
    )  # Sonntag-1994 eq 7; e_w in Pascals
    e_w = math.exp(ln_e_w)
    e_w_hpa = e_w / 100  # also save e_w in hectoPascals (hPa)
    # print('DEBUG:ln_e_w:' + str(ln_e_w))
    # print('DEBUG:e_w:' + str(e_w))

    # Calculate f_w(P,T), enhancement factor for water
    f_w = 1 + (10**-4 * e_w_hpa) / (273 + t) * (
        ((38 + 173 * math.exp(-t / 43)) * (1 - (e_w_hpa / P_hpa)))
        + ((6.39 + 4.28 * math.exp(-t / 107)) * ((P_hpa / e_w_hpa) - 1))
    )  # Sonntag-1994 eq 22.
    # print('DEBUG:f_w:' + str(f_w))

    # Calculate e_prime_w(P,T), saturation vapor pressure of water in air-water mixture, in Pascals
    e_prime_w = f_w * e_w  # Sonntag-1994 eq 18
    # print('DEBUG:e_prime_w:' + str(e_prime_w))

    # Calculate e_prime, vapor pressure of water in air, in Pascals
    e_prime = (RH / 100) * e_prime_w
    # print('DEBUG:e_prime:' + str(e_prime))

    n = 0
    repeat_flag = True
    while repeat_flag == True:
        # print('DEBUG:n:' + str(n))

        # Calculate f_w_td, the enhancement factor for water at dew point temperature.
        if n == 0:
            f = 1.0016 + 3.15 * 10**-6 * P_hpa - (0.074 / P_hpa)  # Sonntag-1994 eq 24
            f_w_td = f  # initial approximation
        elif n > 0:
            t_d_prev = float(t_d)  # save previous t_d value for later comparison
            f_w_td = 1 + (10**-4 * e_w_hpa) / (273 + t_d) * (
                ((38 + 173 * math.exp(-t_d / 43)) * (1 - (e_w_hpa / P_hpa)))
                + ((6.39 + 4.28 * math.exp(-t_d / 107)) * ((P_hpa / e_w_hpa) - 1))
            )  # Sonntag-1994 eq 22.
        # print('DEBUG:f_w_td:' + str(f_w_td))

        # Calculate e, the vapor pressure of water in the pure phase, in Pascals
        e = e_prime / f_w_td  # Sonntag-1994 eq 9 and 20
        # print('DEBUG:e:' + str(e))

        # Calculate y, an intermediate dew point calculation variable
        y = math.log(e / 611.213)
        # print('DEBUG:y:' + str(y))

        # Calculate t_d, the dew point temperature in degrees Celsius
        t_d = (
            13.715 * y
            + 8.4262 * 10**-1 * y**2
            + 1.9048 * 10**-2 * y**3
            + 7.8158 * 10**-3 * y**4
        )  # Sonntag-1994 eq 10
        # print('DEBUG:t_d:' + str(t_d))

        if n == 0:
            # First run
            repeat_flag = True
        else:
            # Test t_d accuracy
            t_d_diff = math.fabs(t_d - t_d_prev)
            # print('DEBUG:t_d     :' + str(t_d))
            # print('DEBUG:t_d_prev:' + str(t_d_prev))
            # print('DEBUG:t_d_diff:' + str(t_d_diff))
            if t_d_diff < 0.01:
                repeat_flag = False
            else:
                repeat_flag = True

        # Calculate T_d, the dew point temperature in Kelvin
        T_d = 273.15 + t_d
        # print('DEBUG:T_d:' + str(T_d))

        if n > 100:
            return T_d  # good enough

        # update loop counter
        n += 1
    return T_d


if __name__ == "__main__":
    pass
