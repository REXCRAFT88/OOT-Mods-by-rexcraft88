# Hero Core native difference

Core uses the shared stamina core and runtime bridge, private runtime HUD and
existing enemy resource patches. It omits controller_options, manual_controls,
wheel runtime and their native hooks. HUD compilation uses HERO_CORE_ONLY;
wheel-only/no-stamina/combined HUD compilation uses WHEEL_UI_ONLY. Full Hero
with Stamina uses the default shared hud.c behavior.

native_guard_impact.c is invoked from the original accepted guard reaction at
main+27f7d00, using the same preserve/restore entry wrapper as full Hero. It
qualifies resolve_player(action) against the cached player, alive/initialized
and combat flags, then spends the configured base block cost with injury
scaling. It neither requests equipment nor changes guard/target input flags.
The original game's blocking/auto-shield behavior and guard-break limitations
remain. Main's original item/guard/controller-menu bytes are retained.

Shared helpers live in subsdk1 at main+4f85000, ending at main+5005000; the
original main text extent stays3c461d0. Main gets the same5000-byte BSS reserve
used for runtime state/config, not an expanded text segment. The applicable IPS
settings record includes the NSO header offset. Do not move these records into
ultrawide's main alignment-page cave.

The public optional builder reconstructs the exact prepared files from checked
patch manifests; it does not require a native compiler. The native sources and
hooks are supplied for research. Recompiling the composite native module also
requires matching linker symbols, original executable and the development
integration harness; do not mix older absolute-address builds into these files.
