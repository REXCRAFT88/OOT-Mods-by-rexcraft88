# Stamina and HUD settings

Hero Mode with Stamina **Beta6** adds configurable capacity, regeneration, costs and HUD offsets. The default yellow bar is moved **24 layout units upward**, closer to the green magic meter and farther from the D-pad accessory/mask/ocarina/Navi display. “Mask HUD” likely refers to that accessory group.

These settings are applied when the game starts. **There is no in-game settings screen yet.**

## Ready-to-import choices

- **Prepared-Addon.zip:** normal 100% stamina, with the adjusted HUD position.
- **125pct-Prepared-Addon.zip:** 25% more stamina.
- **150pct-Prepared-Addon.zip:** 50% more stamina.

Each is a complete Hero Mode Add-on. Choose **one**, disable/remove the old copy and import the chosen ZIP through Lichii's Add-ons menu. Do not stack the presets. Keep the original game and the built-in FPS fix as described in [installation](INSTALLATION.md).

More stamina increases the gameplay pool. The visual bar still grows with permanent heart containers; a larger pool will not stretch it into neighbouring HUD elements. Current low health still increases costs rather than reducing capacity.

## Custom values

Download `stamina_settings.py` beside the release, or find it inside the optional builder ZIP. It uses only Python's standard library; **Python with Tkinter is needed only for this optional custom tool**. The ready-made presets need no Python or commands.

Double-click the script, or run:

```powershell
py -3 stamina_settings.py
```

1. Set capacity, regeneration and action/shield costs as percentages. Choose the regeneration delay in seconds.
2. Set HUD offsets: positive X moves right; positive Y moves up. These are game layout units, not screen pixels. Y=0 restores the previous bar position; Y=24 is the new default.
3. Click **Choose ZIP and save settings**, choose the compatible Prepared Add-on ZIP, then choose a **new** ZIP filename.
4. Disable/remove the old Hero Mode copy, import the new ZIP in Lichii and restart the game.

The tool never edits the game or saves, never overwrites its input ZIP, and needs no network or administrator access. It also writes a SHA-256 checksum for the new ZIP. Custom files naturally have different hashes from the official presets.

The `stamina-settings.json` inside the ZIP records the choices. **Editing that JSON alone does not change the game:** the tool must also update the binary configuration in the IPS sidecar. This is an Add-on ZIP, not a new game NUP.

For scripted use:

```powershell
py -3 stamina_settings.py --input "Hero-Prepared-Addon.zip" --config "my-settings.json" --output "Hero-Custom.zip"
```

## Defaults and limits

| Setting | Default | Supported range |
| --- | --- | --- |
| Capacity | 100% (20 units/heart) | 50–400% |
| Regeneration | 100% (24 units/second) | 25–400% |
| Action/shield costs | 100% | 25–200% |
| Regeneration delay | 1.25 seconds | 0–5 seconds |
| HUD X offset | 0 | -400 to 400 |
| HUD Y offset | +24 | -200 to 200 |

Cost scaling applies to weapon base costs, rolls/jumps/evasions, shield-hold drain and confirmed block costs. Existing move multipliers, injury scaling and exhausted melee penalties remain in place. More capacity does not automatically increase regeneration; increase its percentage separately if desired. Stamina remains unrestricted outside combat.

Only actions that already consume stamina are scaled; the tool adds no new stamina cost to item use.
