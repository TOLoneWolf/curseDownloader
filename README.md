# Curseforge Minecraft Modpack Downloader


A simple script to download mods from a CurseForge Minecraft modpack.

## Source Script Requirements

- Python 3.4+
- appdirs
- requests
- python-tk
- progressbar2

## Setup For Source Script

### Linux
- Debian based  
`sudo apt-get install python3 python3-tk python3-pip`  
- `pip3 install -r requirements.txt`

 - #### How to use source

    - Find the modpack you want from the [CurseForge modpack list](http://www.curse.com/modpacks/minecraft)
    - Unzip the download. There should be a manifest.json file.
    - Run `<python> </path/to/downloader.py> --manifest </path/to/manifest.json file>`
  
 - #### Compiled Executable

    - Find the modpack you want from the [CurseForge modpack list](http://www.curse.com/modpacks/minecraft)
    - Unzip the download. There should be a manifest.json file.
    - Run `</path/to/downloader> --manifest </path/to/manifest.json file>`

### Windows
 - #### Compiled Executable
   #### Accepted Arguments

 	- `CMD> C:\someFolder\cursePackDownloader.exe --portable --nogui --manifest ["/path/to/manifest.json"]`

 	- portable - makes the downloader cache downloads in a sub folder of current directory it is inside.
 	 	
 	 	ex: `CMD> C:\someFolder\cursePackDownloader.exe --portable`
 	 	ex folder: C:\someFolder\curseCache

 	- manifest - provides commandline option to select manifest.json file.
 	
 	 	ex: `CMD> C:\someFolder\cursePackDownloader.exe --manifest [/path/to/manifest.json]`

 	- nogui - runs prgram in commandline only, and must include the manifest argument as well.
 	 	
 	 	ex: `CMD> C:\someFolder\cursePackDownloader.exe --nogui --manifest [/path/to/manifest.json]`

  #### Python Source Script
  download and install python http://www.python.org/downloads/windows/

  take note of the install directory.

  Open a command prompt and run the following (replace python_directory with your path).
  
  `<python_directory\Scripts\pip3.exe> install appdirs progressbar2`

  #### Accepted Arguments

   - CMD> `"path/to/python" "/path/to/downloader.py" --portable --nogui --manifest ["/path/to/manifest.json"]`

   - portable - makes the downloader cache downloads in a sub folder of current directory it is inside.
       
       ex: `CMD> C:\Python34\python.exe ["/path/to/downloader.py"] --portable`
       
       ex folder: C:\someFolder\curseCache

   - manifest - provides commandline option to select manifest.json file.
       
       ex:`CMD> /path/to/<python> ["/path/to/downloader.py"] --manifest ["/path/to/manifest.json"]`

   - nogui - runs program in commandline only, and manifest argument must be provided as well.
       
       ex: `CMD> /path/to/<python> ["/path/to/downloader.py"] --nogui --manifest ["/path/to/manifest.json"]`

