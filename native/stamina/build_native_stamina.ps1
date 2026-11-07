$ErrorActionPreference = 'Stop'
$flags = @('--target=aarch64-none-elf','-Oz','-ffreestanding','-ffunction-sections','-fdata-sections','-fno-stack-protector','-fno-jump-tables','-I','outputs/OOT-Test-Kit')
& clang @flags -c work/hero_native_runtime.c -o work/hero_native_runtime.o
if ($LASTEXITCODE) { throw 'Native bridge compilation failed' }
& clang @flags -c outputs/OOT-Test-Kit/hero_core.c -o work/hero_core_runtime.o
if ($LASTEXITCODE) { throw 'Stamina core compilation failed' }
& clang --target=aarch64-none-elf -c work/hero_stamina_runtime.S -o work/hero_stamina_runtime.o
if ($LASTEXITCODE) { throw 'Hook assembly failed' }
& ld.lld --gc-sections --emit-relocs -e stamina_frame -T work/hero_stamina_runtime.ld work/hero_stamina_runtime.o work/hero_native_runtime.o work/hero_core_runtime.o -o work/hero_stamina_runtime.elf
if ($LASTEXITCODE) { throw 'Native linking failed' }
& llvm-objcopy -O binary --only-section=.text work/hero_stamina_runtime.elf work/hero_stamina_runtime.bin
if ($LASTEXITCODE) { throw 'Payload extraction failed' }
& python work/build_stamina_runtime.py
if ($LASTEXITCODE) { throw 'Executable patch generation failed' }
