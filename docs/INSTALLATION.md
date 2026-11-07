# Installation

## Requirements

- Your own matching Eglantine update 131072 NUP, or an extracted folder containing `exefs/` and `romfs/`.
- Python 3.11 or newer, with pip. The supplied packages were built/tested with Python 3.14 on Windows.
- Lichii build-93 was used for testing. Other emulator versions and hardware have not been qualified.
- For a playable patched NUP copy, allow space for another complete game copy plus about 1 GB. The source is never edited.

## What the release ZIP contains

The downloadable ZIP is a **patch builder**, not an import-ready Lichii add-on. Lichii can extract ready-made `exefs/`/`romfs/` add-ons, but it does not run the Python builder or apply this bundle's binary deltas. First generate the files from your matching game source.

## Manual Shield: install through Add-ons

1. Extract the Manual Shield release ZIP and run `Install-Windows.cmd`.
2. Select your original NUP, then choose a filename for the generated **Add-on ZIP**. This creates the checked ExeFS overrides and an importable ZIP; it does not copy the complete NUP.
3. In Lichii, right-click the game > **Configure Game > Add-ons > Import Mod from ZIP**.
4. Select the **generated Add-on ZIP**, enable the mod, click **Apply/OK**, and launch the original game.

You can also use **Import Mod from Folder** and choose the generated folder containing `exefs/`. To build that folder from the command line:

```powershell
py -3 -m pip install -r requirements.txt
py -3 install.py --source "D:/Games/original.nup" --output "D:/Mods/Manual-Shield"
```

Add `--variant manual-shield` when using the full source checkout instead of the single-mod release ZIP.

## Hero Mode: NUP-copy fallback on build-93

1. Extract either Hero Mode release ZIP and run `Install-Windows.cmd`.
2. Select your original NUP and a NEW patched NUP path.
3. Wait for file/hash/read-back verification and launch the NEW NUP.

Build-93 applies ExeFS replacement mods to NUP games, so the standalone shield can use Add-ons. However, its NUP RomFS path still bypasses the normal RomFS patching step. Hero Mode needs those RomFS changes for the HUD/wheel layouts and enemy resources; appearing in the Add-ons list alone does not prove all those changes are loaded. The NUP-copy path keeps the complete Hero Mode working on this tested build. On a loader with verified NUP RomFS override support, the generated Hero Mode folder can be imported instead.

This distinction is visible in the exact build-93 source: [NUP loader](https://github.com/zortos293/Lichii/blob/09b78bd2dfdd279cc81caed2a794ed85062725c9/src/core/loader/nup.cpp), [ExeFS loading](https://github.com/zortos293/Lichii/blob/09b78bd2dfdd279cc81caed2a794ed85062725c9/src/core/loader/deconstructed_rom_directory.cpp), and [RomFS factory](https://github.com/zortos293/Lichii/blob/09b78bd2dfdd279cc81caed2a794ed85062725c9/src/core/file_sys/romfs_factory.cpp).

Configure your controller normally as a Switch Pro Controller. No controller configuration is overwritten.

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
