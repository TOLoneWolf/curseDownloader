#!/usr/bin/python
# -*- coding: utf-8 -*-


# http://cx-freeze.readthedocs.io/en/latest/distutils.html#build-exe
# http://cx-freeze.readthedocs.io/en/latest/faq.html#using-data-files
from cx_Freeze import setup, Executable
import requests
import sys
import os

# Includes cpcert.pem with package so it can verify with file server.
# http://stackoverflow.com/questions/15157502/requests-library-missing-file-after-cx-freeze
# http://stackoverflow.com/questions/23354628/python-requests-and-cx-freeze
build_exe_options = {
    "include_files": [(requests.certs.where(), 'cacert.pem')]
}

base = None
curseDownloader = "cursePackDownloader"
manifest_updater = "manifest_updater"
executables_list = [Executable("downloader.py", targetName=curseDownloader, base=base),
                    Executable("updater.py", targetName=manifest_updater, base=base)
                    ]

if sys.platform == "win32":
    base = "Win32GUI"  # Makes program work only as GUI on windows.
    curseDownloader += ".exe"
    manifest_updater += ".exe"
    curseDownloaderCLI = "cursePackDownloaderCLI.exe"
    manifest_updaterCLI = "manifest_updaterCLI.exe"
    Python_Path = sys.base_exec_prefix
    os.environ['TCL_LIBRARY'] = Python_Path + "\\tcl\\tcl8.6"
    os.environ['TK_LIBRARY'] = Python_Path + "\\tcl\\tk8.6"
    build_exe_options = {
        "include_files": [(requests.certs.where(), 'cacert.pem'),
                          Python_Path + '\\DLLs\\tcl86t.dll',
                          Python_Path + '\\DLLs\\tk86t.dll'
                          ]
    }
    executables_list = [Executable("downloader.py", targetName=curseDownloader, base=base),
                        Executable("updater.py", targetName=manifest_updater, base=base),
                        Executable("downloader.py", targetName=curseDownloaderCLI, base="Console"),
                        Executable("updater.py", targetName=manifest_updaterCLI, base="Console")
                        ]

setup(
    name='curseDownloader',
    version='0.3.1.5',
    author='portablejim',
    # author_email='',
    # packages=[''],
    # url='',
    license='GNU GENERAL PUBLIC LICENSE Version 3',
    description='Curse Forge Modpack Downloader',
    options={"build_exe": build_exe_options},
    requires=['appdirs', 'requests', 'progressbar2'],
    executables=executables_list
)
