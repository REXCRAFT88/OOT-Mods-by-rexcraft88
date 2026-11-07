# Installation

## Requirements

- Your own matching Eglantine update 131072 NUP, or an extracted folder containing `exefs/` and `romfs/`.
- Python 3.11 or newer, with pip. The supplied packages were built/tested with Python 3.14 on Windows.
- Lichii build-93 was used for testing. Other emulator versions and hardware have not been qualified.
- For a playable patched NUP copy, allow space for another complete game copy plus about 1 GB. The source is never edited.

## Windows: guided build

1. Download a named release ZIP and extract it completely.
2. Run `Install-Windows.cmd`. It installs the listed Python dependencies, opens a file picker for your original NUP, and asks where to create a new patched game copy.
3. Wait for `Built and verified` and the NUP read-back verification. Launch the NEW NUP in Lichii.
4. Configure your controller normally as a Switch Pro Controller. No emulator controller configuration is overwritten.

The script creates a generated mod folder beside the new NUP. Keep it if you want to inspect or use the overrides separately. Do not launch the original NUP expecting mod-folder overrides: the tested Lichii NUP path bypasses those overrides.

## Command line

From the extracted release folder:

```powershell
py -3 -m pip install -r requirements.txt
py -3 install.py --source "D:/Games/original.nup" --output "D:/Mods/Hero-Mode" --patched-nup "D:/Games/OOT-Hero-Mode.nup"
```

In the full source repository add one of these options:

```text
--variant hero-with-stamina
--variant hero-without-stamina
--variant manual-shield
--variant item-wheel
```

For an extracted game, omit `--patched-nup` and give `--source` the folder containing `exefs/` and `romfs/`. Put the resulting mod folder in the loader's mod-data location only if that loader supports overrides for the game format you use. NSP/XCI files are not direct installer inputs.

The output folder must be new/empty; the patched NUP path must name a new file. Wrong source hashes stop the build before mod files are written. Do not bypass these checks to force another version.

## Settings and controls

Fast GPU accuracy and asynchronous shaders were used for testing. These are suggested test settings, not values written by the mod. See [FEATURES.md](FEATURES.md) for controller labels, costs and behavior.

## Updating, uninstalling and conflicts

Build each version from the original matching source into a new folder/copy. Do not use an already modded NUP as the source. To uninstall, launch the original game or disable the complete mod folder in a loader that supports it. Do not delete saves. The installer does not edit saves or emulator profiles.

Install only one Hero Mode variant. Do not combine it with standalone wheel, shield, stamina, AI balance or PS5 Common-UI replacement files. Their executable/UI/resource paths overlap. A selective manual merge requires rebuilding and validation, not choosing an overwrite order.
