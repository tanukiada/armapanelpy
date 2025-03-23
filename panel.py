from tkinter import *
from tkinter import ttk
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import tkinter as tk
import requests
import psutil
import subprocess
import logging
import os
import re


class App:
    def __init__(self):
        load_dotenv()

        self.USER_NAME = os.getenv("USER_NAME")
        self.PASSWORD = os.getenv("PASSWORD")
        self.LOGGER = logging.getLogger(__name__)
        self.ARMA_PATH = "c:/arma3" # set this to where your arma 3 install is
        self.ARMA_EXE = "arma3server_x64.exe" # don't change this unless you want 32 bit arma for some reason
        self.ARMA_PROCESS = None

    def RunApp(self):
        logging.basicConfig(filename='log.txt', level=logging.INFO)
        App.LOGGER.info('Started')
        root = Tk()
        root.resizable(False, False)
        frm = ttk.Frame(root, padding=10)
        frm.grid()
        ttk.Label(frm, text="Arma Server Panel").grid(column=0, row=0)
        ttk.Label(frm, text="Select Mod List: ").grid(column=0, row=1)
        combobox = ttk.Combobox(frm, state="readonly")
        combobox['values'] = App.GetModLists()
        combobox.grid(column=1, row=1)
        ttk.Button(frm, text="Start Server", command=lambda: App.StartServer(combobox)).grid(column=0, row=2)
        ttk.Button(frm, text="Stop Server", command=App.StopServer).grid(column=1, row=2)
        ttk.Separator(frm, orient='horizontal').grid(column=0, row=4, columnspan=3, sticky='ew')
        ttk.Button(frm, text="Update Mods", command=App.UpdateAllMods).grid(column=0, row=5)
        modIdEntry = ttk.Entry(frm)
        modIdEntry.grid(column=0, row=6)
        ttk.Button(frm, text="Download/Update Mod", command=lambda: App.UpdateMod(App.FindModName(modIdEntry.get()), modIdEntry.get(), App.USER_NAME, App.PASSWORD)).grid(column=1, row=6)
        ttk.Button(frm, text="Download modlist", command=App.DownloadModList).grid(column=1, row=5)

        root.mainloop()

    def GetModLists(self):
        modList = []
        for file in os.listdir(f"{App.ARMA_PATH}/presets"):
            modList.append(file)
        return modList

    def GetAllMods(self):
        mods = []
        for fname in os.listdir(path=App.ARMA_PATH):
            if fname.startswith("@"):
                mods.append(fname)
        if len(mods) > 0:
            return mods
        else:
            return None

    def MakeKeyValueForMetaFile(self, mod):
        fileKeyValue = {}
        with open(f"{App.ARMA_PATH}/{mod}/meta.cpp") as f:
            fileContent = f.read()
        key_values = fileContent.splitlines()
        for key_value in key_values:
            key, value = key_value.split("=")
            key = key.strip()
            value = value.strip()
            fileKeyValue[key] = value
        return fileKeyValue
        
    def GetModId(self, mod):
        fileKeyValue = App.MakeKeyValueForMetaFile(mod)
        return fileKeyValue['publishedid'].strip(";")

    def GetRemoteTimestamp(self, modID):
        body = {
            'itemcount': 1,
            'publishedfileids[0]': modID
        }
        try:
            steamRequest = requests.post('https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/', data=body)
            steamRequest.raise_for_status()
        except requests.exceptions.HTTPError as error:
            print(error)
            logging.info(error)
        jsonContent = steamRequest.json()
        jsonContent = jsonContent["response"]
        jsonContent = jsonContent["publishedfiledetails"]
        remoteTime = jsonContent[0]["time_updated"]
        return remoteTime

    def GetLocalTimestamp(self, mod):
        timeStamp = os.path.getmtime(f"{App.ARMA_PATH}/{mod}")
        return timeStamp

    def CompareTimeStamps(self, remote, local):
        if remote > local:
            return True
        elif remote <= local:
            return False

    def FindModName(self, modId):
        body = {
            'itemcount': 1,
            'publishedfileids[0]': modId
        }
        try:
            steamRequest = requests.post('https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/', data=body)
            steamRequest.raise_for_status()
        except requests.exceptions.HTTPError as error:
            print(error)
            logging.info(error)
        jsonContent = steamRequest.json()
        jsonContent = jsonContent["response"]
        jsonContent = jsonContent["publishedfiledetails"]
        modName = jsonContent[0]["title"]
        return modName
        
    def UpdateMod(self, mod, modID, USER_NAME, PASSWORD):
        mod = re.sub(r"[=\s_+-\.,\[\]\:\(\)']", "", mod)
        try:
            os.path.exists(f'@{mod}')
        except OSError:
            logging.info(f'{mod} does not exist, creating dir')
            print(f'{mod} does not exist, creating dir')
            os.mkdir(f"{App.ARMA_PATH}/@{mod}")
        subprocess.run(f"DepotDownloader.exe -app 107410 -pubfile {modID} -username {USER_NAME} -password {PASSWORD} -dir {ARMA_PATH}/@{mod}")

    def UpdateAllMods(self):
        mods = App.GetAllMods()
        if mods is None:
            logging.info('No mods found.')
            print("Searching for mods failed..")
        else:
            for mod in mods:
                modID = App.GetModId(mod)
                remoteTime = App.GetRemoteTimestamp(modID)
                localTime = App.GetLocalTimestamp(mod)
                needsUpdate = App.CompareTimeStamps(remoteTime, localTime)
                if needsUpdate:
                    App.UpdateMod(mod, modID, App.USER_NAME, App.PASSWORD)
                    logging.info(f'{mod} updated successfully.')
                    print(f'{mod} updated successfully.')
                else:
                    logging.info(f'{mod} does not need updating.')
                    print(f'{mod} does not need updating.')

    def DownloadModList(self):
        with open('mods.html') as f:
            read_data = f.read()

        soup = BeautifulSoup(read_data, 'html.parser')

        modListName = []
        modListID = []
        modDict = {}

        for modName in soup.find_all(attrs={"data-type" : "DisplayName"}):
            editedModName = re.sub(r"[=\s_+-\.,\[\]\:\(\)']", "", modName.string)
            modListName.append(editedModName)

        for link in soup.find_all('a'):
            mod = re.split(r"=", link.get('href'))[1]
            modListID.append(mod)

        modDict = {key: value for key, value in zip(modListName, modListID)}

        for name, id in modDict.items():
            App.UpdateMod(name, id, App.USER_NAME, App.PASSWORD)
            
    def StartServer(self, combobox):
        with open(f"{App.ARMA_PATH}/presets/{combobox.get()}", encoding="utf-8") as f:
            modString = f.read()
        try:
            App.ARMA_PROCESS = psutil.Popen([f"{App.ARMA_PATH}/{App.ARMA_EXE}", "-name=server", "-filePatching", "-config=server.cfg", "-cfg=basic.cfg", f"-mod={modString}", "-servermod=@AdvancedUrbanRappelling;@AdvancedRappelling;@AdvancedSlingLoading;@AdvancedTowing"])
        except psutil.Error as error:
            stringError = str(error)
            logging.info(stringError)
            print(stringError)

    def StopServer(self):
        App.ARMA_PROCESS.terminate()

App = App()

App.RunApp()