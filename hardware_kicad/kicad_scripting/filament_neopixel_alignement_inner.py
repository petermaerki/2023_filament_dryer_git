import pcbnew


def run():
    pcb = pcbnew.GetBoard()

    # x, y
    # 93, 134, 180degree
    # 93, 138, 180degree
    def align_column(i0: int, count: int, neo_d_x0: float, neo_d_y0: float, neo_d_y: float) -> None:
        
        for i in range(count):

            def position(
                reference: str, x_offset=0.0, y_offset=0.0, orientation=0.0
            ) -> None:
                mod = pcb.FindFootprintByReference(reference)
                mod.SetOrientationDegrees(orientation)
                mod.SetPosition(
                    pcbnew.VECTOR2I_MM(
                        neo_d_x0 + x_offset, neo_d_y0 + y_offset + i * neo_d_y
                    )
                )

            position(reference=f"NeoD{i0+i+1}", orientation=180.0)
            position(
                reference=f"NeoC{i0+i+1}",
                x_offset=-3.37,
                y_offset=0.54,
                orientation=180.0,
            )

    neo_d_y0=119.0
    neo_d_y = 2.9
    align_column(i0=0, count=10, neo_d_x0=91.0, neo_d_y0=neo_d_y0, neo_d_y = neo_d_y)
    align_column(i0=10, count=10, neo_d_x0=113.0, neo_d_y0=neo_d_y0, neo_d_y = neo_d_y)
    align_column(i0=20, count=3, neo_d_x0=101.0, neo_d_y0=neo_d_y0+2.0, neo_d_y = neo_d_y)
    align_column(i0=23, count=3, neo_d_x0=101.0, neo_d_y0=neo_d_y0+20.5, neo_d_y = neo_d_y)

print(f"module was loaded: {__name__}")
