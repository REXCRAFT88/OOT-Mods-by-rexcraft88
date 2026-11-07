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
    source = filedialog.askopenfilename(title='Select your ORIGINAL matching Eglantine NUP', filetypes=[('NUP games', '*.nup')])
    if not source:
        return 0
    out = filedialog.asksaveasfilename(title='Save a NEW Add-on ZIP', initialfile='OOT-Mod-Addon.zip', defaultextension='.zip', filetypes=[('Add-on ZIP', '*.zip')])
    if not out:
        return 0
    path = pathlib.Path(out)
    if path.exists():
        messagebox.showerror('Choose a new destination', 'This destination already exists. Select a new filename.')
        return 1
    folder = path.with_suffix('').with_name(path.stem + '-Mod')
    args = [sys.executable, str(base / 'install.py'), '--source', source, '--output', str(folder)]
    result = subprocess.run(args, cwd=base)
    if result.returncode:
        messagebox.showerror('Build failed', 'Read the console error. The original game was not edited.')
        return result.returncode
    pack_addon(folder, path)
    messagebox.showinfo('Add-on ready', 'In Lichii build95: right-click the ORIGINAL game > Configure Game > Add-ons > Import Mod from ZIP.\nSelect:\n' + out + '\nEnable the mod and the built-in Dynamic FPS fix, Apply, and launch your original game.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
