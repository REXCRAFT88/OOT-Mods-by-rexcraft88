"""Configure a compatible Hero Mode Add-on ZIP; never edits a game or save."""
import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import struct
import zipfile

ADDRESS = 0x4EA4000
MAGIC = int.from_bytes(b'STM1', 'little')
BUILD_ID = 'E0F3CCFAF50065AE4EA01EB5AEB13B1A45DA3348'
DEFAULTS = dict(schema_version=1, capacity_percent=100, regeneration_percent=100,
                cost_percent=100, regeneration_delay=1.25, hud_offset_x=0, hud_offset_y=24)
LIMITS = dict(capacity_percent=(50, 400), regeneration_percent=(25, 400),
              cost_percent=(25, 200), regeneration_delay=(0, 5),
              hud_offset_x=(-400, 400), hud_offset_y=(-200, 200))

def validate(values):
    if not isinstance(values, dict):
        raise ValueError('Settings must be a JSON object')
    if set(values) - set(DEFAULTS):
        raise ValueError('Unknown settings: ' + ', '.join(sorted(set(values) - set(DEFAULTS))))
    settings = dict(DEFAULTS, **values)
    if type(settings['schema_version']) is not int or settings['schema_version'] != 1:
        raise ValueError('Unsupported settings schema')
    for key, (lo, hi) in LIMITS.items():
        value = settings[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not lo <= value <= hi:
            raise ValueError(f'{key} must be between {lo} and {hi}')
    return settings

def encode_settings(values):
    s = validate(values)
    cost = s['cost_percent'] / 100
    floats = [20*s['capacity_percent']/100, s['regeneration_delay'], 24*s['regeneration_percent']/100,
              12*cost, 10*cost, 8*cost, 8*cost, 4*cost, .5, .75,
              8*cost, 12*cost, 18*cost, 20*cost, 1, 1.1, 1.5, 1.8, 2, 2*cost,
              s['hud_offset_x'], s['hud_offset_y']]
    return struct.pack('<22fII', *floats, MAGIC, 1)

def patch_ips(data, settings):
    if data[:5] != b'IPS32':
        raise ValueError('Expected the current IPS32 sidecar')
    result = bytearray(data)
    at, hits = 5, 0
    while data[at:at+4] != b'EEOF':
        if at+6 > len(data):
            raise ValueError('Truncated IPS file')
        address, size = struct.unpack_from('>IH', data, at)
        at += 6
        if not size or at+size > len(data):
            raise ValueError('Unsupported or truncated IPS record')
        if address == ADDRESS + 0x100:
            if size != 96 or struct.unpack_from('<II', data, at+88) != (MAGIC, 1):
                raise ValueError('Unsupported stamina config block')
            result[at:at+size] = encode_settings(settings)
            hits += 1
        at += size
    if hits != 1:
        raise ValueError('Requires the configurable Hero Mode with Stamina release (Beta6 or newer)')
    return bytes(result)

def configure_addon(source, output, settings):
    settings = validate(settings)
    source, output = Path(source).resolve(), Path(output).resolve()
    checksum = output.with_name(output.stem+'-SHA256.txt')
    if source == output or output.exists() or checksum.exists():
        raise ValueError('Choose a NEW output ZIP; the input is never overwritten')
    with zipfile.ZipFile(source) as src:
        names = src.namelist()
        if len(names)>4096 or any(i.file_size>512*1024*1024 for i in src.infolist()) or sum(i.file_size for i in src.infolist())>2*1024*1024*1024:
            raise ValueError('ZIP exceeds the supported Add-on size')
        if len(names) != len(set(names)) or any(PurePosixPath(n).is_absolute() or '..' in PurePosixPath(n).parts or '\\' in n or ':' in n for n in names):
            raise ValueError('Unsafe or duplicate ZIP paths')
        ips_names = [n for n in names if n.endswith('/exefs/'+BUILD_ID+'.ips')]
        if len(ips_names) != 1:
            raise ValueError('Select a single compatible Prepared Add-on ZIP')
        ips_name = ips_names[0]
        edited = patch_ips(src.read(ips_name), settings)
        root = ips_name.rsplit('/exefs/', 1)[0]
        metadata = root + '/mod-info.json'
        receipt = json.loads(src.read(metadata))
        for entry in receipt['files']:
            if entry['path'] == 'exefs/' + BUILD_ID + '.ips':
                entry['sha256'] = hashlib.sha256(edited).hexdigest()
        receipt['stamina_settings'] = settings
        replacements = {ips_name:edited, root+'/stamina-settings.json':json.dumps(settings, indent=2).encode(),
                        metadata:json.dumps(receipt, indent=2).encode()}
        with zipfile.ZipFile(output, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as dest:
            for name in names:
                if name.endswith('/'):
                    continue
                dest.writestr(name, replacements.pop(name) if name in replacements else src.read(name))
            for name, value in replacements.items():
                dest.writestr(name, value)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    checksum.write_text(digest+'  '+output.name+'\n')
    return output

def gui():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    root = tk.Tk()
    root.title('Hero Mode — Stamina Settings')
    root.resizable(False, False)
    frame = ttk.Frame(root, padding=18)
    frame.grid()
    ttk.Label(frame, text='Choose the configurable Prepared Add-on ZIP, then save a new ZIP.\nImport the new ZIP in Lichii and restart the game.').grid(row=0, columnspan=2, pady=(0, 12))
    labels = [('capacity_percent','Stamina capacity (%)'), ('regeneration_percent','Regeneration rate (%)'),
              ('cost_percent','Action/shield costs (%)'), ('regeneration_delay','Regeneration delay (seconds)'),
              ('hud_offset_x','HUD offset right (layout units)'), ('hud_offset_y','HUD offset up (layout units)')]
    variables = {}
    for row, (key, label) in enumerate(labels, 1):
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky='w', pady=4)
        variables[key] = tk.StringVar(value=str(DEFAULTS[key]))
        ttk.Spinbox(frame, from_=LIMITS[key][0], to=LIMITS[key][1], textvariable=variables[key], width=12).grid(row=row, column=1)
    def preset(capacity):
        for key, var in variables.items():
            var.set(str(capacity if key=='capacity_percent' else DEFAULTS[key]))
    buttons = ttk.Frame(frame)
    buttons.grid(row=7, columnspan=2, pady=10)
    ttk.Button(buttons, text='Default', command=lambda:preset(100)).pack(side='left', padx=4)
    ttk.Button(buttons, text='125% stamina', command=lambda:preset(125)).pack(side='left', padx=4)
    ttk.Button(buttons, text='150% stamina', command=lambda:preset(150)).pack(side='left', padx=4)
    def save():
        try:
            settings = validate({k:float(v.get()) for k,v in variables.items()})
            source = filedialog.askopenfilename(title='Select configurable Prepared Add-on ZIP', filetypes=[('ZIP','*.zip')])
            if not source:
                return
            target = filedialog.asksaveasfilename(title='Save NEW configured Add-on ZIP', initialfile='OOT-Hero-Mode-Custom-Stamina.zip', defaultextension='.zip', filetypes=[('ZIP','*.zip')])
            if not target:
                return
            configure_addon(source, target, settings)
            messagebox.showinfo('Add-on ready', 'Disable the old Hero Mode copy. Import this NEW ZIP through Lichii Add-ons and restart:\n'+target)
        except (ValueError, OSError, zipfile.BadZipFile, KeyError) as e:
            messagebox.showerror('Cannot create Add-on', str(e))
    ttk.Button(frame, text='Choose ZIP and save settings…', command=save).grid(row=8, columnspan=2, pady=8)
    ttk.Label(frame, text='More capacity keeps the visual bar sized to heart containers.\nPositive HUD Y moves upward. No game/save files are edited.').grid(row=9, columnspan=2)
    root.mainloop()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input')
    parser.add_argument('--output')
    parser.add_argument('--config')
    args = parser.parse_args()
    if not any((args.input, args.output, args.config)):
        gui()
    elif not all((args.input, args.output, args.config)):
        parser.error('--input, --output and --config are required together')
    else:
        configure_addon(args.input, args.output, json.loads(Path(args.config).read_text(encoding='utf-8-sig')))
