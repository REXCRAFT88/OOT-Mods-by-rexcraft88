# Classic HUD Hearts compatibility

Hero stamina and Classic HUD Hearts v1.0.1 replace the same Common HUD texture archive. Installing both separate addons can make stamina black; reversing their order can instead discard Classic HUD's hearts. Emulator load order cannot merge individual textures.

For a combined addon, use the optional **HUD-Compatibility-Tool.zip** download:

1. Extract it. Python and the dependencies in requirements.txt are needed only for this optional tool.
2. Double-click `merge_classic_hud.py`.
3. Select your original matching OOT NUP, the current Hero **with Stamina Prepared Addon ZIP**, and your Classic HUD Hearts ZIP.
4. Choose a new output ZIP. No original file or game is edited.
5. Disable/remove the separate Hero and Classic HUD addons. Import the generated combined ZIP through **Configure Game > Add-Ons > Import Mod from ZIP**, and enable only that combined addon.

The merge restores Hero's independent yellow stamina texture view while retaining the input HUD's existing image payloads and increasing its allocation budget. A merged Classic HUD v1.0.1 build was visually tested: yellow stamina and green magic both rendered correctly. This is a file merge, not general compatibility with every HUD mod. The tool does not distribute Classic HUD assets; use your own copy. Ordinary Prepared Addon installation still needs no commands or Python.
