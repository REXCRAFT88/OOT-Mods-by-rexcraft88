> Current native stamina status: see [STAMINA-DEVELOPMENT.md](STAMINA-DEVELOPMENT.md). The notes below preserve earlier research checkpoints and may describe superseded probes. The current test build uses Lichii build-93 and the native stamina patch.

# Research cross-checks

The two Gemini guides under the project's `docs/` directory and the JSON files in `work/database/` are useful research inputs. Their descriptions are not proof that a runtime feature is implemented. This file records differences found while comparing them with this build and live tests.

## Native guard corrections

- `0x972e14` is `movk w9, #8, lsl #16`, constructing an `e50` mask with bit19 and bit8. It does not itself set `e58` bit18.
- `0x7f9b1c` originally loads `PlayerState+0x50`, not `+0x20`. The later instruction at `0x7f9b38` loads `+0x20`.
- `0x4a1cec` checks a PlayerGameParam Boolean within a shared shield predicate. Calling it an automatic shield-draw trigger is unverified and misleading. A broad NOP here enabled the crouch transition, but also changed other equipment callers. The revised candidate preserves it and bypasses the predicate only at the manual transition's tail call, `0x7f9bc8`.
- `0x2e836c4` contributes a logical-input bit to a larger request mask. It is not, by itself, the complete collision arbitrator. Blocked-hit behavior still requires live qualification.
- Live tests confirmed entering `CrouchGuard` (`e58 & 0x40000`) and leaving it when the test guard flag changed. They also exposed that the shield remained on Link's back. Those tests do not establish working shield placement or damage absorption.
- `ExecuteEventPlayerDrawnShieldAfterUseBottle` calls `0x6b6820` with the equipment-user component and slot4. This is a concrete lead for moving the shield into its drawn state. Its integration is being tested.
- Stamina charging, guard break and tired attack effects are not installed by the current shield candidate. The guide's complete-hook diagram is a proposed architecture.

## Data and asset corrections

- The plain `Life` name hash (`0x0355c603`) differs from the verified PlayerStatus Life record ID (`0x31ab5580`). Likewise, the verified MaxLife record is `0xfbe01da1`. Use the actual struct's references; do not interchange name hashes and record IDs, or use either as memory addresses.
- BUIL's pane table is not universally at `0xa00`. That location was qualified for PaSystemController_00. Other layouts require reading their pane-pointer arrays. Treating all 17 words as floats or color fields is unsafe; some contain flags and references.
- The supplied ZBIC package decoded the original NSO, but its compressor's output failed round-trip validation for the modified text. The candidate uses a standard uncompressed NSO text segment with its compression flag cleared and hash updated. Do not assume compression succeeds without testing it.
- Radial coordinates and suggested gauge bindings are design material. Dynamic item filtering, selection handling, new HUD bindings and menu callbacks still need implementation.

## Useful material retained

The extracted shield bone names agree with the original EquipmentUserParam: `Weapon_R` is the equipped shield socket and `Pod_A` is the back socket. The actor, equipment and scene databases can accelerate locating original resources. Validate individual values and inherited defaults before changing them.


## 2026-11-06: shield movement and bomb isolation

User confirms holding L2 raises the shield but locks movement and recenters the camera; targeting alone still raises it. The current candidate is not a completed manual-shield implementation. Native ExecutePlayerCrouchGuard Enter explicitly zeroes motion (calls 9339f0 with zero speed and clears the actor movement vector); its update does not run the ordinary movement handler. The candidate must separate a moving guard pose from this stationary main action. Changing the animation alone does not fix movement.

The player's animation blackboard Bool index 14 is IsEnableGuardAnim. This differs from the native name enum: native enum 22 names IsEnableGuardAnim, enum 12 IsRequestKeepGuard. The native enum strings begin at main+3ee5400 and their 70 signed relative offsets at main+3ee5874. Helper 2efceb0 maps a native enum to an animation blackboard index using the name and a controller virtual lookup at +300. Dark Link call sites 2677fb4 and 2678370 use enum 22 and virtual Bool setter +88. These are Dark Link code, not yet qualified as the player update hook; do not patch them to change Link. Research enum mapping: work/hero-research/player-as-native-bool-enum.json.

User observes bombs fail in the practice area independently of targeting. Treat this as a separate, unconfirmed area/item issue. No explicit bomb prohibition has been established from the inspected DreamWorld dungeon and inherited Banc parameters. Do not change targeting to compensate or describe an arena restriction as confirmed. A comparison with the same inventory in a normal field remains necessary.
