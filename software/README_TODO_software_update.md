## Observation

Dryer `Peter 4` did behave differently than the others.
When looking at the filesystem, I observed most of the files as `.py` and `.mpy`.

## Problem

It does not make sense to have `.py` and `.mpy` files together.
If a update installs a `xy.py` it should remove the `xy.mpy` counterpart!

A exception might be `main.py` / `main.mpy`.


## Cause

The last file in the tar file is `config_package_manifest.json`.
This makes sure, that all files have been downloaded.

However, when the update crashes while cleaning up the old files, the not cleaned up file will stay there forever.


