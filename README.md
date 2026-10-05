# Markdown Viewer

A Windows-friendly Markdown reader and HTML exporter built with Python, Tkinter, and ttkbootstrap. Opened files render in the document pane, where you can switch to source editing. Browser preview supports Mermaid diagrams and full HTML styling.

## Run from source

1. Install Python 3.10 or later with **Tcl/Tk** enabled.
2. In this folder, run:

   ```powershell
   py -m pip install -r requirements.txt
   py app.py
   ```

The first time a browser preview is opened, Mermaid.js is loaded from jsDelivr, so an internet connection is needed to render Mermaid diagrams. Standard Markdown rendering in the app and exported HTML otherwise work offline.

## Build a Windows executable

On Windows, install the app dependencies and PyInstaller, then run:

```powershell
py -m pip install -r requirements.txt pyinstaller
py -m PyInstaller --noconfirm --onefile --windowed --name "Markdown Viewer" --icon assets/markdown-viewer.ico --add-data "assets/markdown-viewer.ico;assets" --collect-all markdown app.py
```

The executable will be in `dist/Markdown Viewer.exe`. The `--collect-all markdown` option bundles the parser and its extensions so previews stay rendered in the packaged app. The application also draws its own document icon in the window header.

If previewing or exporting reports that the Markdown parser is missing, install dependencies again with `py -m pip install -r requirements.txt`.
