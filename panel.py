from tkinter import *
from tkinter import ttk
from dotenv import load_dotenv
import requests
import psutil
import os

load_dotenv()

USER_NAME = os.getenv("USER_NAME")
PASSWORD = os.getenv("PASSWORD")
ARMA_PATH = "c:\\arma3" # set this to where your arma 3 install is
ARMA_EXE = "arma3server_x64.exe" # don't change this unless you want 32 bit arma for some reason

def GetModLists():
    modList = []
    for file in os.listdir(f"{ARMA_PATH}\\presets"):
        modList.append(file)
        return modList
        
def GetProcessId():
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == ARMA_EXE:
            return proc.info['pid']

def GetAllMods():
    mods = []
    for fname in os.listdir(path=ARMA_PATH):
        if fname.startswith("@"):
            mods.append(fname)
    return mods

def MakeKeyValueForMetaFile(mod):
    fileKeyValue = {}
    with open(f"{ARMA_PATH}\\{mod}\\meta.cpp") as f:
        fileContent = f.read()
    key_values = fileContent.splitlines()
    for key_value in key_values:
        key, value = key_value.split("=")
        key = key.strip()
        value = value.strip()
        fileKeyValue[key] = value
    return fileKeyValue
    
def GetModId(mod):
    fileKeyValue = MakeKeyValueForMetaFile(mod)
    return fileKeyValue['publishedid'].strip(";")

def GetRemoteTimestamp(modID):
    body = {
        'itemcount': 1,
        'publishedfileids[0]': modID
    }
    steamRequest = requests.post('https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/', data=body)
    jsonContent = steamRequest.json()
    jsonContent = jsonContent["response"]
    jsonContent = jsonContent["publishedfiledetails"]
    remoteTime = jsonContent[0]["time_updated"]
    return remoteTime

def GetLocalTimestamp(mod):
    timeStamp = os.path.getmtime(f"{ARMA_PATH}\\{mod}")
    return timeStamp

def CompareTimeStamps(remote, local):
    if remote > local:
        return True
    elif remote <= local:
        return False
    
def UpdatedMod(mod, modID):
    

def UpdateAllMods():
    mods = GetAllMods()
    for mod in mods:
        modID = GetModId(mod)
        remoteTime = GetRemoteTimestamp(modID)
        localTime = GetLocalTimestamp(mod)
        needsUpdate = CompareTimeStamps(remoteTime, localTime)
        if needsUpdate:
            UpdateMod(mod, modID)
            with open('log.txt', encoding="utf-8") as f:
                f.write(f"{mod} updated!")
        else:
            with open('log.txt', encoding="utf-8") as f:
                f.write(f"{mod} did not need updated.")
        
def StartServer(combobox):
    with open(f"{ARMA_PATH}\\presets\\{combobox.get()}", encoding="utf-8") as f:
        modString = f.read()
    psutil.Popen([f"{ARMA_PATH}\\{ARMA_EXE}", "-name=server", "-filePatching", "-config=server.cfg", "-cfg=basic.cfg", f"-mod={modString}", "-servermod=@AdvancedUrbanRappelling;@AdvancedRappelling;@AdvancedSlingLoading;@AdvancedTowing"])

def StopServer():
    pid = GetProcessId()
    process = psutil.Process(pid)
    process.kill()
    
root = Tk()
root.resizable(False, False)
frm = ttk.Frame(root, padding=10)
frm.grid()
ttk.Label(frm, text="Arma Server Panel").grid(column=0, row=0)
ttk.Label(frm, text="Select Mod List: ").grid(column=0, row=1)
combobox = ttk.Combobox(frm, state="readonly")
combobox['values'] = GetModLists()
combobox.grid(column=1, row=1)
ttk.Button(frm, text="Start Server", command=lambda: StartServer(combobox)).grid(column=0, row=2)
ttk.Button(frm, text="Stop Server", command=StopServer).grid(column=1, row=2)
ttk.Separator(frm, orient='horizontal').grid(column=0, row=3, columnspan=3, sticky='ew')
ttk.Button(frm, text="Update Mods", command=UpdateAllMods).grid(column=0, row=4)
root.mainloop()