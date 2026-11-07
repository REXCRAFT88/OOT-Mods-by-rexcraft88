import pathlib, subprocess, sys, tkinter as tk
from tkinter import filedialog,messagebox
root=tk.Tk();root.withdraw();base=pathlib.Path(__file__).resolve().parent
source=filedialog.askopenfilename(title="Select your ORIGINAL matching Eglantine NUP",filetypes=[("NUP games","*.nup")])
if not source:sys.exit(0)
out=filedialog.asksaveasfilename(title="Choose a NEW patched NUP path",defaultextension=".nup",filetypes=[("NUP games","*.nup")])
if not out:sys.exit(0)
p=pathlib.Path(out);folder=p.with_suffix("").with_name(p.stem+"-Mod")
result=subprocess.run([sys.executable,str(base/"install.py"),"--source",source,"--output",str(folder),"--patched-nup",out],cwd=base)
messagebox.showinfo("Mod build",("Finished. Launch the new NUP: "+out) if result.returncode==0 else "Build failed. Read the console error; the original game was not edited.")
sys.exit(result.returncode)
