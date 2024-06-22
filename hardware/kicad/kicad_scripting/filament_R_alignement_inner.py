import pcbnew


def run():
    pcb = pcbnew.GetBoard()

    # x, y
    # 93, 134, 180degree
    # 93, 138, 180degree
    def align_column(i: int, x: float, y: float, orientation=180.0) -> None:
        mod = pcb.FindFootprintByReference(f"PowerR{i+1}")
        mod.SetOrientationDegrees(orientation)
        mod.SetPosition(pcbnew.VECTOR2I_MM(x, y))

    # power_r_y0=119.0
    # power_r_y=2.9
    # align_column(i0=0, count=10, neo_d_x0=91.0, power_r_y0=power_r_y0, power_r_y = power_r_y)
    # align_column(i0=10, count=10, neo_d_x0=113.0, power_r_y0=power_r_y0, power_r_y = power_r_y)
    # align_column(i0=20, count=3, neo_d_x0=101.0, power_r_y0=power_r_y0+2.0, power_r_y = power_r_y)
    y0 = 119.0
    x0 = 89.0
    x_columns = 4
    y_rows_outer = 2
    y_rows_inner = 3
    x_distance_mm = 8.0
    y_inner_mm = 4.0
    y_outer_mm = 18.0
    for x in range(x_columns):
        for y_row_outer in range(y_rows_outer):
            for y_row_inner in range(y_rows_inner):
                i = (
                    x * (y_rows_outer * y_rows_inner)
                    + y_row_outer * (y_row_outer * y_rows_inner)
                    + y_row_inner
                )
                align_column(
                    i=i,
                    x=x0 + x * x_distance_mm,
                    y=y0 + (y_row_outer * y_outer_mm) + (y_row_inner * y_inner_mm),
                )


print(f"module was loaded: {__name__}")
