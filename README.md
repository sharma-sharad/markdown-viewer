# Markdown Viewer

A Windows-friendly Markdown reader and HTML exporter built with Python, Tkinter, and ttkbootstrap. It opens Markdown files, lets you edit and save them, and previews rendered HTML (including Mermaid diagrams) in your default browser.

## Run from source

1. Install Python 3.10 or later with **Tcl/Tk** enabled.
2. In this folder, run:

   ```powershell
   py -m pip install -r requirements.txt
   py app.py
   ```

The first time a preview is opened, Mermaid.js is loaded from jsDelivr, so an internet connection is needed to render Mermaid diagrams. Standard Markdown rendering and exported HTML otherwise work offline.

## Build a Windows executable

On Windows, install the app dependencies and PyInstaller, then run:

```powershell
py -m pip install -r requirements.txt pyinstaller
py -m PyInstaller --noconfirm --onefile --windowed --name "Markdown Viewer" --icon assets/markdown-viewer.ico --add-data "assets/markdown-viewer.ico;assets" app.py
```

The executable will be in `dist/Markdown Viewer.exe`. The application also draws its own document icon in the window header.
