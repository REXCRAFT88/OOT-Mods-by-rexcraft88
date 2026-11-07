$ErrorActionPreference = 'Stop'
$root = 'work/hero-mode-integrated-trial'
$flags = @('--target=aarch64-none-elf','-Oz','-ffreestanding','-ffunction-sections','-fdata-sections','-fno-stack-protector')

& clang @flags -c "$root/src/hero_controls_runtime.c" -o "$root/hero_controls_runtime.o"
if ($LASTEXITCODE) { throw 'Control bridge C compilation failed' }
& clang @flags -c "$root/src/wheel_runtime.c" -o "$root/wheel_runtime_for_subsdk.o"
if ($LASTEXITCODE) { throw 'SubSDK wheel helper compilation failed' }
& clang --target=aarch64-none-elf -c "$root/src/hero_controls_runtime.S" -o "$root/hero_controls_runtime_asm.o"
if ($LASTEXITCODE) { throw 'Setter trampoline assembly failed' }
& ld.lld --gc-sections --undefined=hero_guard_impact_entry --undefined=hero_all_input --undefined=hero_setter_hook --undefined=hero_guard_frame --undefined=hero_as_request_hook --undefined=hero_target_guard_flags --undefined=hero_target_guard_update --emit-relocs -e hero_all_input -T "$root/src/hero_controls.ld" "$root/hero_controls_runtime.o" "$root/wheel_runtime_for_subsdk.o" "$root/hero_controls_runtime_asm.o" -o "$root/hero_controls_runtime.elf"
if ($LASTEXITCODE) { throw 'SubSDK control payload link failed' }
& llvm-objcopy -O binary --only-section=.text "$root/hero_controls_runtime.elf" "$root/hero_controls_runtime.bin"
if ($LASTEXITCODE) { throw 'SubSDK payload extraction failed' }

python "$root/src/update_subsdk_symbols.py"
if ($LASTEXITCODE) { throw 'Cross-module symbol update failed' }
& clang @flags -c "$root/src/wheel_runtime.c" -o "$root/wheel_runtime.o"
if ($LASTEXITCODE) { throw 'rtld wheel compilation failed' }
& clang --target=aarch64-none-elf -c "$root/src/wheel_probe.S" -o "$root/wheel_probe.o"
if ($LASTEXITCODE) { throw 'rtld hook assembly failed' }
& ld.lld --gc-sections --undefined=wheel_update --emit-relocs -e wheel_bind_entry -T "$root/src/wheel_probe.ld" "$root/wheel_probe.o" "$root/wheel_runtime.o" -o "$root/wheel_probe.elf"
if ($LASTEXITCODE) { throw 'rtld wheel payload link failed' }
& llvm-objcopy -O binary --only-section=.text "$root/wheel_probe.elf" "$root/wheel_probe.bin"
if ($LASTEXITCODE) { throw 'rtld payload extraction failed' }

python "$root/build_candidate.py"
if ($LASTEXITCODE) { throw 'Integrated candidate assembly failed' }
