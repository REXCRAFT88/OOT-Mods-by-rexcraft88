# Download verification and security checks

Use the **Prepared-Addon.zip** from this repository's GitHub Releases. It contains game overrides, a README and a file-hash receipt. It does not require a Windows executable, CMD script, Python, administrator privileges or disabling antivirus. Import it through Lichii's Add-ons menu.

The `exefs/main`, `rtld`, `subsdk0` and, in the stamina compatibility update, `sdk` files are modified **AArch64 NSO game modules**. They are not Windows PE applications. RomFS files are game resources. These distinctions explain the files; they are not a guarantee that arbitrary mods are safe.

Optional builder ZIPs contain readable Python/C/assembly source and checked patch data. `Install-Windows.cmd` uses pip to install the four pinned packages in requirements.txt, then opens the local Python builder. The builder verifies the matching source game, writes a separate output, and checks its hashes. It does not need credentials, a remote script, startup registration, a service or administrator access. The prepared Add-on route avoids this installation step entirely.

## Verify a download

Download the matching `-SHA256.txt` asset. In PowerShell run:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath 'C:\Downloads\YOUR-Prepared-Addon.zip'
```

Compare the full hash with the release checksum and the published scan report. A matching hash proves file identity with that release, not absence of malicious behavior. You can also right-click the ZIP and scan it with Microsoft Defender or your own scanner. Do not disable protection to install a mod. Please report the exact asset name, hash and detection name if a scanner flags one.

## Scope and limits

The published report records Microsoft Defender scan results, signature version, archive contents/hashes, Python static analysis and known-vulnerability checks of the pinned direct dependencies. Low-severity developer-script findings are disclosed. Antivirus and static checks can miss threats; this is a maintainer's reproducible check, not an independent security certification. A clean result must not be described as a universal malware-free guarantee.

No release is uploaded to a third-party scanning service as part of these local checks. Optional dependencies are fetched from the configured Python package index only when someone chooses the builder route.

Latest evidence: [security report](security-reports/latest.json).

The optional `stamina_settings.py` tool uses only the Python standard library and edits a compatible Add-on ZIP into a new ZIP. It changes only the bounded96-byte stamina configuration block, settings receipt and checksum; it does not run code from the ZIP or read/write the game or saves. It rejects incompatible config formats, unsafe archive paths, non-finite/out-of-range values and existing output files. The125%/150% preset archives preserve the same executable code as the default release.
