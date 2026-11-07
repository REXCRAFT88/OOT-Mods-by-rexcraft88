import pathlib
import subprocess
import sys
import zipfile


def pack_addon(folder, destination):
    folder, destination = pathlib.Path(folder), pathlib.Path(destination)
    if destination.exists():
        raise ValueError('Choose a new ZIP filename; the destination already exists')
    files = [p for section in ('exefs', 'romfs') for p in (folder / section).rglob('*') if p.is_file()]
    if not files:
        raise ValueError('No generated ExeFS/RomFS mod files found')
    with zipfile.ZipFile(destination, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for p in files:
            archive.write(p, folder.name + '/' + p.relative_to(folder).as_posix())


def main():
    import tkinter as tk
    from tkinter import filedialog, messagebox
    root = tk.Tk()
    root.withdraw()
    base = pathlib.Path(__file__).resolve().parent
    manifests = list((base / 'patches').glob('*/manifest.json'))
    shield_only = len(manifests) == 1 and manifests[0].parent.name == 'manual-shield'
    source = filedialog.askopenfilename(title='Select your ORIGINAL matching Eglantine NUP', filetypes=[('NUP games', '*.nup')])
    if not source:
        return 0
    if shield_only:
        out = filedialog.asksaveasfilename(title='Save a NEW shield Add-on ZIP', initialfile='OOT-Manual-Shield-Addon.zip', defaultextension='.zip', filetypes=[('Add-on ZIP', '*.zip')])
    else:
        out = filedialog.asksaveasfilename(title='Choose a NEW patched NUP path', defaultextension='.nup', filetypes=[('NUP games', '*.nup')])
    if not out:
        return 0
    path = pathlib.Path(out)
    if path.exists() or (not shield_only and path.with_suffix('.addon.zip').exists()):
        messagebox.showerror('Choose a new destination', 'This destination already exists. Select a new filename.')
        return 1
    folder = path.with_suffix('').with_name(path.stem + '-Mod')
    args = [sys.executable, str(base / 'install.py'), '--source', source, '--output', str(folder)]
    if not shield_only:
        args += ['--patched-nup', out]
    result = subprocess.run(args, cwd=base)
    if result.returncode:
        messagebox.showerror('Build failed', 'Read the console error. The original game was not edited.')
        return result.returncode
    if shield_only:
        pack_addon(folder, path)
        messagebox.showinfo('Shield Add-on ready', 'In Lichii: right-click the game > Configure Game > Add-ons > Import Mod from ZIP.\nSelect:\n' + out + '\nEnable it, Apply, and launch your original game.')
    else:
        addon = path.with_suffix('.addon.zip')
        pack_addon(folder, addon)
        messagebox.showinfo('Mod build', 'Finished. On Lichii build-93, launch the new NUP:\n' + out + '\n\nAn Add-on ZIP was also generated for loaders with NUP RomFS override support:\n' + str(addon))
    return 0


if __name__ == '__main__':
    sys.exit(main())
