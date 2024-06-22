```python

import pcbnew
board = pcbnew.GetBoard()
[f.SetLocked(True) for f in board.GetFootprints() if f.GetDescription() == "SilicagelHole 1mm"]
``````