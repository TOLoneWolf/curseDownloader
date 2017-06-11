#!/usr/bin/python3
# -*- coding: utf-8 -*-
import appdirs
import argparse
import json
import os
import time
import requests
import shutil
from urllib.parse import urlparse, unquote
from pathlib import Path
from threading import Thread
from tkinter import ttk, filedialog, sys, Tk, N, S, E, W, StringVar, Text, Scrollbar, END
# pip3 install progressbar2 to install this module.
# https://pythonhosted.org/progressbar2/installation.html
from progressbar import Bar, AdaptiveETA, Percentage, ProgressBar


enableTxtProgressBar = True
cursePackDownloaderVersion = "0.3.1.5"
temp_file_name = "curseDownloader-download.temp"
sess = requests.session()
erred_mod_downloads = []
print("Version: " + cursePackDownloaderVersion)


# This try catch is for windows systems since it's dumb and doesn't know when to switch to GUI or Console :/
# code snippets from these nice people for figuring it out. just had to add -
#   "except AttributeError:" block to get it working :)
# https://stackoverflow.com/questions/2883205/how-can-i-freeze-a-dual-mode-gui-and-console-application-using-cx-freeze
# http://sebsauvage.net/python/snyppets/
# https://www.reddit.com/r/learnprogramming/comments/3vq0dm/python_how_can_i_print_text_out_in_the_gui_rather/
class dummyErrorText:
    ''' dummyStream behaves like a stream but does nothing. '''
    def __init__(self): pass

    def write(self, message_data):
        print_text(message_data)

    def read(self, data): pass

    def flush(self): pass

    def close(self): pass

sys.stderr = dummyErrorText()
sys.__stderr__ = dummyErrorText()

try:
    if not sys.stdout.isatty():
        enableTxtProgressBar = False
except AttributeError or IOError:
    class dummyNormalText:
        ''' dummyStream behaves like a stream but does nothing. '''
        def __init__(self): pass

        def write(self, data): pass

        def read(self, data): pass

        def flush(self): pass

        def close(self): pass

    # and now redirect all default streams to this dummyStream:
    sys.stdout = dummyNormalText()
    sys.stdin = dummyNormalText()
    sys.__stdout__ = dummyNormalText()
    sys.__stdin__ = dummyNormalText()
    enableTxtProgressBar = False


compiledExecutable = False
# If in frozen state(aka executable) then use this path, else use original path.
if getattr(sys, 'frozen', False):
    # if frozen, get embedded file
    CA_Certificates = os.path.join(os.path.dirname(sys.executable), 'cacert.pem')
    compiledExecutable = True
else:
    # else just get the default file
    CA_Certificates = requests.certs.where()
# https://stackoverflow.com/questions/15157502/requests-library-missing-file-after-cx-freeze
os.environ["REQUESTS_CA_BUNDLE"] = CA_Certificates


parser = argparse.ArgumentParser(description="Download Curse modpack mods")
parser.add_argument("--manifest", help="manifest.json file from unzipped pack")
parser.add_argument("--nogui", dest="gui", action="store_false", help="Do not use gui to to select manifest")
parser.add_argument("--portable", dest="portable", action="store_true", help="Use portable cache")
args, unknown = parser.parse_known_args()


# Simplify output text for both console and GUI.
def print_text(message):
    message = str(message)
    print(message)  # For the console output
    if args.gui:
        programGui.set_output(message)  # For the GUI output


def get_human_readable(size, precision=2, requestz=-1):
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
    suffix_index = 0
    if requestz == -1:
        while size > 1024 and suffix_index < 4:
            suffix_index += 1  # increment the index of the suffix
            size /= 1024.0  # apply the division
    elif (requestz >= 1 or requestz == 4):
        i = 0
        while i < requestz:
            suffix_index += 1  # increment the index of the suffix
            size /= 1024.0  # apply the division
            i += 1

    return "%s%s" % (str("{:.3g}".format(round(size, 2))), suffixes[suffix_index])


class DownloadUI(ttk.Frame):
    def __init__(self):
        self.root = Tk()
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.parent = ttk.Frame(self.root)
        self.parent.grid(column=0, row=0, sticky=(N, S, E, W))
        self.parent.columnconfigure(0, weight=1)
        self.parent.rowconfigure(0, weight=1)
        ttk.Frame.__init__(self, self.parent, padding=(6, 6, 14, 2))
        self.grid(column=0, row=0, sticky=(N, S, E, W))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self.root.title("Curse Pack Downloader v%s" % cursePackDownloaderVersion)

        self.manifestPath = StringVar()

        chooser_container = ttk.Frame(self)
        self.chooserText = ttk.Label(chooser_container, text="Locate your manifest.json: ")
        chooser_entry = ttk.Entry(chooser_container, textvariable=self.manifestPath)
        self.chooserButton = ttk.Button(chooser_container, text="Browse", command=self.choose_file)
        self.chooserText.grid(column=0, row=0, sticky=W)
        chooser_entry.grid(column=1, row=0, sticky=(E, W), padx=5)
        self.chooserButton.grid(column=2, row=0, sticky=E)
        chooser_container.grid(column=0, row=0, sticky=(E, W))
        chooser_container.columnconfigure(1, weight=1)
        self.downloadButton = ttk.Button(self, text="Download mods", command=self.go_download)
        self.downloadButton.grid(column=0, row=1, sticky=(E, W))

        self.logText = Text(self, state="disabled", wrap="none")
        self.logText.grid(column=0, row=2, sticky=(N, E, S, W))

        self.logScroll = Scrollbar(self, command=self.logText.yview)
        self.logScroll.grid(column=1, row=2, sticky=(N, E, S, W))
        self.logText['yscrollcommand'] = self.logScroll.set

        # *** Progress Bars Frame ***
        progress_bars = ttk.Frame(padding=(6, 2, 14, 2))
        progress_bars.grid(column=0, row=1, sticky=(E, W))
        progress_bars.columnconfigure(1, weight=1)

        # *** Total Un-Pack Progress ***
        self.tl_progressText = ttk.Label(progress_bars, text="Total Unpacking Progress: ")
        self.tl_progressText.grid(column=0, row=0, sticky=E)
        self.tl_progress = ttk.Progressbar(progress_bars, orient="horizontal",
                                           length=200, mode="determinate")
        self.tl_progress.grid(column=1, row=0, sticky=(E, W))
        self.tl_progress["value"] = 0
        self.tl_progress["maximum"] = 100

        # *** Download Progress ***
        self.dl_progressText = ttk.Label(progress_bars, text="Current Download Progress: ")
        self.dl_progressText.grid(column=0, row=1, sticky=E)
        self.dl_progress = ttk.Progressbar(progress_bars, orient="horizontal",
                                           length=200, mode="determinate")
        self.dl_progress.grid(column=1, row=1, sticky=(E, W))
        self.dl_progress["value"] = 0
        self.dl_progress["maximum"] = 100

    def choose_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=(("Json files", "*.json"),),
            initialdir=os.path.expanduser("~"),
            parent=self)
        self.manifestPath.set(file_path)
        # Reset bars if user select old/new manifest.
        programGui.tl_progress["value"] = 0
        programGui.dl_progress["value"] = 0

    def go_download(self):
        t = Thread(target=self.go_download_background)
        t.start()

    def go_download_background(self):
        self.downloadButton.configure(state="disabled")
        self.chooserButton.configure(state="disabled")
        do_download(self.manifestPath.get())
        self.downloadButton.configure(state="enabled")
        self.chooserButton.configure(state="enabled")

    def set_output(self, message):
        self.logText["state"] = "normal"
        self.logText.insert("end", message + "\n")
        self.logText["state"] = "disabled"
        self.logText.see(END)

    def set_manifest(self, file_name):
        self.manifestPath.set(file_name)


class HeadlessUI:
    def set_output(self, message):
        pass


programGui = None


def do_download(manifest):
    if manifest == '':
        print_text("Select a manifest file first!")
        return None
    manifest_path = Path(manifest)
    target_dir_path = manifest_path.parent

    manifest_text = manifest_path.open().read()
    manifest_text = manifest_text.replace('\r', '').replace('\n', '')

    manifest_json = json.loads(manifest_text)

    try:
        if not "minecraftModpack" == manifest_json['manifestType']:
            print_text('Manifest Error. manifestType is not "minecraftModpack"')
            return None
    except KeyError as e:
        print_text('I got a KeyError - reason %s' % str(e))
        print_text("Manifest Error. Make sure you selected a valid pack manifest.json")
        return None

    try:
        override_path = Path(target_dir_path, manifest_json['overrides'])
        minecraft_path = Path(target_dir_path, "minecraft")
        mods_path = minecraft_path / "mods"
    except KeyError as e:
        print_text('I got a KeyError - reason %s' % str(e))
        print_text("Manifest Error. Make sure you selected a valid pack manifest.json")
        return None

    if override_path.exists():
        shutil.move(str(override_path), str(minecraft_path))

    downloader_dirs = appdirs.AppDirs(appname="cursePackDownloader", appauthor="portablejim")
    cache_path = Path(downloader_dirs.user_cache_dir, "curseCache")

    # Attempt to set proper portable data directory if asked for
    if args.portable:
        if getattr(sys, 'frozen', False):
            # if frozen, get embeded file
            cache_path = Path(os.path.join(os.path.dirname(sys.executable), 'curseCache'))
        else:
            if '__file__' in globals():
                cache_path = Path(os.path.dirname(os.path.realpath(__file__)), "curseCache")
            else:
                print_text("Portable data dir not supported for interpreter environment")
                sys.exit(2)

    if not cache_path.exists():
        cache_path.mkdir(parents=True)

    if not minecraft_path.exists():
        minecraft_path.mkdir()

    if not mods_path.exists():
        mods_path.mkdir()

    i = 1
    try:
        i_len = len(manifest_json['files'])
    except KeyError as e:
        print_text('I got a KeyError - reason %s' % str(e))
        print_text("Manifest Error. Make sure you selected a valid pack manifest.json")
        return None

    print_text("Cached files are stored here:\n %s\n" % cache_path)
    print_text("%d files to download" % i_len)
    if args.gui:
        programGui.tl_progress["maximum"] = i_len
    for dependency in manifest_json['files']:
        dep_cache_dir = cache_path / str(dependency['projectID']) / str(dependency['fileID'])
        if dep_cache_dir.is_dir():
            # File is cached
            dep_files = [f for f in dep_cache_dir.iterdir()]
            if len(dep_files) >= 1:
                dep_file = dep_files[0]
                target_file = minecraft_path / "mods" / dep_file.name
                shutil.copyfile(str(dep_file), str(target_file))
                print_text("[%d/%d] %s (cached)" % (i, i_len, target_file.name))

                i += 1
                if args.gui:
                    programGui.tl_progress["value"] = i

                # Cache access is successful,
                # Don't download the file
                continue

        # File is not cached and needs to be downloaded

        temp_mod_file = str(minecraft_path / temp_file_name)
        if Path(temp_mod_file).exists():
            os.remove(temp_mod_file)

        project_response = sess.get("http://minecraft.curseforge.com/projects/%s"
                                    % (dependency['projectID']), stream=True)
        project_response.url = project_response.url.replace('?cookieTest=1', '')
        file_response = sess.get("%s/files/%s/download"
                                 % (project_response.url, dependency['fileID']), stream=True)
        requested_file_sess = sess.get(file_response.url, stream=True)

        remote_url = Path(requested_file_sess.url)
        file_name = unquote(remote_url.name).split('?')[0]  # If query data strip it and return just the file name.
        # print_text(str(requested_file_sess.status_code))
        # print_text(str(requested_file_sess.headers['content-type']))
        if (requested_file_sess.status_code == 404) or (file_name == "download"):
            print_text(str("[%d/%d] " + "Trying to resolve using alternate requesting.") % (i, i_len))

            # If curse website fails to provide correct url try Dries API list.
            # get the json from Dries:
            metabase = "https://cursemeta.dries007.net"
            metaurl = "%s/%s/%s.json" % (metabase, dependency['projectID'], dependency['fileID'])
            r = sess.get(metaurl)
            r.raise_for_status()
            main_json = r.json()
            if "code" in main_json:
                print_text(str("[%d/%d] " + "ERROR FILE MISSING FROM SOURCE") % (i, i_len))
                erred_mod_downloads.append(metaurl.url)
                i += 1
                continue
            fileurl = main_json["DownloadURL"]
            file_name = main_json["FileNameOnDisk"]
            requested_file_sess = sess.get(fileurl, stream=True)

        try:
            full_file_size = int(requested_file_sess.headers.get('content-length'))
            # print_text(str(requested_file_sess.headers['content-length']))
        except TypeError:
            print_text(str("[%d/%d] " + "MISSING FILE SIZE") % (i, i_len))
            full_file_size = 100

        print_text(str("[%d/%d] " + file_name +
                   " (DL: " + get_human_readable(full_file_size) + ")") % (i, i_len))
        time.sleep(0.1)

        with open(temp_mod_file, 'wb') as file_data:
            dl = 0
            widgets = [Percentage(), Bar(), ' ', AdaptiveETA()]
            pbar = ProgressBar(widgets=widgets, maxval=full_file_size)
            if args.gui:
                programGui.dl_progress["maximum"] = full_file_size
            # maybe do something
            if enableTxtProgressBar:
                pbar.start()
            for chunk in requested_file_sess.iter_content(chunk_size=1024):
                if dl < full_file_size:
                    dl += len(chunk)
                elif dl > full_file_size:
                    dl = full_file_size
                if enableTxtProgressBar:
                    pbar.update(dl)
                if args.gui:
                    programGui.dl_progress["value"] = dl
                if chunk:  # filter out keep-alive new chunks
                    file_data.write(chunk)
            if enableTxtProgressBar:
                pbar.finish()
            if args.gui:
                programGui.dl_progress["value"] = 0
            file_data.close()
        shutil.move(temp_mod_file, str(mods_path / file_name))  # Rename from temp to correct file name.

        # Try to add file to cache.
        if not dep_cache_dir.exists():
            dep_cache_dir.mkdir(parents=True)
            shutil.copyfile(str(mods_path / file_name), str(dep_cache_dir / file_name))

        i += 1
        if args.gui:
            programGui.tl_progress["value"] = i

    # This is not available in curse-only packs
    if 'directDownload' in manifest_json:
        i = 1
        i_len = len(manifest_json['directDownload'])
        programGui.set_output("%d additional files to download." % i_len)
        for download_entry in manifest_json['directDownload']:
            if "url" not in download_entry or "filename" not in download_entry:
                programGui.set_output("[%d/%d] <Error>" % (i, i_len))
                i += 1
                continue
            source_url = urlparse(download_entry['url'])
            download_cache_children = Path(source_url.path).parent.relative_to('/')
            download_cache_dir = cache_path / "directdownloads" / download_cache_children
            cache_target = Path(download_cache_dir / download_entry['filename'])
            if cache_target.exists():
                # Cached
                target_file = minecraft_path / "mods" / cache_target.name
                shutil.copyfile(str(cache_target), str(target_file))

                i += 1
                if args.gui:
                    programGui.tl_progress["value"] = i

                # Cache access is successful,
                # Don't download the file
                continue
            # File is not cached and needs to be downloaded
            file_response = sess.get(source_url, stream=True)
            while file_response.is_redirect:
                source = file_response
                file_response = sess.get(source, stream=True)
            programGui.set_output("[%d/%d] %s" % (i, i_len, download_entry['filename']))
            with open(str(minecraft_path / "mods" / download_entry['filename']), "wb") as mod:
                mod.write(file_response.content)

            i += 1
            if args.gui:
                programGui.tl_progress["value"] = i

        if args.gui:
            programGui.tl_progress["value"] = 0

    if len(erred_mod_downloads) is not 0:
        print_text("\n!! WARNING !!\nThe following mod downloads failed.")
        for index in erred_mod_downloads:
            print_text("- " + index)
        # Create log of failed download links to pack manifest directory for user to inspect manually.
        log_file = open(str(target_dir_path / "cursePackDownloaderModErrors.log"), 'w')
        log_file.write("\n".join(str(elem) for elem in erred_mod_downloads))
        log_file.close()
        print_text("See log in manifest directory for list.\n!! WARNING !!\n")
        erred_mod_downloads.clear()

    print_text("Unpacking Complete")
    sess.close()


if args.gui:
    programGui = DownloadUI()
    if args.manifest is not None:
        programGui.set_manifest(args.manifest)
    programGui.root.mainloop()
else:
    programGui = HeadlessUI()
    if args.manifest is not None:
        do_download(args.manifest)
    else:
        if sys.platform == "win32":
            if compiledExecutable:
                print('C:\someFolder\cursePackDownloader.exe '
                      '--portable '
                      '--nogui '
                      '--manifest ["/path/to/manifest.json"]')
                sys.exit()
            else:
                print(
                    'CMD>"path/to/python" "/path/to/downloader.py" '
                    '--portable '
                    '--nogui '
                    '--manifest ["/path/to/manifest.json"]')
                sys.exit()
