"""Markdown Viewer — a desktop Markdown reader and HTML exporter."""
from __future__ import annotations

import html
import os
import re
import struct
import sys
import tempfile
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
except ImportError as exc:
    raise SystemExit("Install dependencies with: python -m pip install -r requirements.txt") from exc

APP_NAME = "Markdown Viewer"
MERMAID_SCRIPT = "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"


def markdown_to_html(source: str, title: str = "Markdown Viewer") -> str:
    """Convert Markdown to a self-contained themed HTML page (Mermaid uses CDN)."""
    try:
        import markdown
        body = markdown.markdown(source, extensions=["extra", "sane_lists", "toc", "fenced_code"])
    except ImportError:
        body = "<pre>" + html.escape(source) + "</pre>"
    body = re.sub(r"<pre><code class=\"language-mermaid\">(.*?)</code></pre>",
                  lambda m: '<pre class="mermaid">' + m.group(1) + '</pre>', body, flags=re.S)
    safe_title = html.escape(title)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{safe_title}</title><script src="{MERMAID_SCRIPT}"></script><script>mermaid.initialize({{startOnLoad:true,theme:'neutral',securityLevel:'strict'}});</script>
<style>*{{box-sizing:border-box}}body{{margin:0;background:#f5f7fb;color:#202b3c;font:16px/1.7 'Segoe UI',Arial,sans-serif}}main{{max-width:980px;margin:42px auto;padding:42px 56px;background:white;border:1px solid #e2e8f0;border-radius:18px;box-shadow:0 12px 38px #13274412}}h1,h2,h3{{line-height:1.25;color:#182942;margin-top:1.7em}}h1{{margin-top:0;font-size:2.3em}}a{{color:#4263eb}}blockquote{{border-left:4px solid #748ffc;margin:1em 0;padding:.4em 1em;color:#596579;background:#f8f9ff}}pre{{overflow:auto;background:#101828;color:#e5edf8;padding:18px;border-radius:10px}}code{{font-family:Consolas,monospace}}:not(pre)>code{{background:#eef2f7;padding:2px 5px;border-radius:4px}}table{{border-collapse:collapse;width:100%}}th,td{{text-align:left;border:1px solid #dce3ec;padding:9px 12px}}th{{background:#f3f6fa}}img{{max-width:100%}}hr{{border:0;border-top:1px solid #e2e8f0}}.mermaid{{display:flex;justify-content:center;background:#fff;color:#202b3c}}@media(max-width:700px){{main{{margin:12px;padding:24px}}}}</style></head><body><main>{body}</main></body></html>'''


class MarkdownViewer:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1280x820")
        self.root.minsize(900, 600)
        icon_path = Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "assets" / "markdown-viewer.ico"
        if icon_path.exists():
            try: self.root.iconbitmap(str(icon_path))
            except tk.TclError: pass
        self.path: Path | None = None
        self.dirty = False
        self.preview_path: Path | None = None
        self.style = ttk.Style(theme="flatly")
        self.style.configure("Top.TFrame", background="#172b4d")
        self.style.configure("TopTitle.TLabel", background="#172b4d", foreground="white", font=("Segoe UI", 17, "bold"))
        self.style.configure("TopSub.TLabel", background="#172b4d", foreground="#bdc9dc", font=("Segoe UI", 9))
        self.style.configure("PanelTitle.TLabel", font=("Segoe UI", 11, "bold"), foreground="#344563")
        self.style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=(14, 9))
        self._build()
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self.root.bind("<Control-o>", lambda _: self.open_file())
        self.root.bind("<Control-s>", lambda _: self.save_file())
        self.root.bind("<Control-Shift-s>", lambda _: self.export_html())
        self.root.bind("<Control-n>", lambda _: self.new_file())

    def _build(self):
        self.root.configure(background="#f5f7fb")
        top = ttk.Frame(self.root, style="Top.TFrame", padding=(24, 17))
        top.pack(fill="x")
        icon = tk.Canvas(top, width=42, height=42, bg="#172b4d", highlightthickness=0)
        icon.pack(side="left", padx=(0, 13))
        icon.create_rectangle(8, 4, 34, 38, fill="#ffffff", outline="")
        icon.create_polygon(26, 4, 34, 12, 26, 12, fill="#97b6ff", outline="")
        icon.create_line(13, 19, 29, 19, fill="#4263eb", width=2)
        icon.create_line(13, 24, 29, 24, fill="#4263eb", width=2)
        icon.create_line(13, 29, 24, 29, fill="#4263eb", width=2)
        labels = ttk.Frame(top, style="Top.TFrame"); labels.pack(side="left")
        ttk.Label(labels, text="Markdown Viewer", style="TopTitle.TLabel").pack(anchor="w")
        ttk.Label(labels, text="READ  ·  PREVIEW  ·  EXPORT", style="TopSub.TLabel").pack(anchor="w", pady=(2, 0))
        actions = ttk.Frame(top, style="Top.TFrame"); actions.pack(side="right")
        ttk.Button(actions, text="＋  Open file", bootstyle="light", command=self.open_file).pack(side="left", padx=5)
        ttk.Button(actions, text="Save", bootstyle="secondary-outline", command=self.save_file).pack(side="left", padx=5)
        ttk.Button(actions, text="Export HTML  ↗", style="Accent.TButton", bootstyle="primary", command=self.export_html).pack(side="left", padx=(5, 0))

        bar = ttk.Frame(self.root, padding=(22, 12)); bar.pack(fill="x")
        self.file_label = ttk.Label(bar, text="Untitled.md", font=("Segoe UI", 10, "bold")); self.file_label.pack(side="left")
        ttk.Label(bar, text="  /  Markdown document", foreground="#8792a2").pack(side="left")
        self.status = ttk.Label(bar, text="Ready", foreground="#697586"); self.status.pack(side="right")

        panes = ttk.Panedwindow(self.root, orient="horizontal")
        panes.pack(fill="both", expand=True, padx=22, pady=(0, 15))
        left = ttk.Frame(panes); right = ttk.Frame(panes)
        panes.add(left, weight=1); panes.add(right, weight=1)
        for panel, title, subtitle in ((left, "MARKDOWN", "Source text"), (right, "PREVIEW", "Rendered in your browser")):
            heading = ttk.Frame(panel); heading.pack(fill="x", pady=(0, 9))
            ttk.Label(heading, text=title, style="PanelTitle.TLabel").pack(side="left")
            ttk.Label(heading, text=subtitle, foreground="#8792a2", font=("Segoe UI", 9)).pack(side="right")
        editorbox = ttk.Frame(left); editorbox.pack(fill="both", expand=True)
        self.editor = tk.Text(editorbox, wrap="word", undo=True, font=("Cascadia Code", 11), padx=16, pady=14,
                              bg="#ffffff", fg="#27364b", insertbackground="#4263eb", relief="flat",
                              highlightthickness=1, highlightbackground="#dfe5ee", highlightcolor="#748ffc",
                              spacing1=2, spacing3=3)
        scroll = ttk.Scrollbar(editorbox, command=self.editor.yview); self.editor.configure(yscrollcommand=scroll.set)
        self.editor.pack(side="left", fill="both", expand=True); scroll.pack(side="right", fill="y")
        card = ttk.Frame(right, padding=22, bootstyle="light"); card.pack(fill="both", expand=True)
        ttk.Label(card, text="Your preview opens in your default browser", font=("Segoe UI", 13, "bold"), bootstyle="dark").pack(anchor="w", pady=(5, 10))
        ttk.Label(card, text="Browser preview supports rich Markdown styling and Mermaid diagrams. Export creates a shareable HTML file with the same rendering.",
                  wraplength=390, justify="left", foreground="#697586").pack(anchor="w", pady=(0, 18))
        ttk.Button(card, text="◉  Open preview", bootstyle="primary", command=self.preview).pack(anchor="w")
        ttk.Separator(card).pack(fill="x", pady=24)
        ttk.Label(card, text="SUPPORTED", font=("Segoe UI", 9, "bold"), foreground="#8792a2").pack(anchor="w", pady=(0, 8))
        ttk.Label(card, text="Headings  ·  Lists  ·  Tables  ·  Code\nLinks  ·  Quotes  ·  Mermaid flowcharts", justify="left", foreground="#526174").pack(anchor="w")
        self.editor.insert("1.0", "# Welcome to Markdown Viewer\n\nOpen a `.md` file or start writing here. Use **Markdown** to format your document.\n\n## Mermaid flowchart\n\n```mermaid\ngraph TD\n    A[Write Markdown] --> B[Preview]\n    B --> C[Export HTML]\n```\n\nChoose **Open preview** to see the rendered document in your browser, or export it as HTML.\n")
        self.editor.edit_modified(False)
        self.editor.bind("<<Modified>>", self._modified)

    def _modified(self, _event=None):
        if self.editor.edit_modified():
            self.dirty = True
            self.editor.edit_modified(False)
            self.status.configure(text="Unsaved changes")

    def _ask_save(self) -> bool:
        if not self.dirty: return True
        answer = messagebox.askyesnocancel(APP_NAME, "Save changes to this Markdown file?")
        if answer is None: return False
        return self.save_file() if answer else True

    def new_file(self):
        if not self._ask_save(): return
        self.path = None; self.editor.delete("1.0", "end"); self.dirty = False
        self.file_label.configure(text="Untitled.md"); self.status.configure(text="New document")

    def open_file(self):
        if not self._ask_save(): return
        chosen = filedialog.askopenfilename(title="Open Markdown", filetypes=[("Markdown files", "*.md *.markdown *.mdown *.mkd"), ("Text files", "*.txt"), ("All files", "*.*")])
        if not chosen: return
        try: source = Path(chosen).read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as exc:
            messagebox.showerror(APP_NAME, f"Could not open file:\n{exc}"); return
        self.path = Path(chosen); self.editor.delete("1.0", "end"); self.editor.insert("1.0", source)
        self.dirty = False; self.file_label.configure(text=self.path.name); self.status.configure(text="Opened successfully")

    def save_file(self):
        if self.path is None:
            chosen = filedialog.asksaveasfilename(title="Save Markdown", defaultextension=".md", filetypes=[("Markdown files", "*.md"), ("All files", "*.*")])
            if not chosen: return False
            self.path = Path(chosen)
        try: self.path.write_text(self.editor.get("1.0", "end-1c"), encoding="utf-8")
        except OSError as exc:
            messagebox.showerror(APP_NAME, f"Could not save file:\n{exc}"); return False
        self.dirty = False; self.file_label.configure(text=self.path.name); self.status.configure(text="Saved"); return True

    def _html(self):
        title = self.path.stem if self.path else "Markdown Viewer"
        return markdown_to_html(self.editor.get("1.0", "end-1c"), title)

    def preview(self):
        try:
            temp = tempfile.NamedTemporaryFile("w", suffix=".html", prefix="markdown_viewer_", encoding="utf-8", delete=False)
            with temp: temp.write(self._html())
            self.preview_path = Path(temp.name)
            webbrowser.open(self.preview_path.as_uri())
            self.status.configure(text="Preview opened in browser")
        except OSError as exc: messagebox.showerror(APP_NAME, f"Could not open preview:\n{exc}")

    def export_html(self):
        suggested = (self.path.stem if self.path else "document") + ".html"
        chosen = filedialog.asksaveasfilename(title="Export as HTML", initialfile=suggested, defaultextension=".html", filetypes=[("HTML files", "*.html"), ("All files", "*.*")])
        if not chosen: return
        try: Path(chosen).write_text(self._html(), encoding="utf-8")
        except OSError as exc: messagebox.showerror(APP_NAME, f"Could not export HTML:\n{exc}"); return
        self.status.configure(text="HTML exported successfully")
        if messagebox.askyesno(APP_NAME, "HTML exported. Open it in your browser now?"):
            webbrowser.open(Path(chosen).as_uri())

    def _close(self):
        if self._ask_save(): self.root.destroy()


def main():
    root = ttk.Window(themename="flatly")
    root.title(APP_NAME)
    MarkdownViewer(root)
    root.mainloop()

if __name__ == "__main__": main()
