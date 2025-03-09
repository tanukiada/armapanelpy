from tkinter import *
from tkinter import ttk
import psutil
import os

ARMA_PATH = "c:\\arma3" # set this to where your arma 3 install is
ARMA_EXE = "arma3server_x64.exe" # don't change this unless you want 32 bit arma for some reason
modString = "" # global variable for the modstring, empty by default

def GetModLists():
    modList = []
    for file in os.listdir(f"{ARMA_PATH}\\presets"):
        modList.append(file)
        return modList
        
def GetProcessId():
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == ARMA_EXE:
            return proc.info['pid']

def StartServer():
    psutil.Popen([f"{ARMA_PATH}\\{ARMA_EXE}", "-name=server", "-filePatching", "-config=server.cfg", "-cfg=basic.cfg", f"-mod={modString}", "-servermod=@AdvancedUrbanRappelling;@AdvancedRappelling;@AdvancedSlingLoading;@AdvancedTowing"])

def StopServer():
    pid = GetProcessId()
    process = psutil.Process(pid)
    process.kill()
    
root = Tk()
frm = ttk.Frame(root, padding=10)
frm.grid()
ttk.Label(frm, text="Arma Server Panel").grid(column=0, row=0)
ttk.Button(frm, text="Start Server", command=StartServer).grid(column=0, row=2)
ttk.Label(frm, text="Select Mod List: ").grid(column=0, row=1)
combobox = ttk.Combobox(frm, state="readonly")
combobox['values'] = GetModLists()
combobox.grid(column=1, row=1)
ttk.Button(frm, text="Stop Server", command=StopServer).grid(column=2, row=2)
root.mainloop()