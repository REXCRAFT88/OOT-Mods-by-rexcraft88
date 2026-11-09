# HUD compatibility — Hero with Stamina beta.10

Beta.10 creates its stamina gauge and wheel layout metadata privately during native UI initialization. It supplies **neither Common HUD layout nor Common HUD texture archive**. This avoids the previous texture/layout file replacement conflict. Stamina is a solid yellow bar at full width and half height, spaced below the green magic meter.

## Install with DualSense UI

1. Remove the old Hero version and old combined HUD/Hero addon. Use the original matching game NUP.
2. Import the new **Hero with Stamina beta.10 Prepared Addon ZIP** through Configure Game > Add-Ons > Import Mod from ZIP. Install the whole ZIP, including `subsdk1` and the IPS sidecar.
3. Keep its installed folder name beginning **`00-OOT-Hero`**. This gives Hero's resource-size table priority over `DualSense UI` on the tested alphabetical loader.
4. Install the separate `DualSense UI` mod normally, enable both, and restart.

The complete supplied `dualsense_ui_oot_bf16c.zip` was tested as a **separate addon** in Fritchii v4.1: font and textures unchanged, yellow stamina, green magic, wheel selection/highlight, and wheel use after repeated menu visits. Hero reserves 16 KiB for the replacement font (the old table reserved 14856 bytes). It retains its larger allocations for controller-setting resources. No DualSense assets are distributed in Hero.

Keep the folder prefix when importing or extracting. If your emulator uses a different priority scheme, give Hero's resource-size table priority or merge the allocation tables using the maximum required size for each resource. Simply letting the other mod's entire table replace Hero's can discard other required allocations.

## Limits

This fixes a shared-archive conflict, not every possible mod conflict. Mods changing Bootup, GameData, localized messages, native hooks, or using `subsdk1` still require compatibility work. UI skins that remove/rename stock magic-gauge panes or the stock white texture may not work. The exact original Classic HUD Hearts ZIP was no longer available for a new runtime test; broad skin, equipment, and scene-reload coverage remains limited. FPS/ultrawide code caves remain reserved, but this revision has not had a new ultrawide gameplay test.

The old HUD Compatibility Tool and texture-merger instructions apply to beta.9 and earlier only. Do not run that old texture merger on beta.10; Hero no longer includes the texture archive it expected.

The runtime HUD change is currently released in **Hero with Stamina beta.10**. Other existing release variants retain their documented behavior.
