# Optional recovery-drop replacement

Private candidate, not yet gameplay-qualified or published.

The common lottery function at main+`2ef45e0` is called at `784564` from the actual drop/spawn path (`784460`), at `11f7a60`, and by preview/name queries at `2deb5c0` and `2deb6f4`. The initializer at `2deb890` and first-result access at `2deb5c4` establish the returned FixedObjArray: count/capacity at +0/+4, node-pointer array at +8, each name/hash record storing borrowed name pointer at +0 and hash at +8. Nodes are owned by the native result container; the filter must not replace the node pointers or free anything.

The wrapper executes the original lottery, then filters that result list only when the saved option is enabled. Exact ordinary recovery actor names (heart, small/large magic jars, random fairy) become green rupees, with their cached name hashes recomputed by native `1739e0`. It preserves both bare-name and Work/Actor reference forms. The option defaults Off.

Heart containers/pieces, quest rewards, keys, ammo, existing rupees, fixed map actors, bottled inventory and explicit scripted grants are not matched. Fixed fairy fountains are outside this lottery filter. Broader loot/scene and ownership behavior still needs live checks before release. This implementation chooses rupees for replaced recovery results; it does not randomize ammo versus rupees or remove every non-ammo drop family.
