"""Desktop bootstrap; never opens accounts or reads credentials during setup."""
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk


def check_runtime():
    from playwright.sync_api import sync_playwright
    import win32cred  # Verify bundled native extension without reading the vault.
    with sync_playwright() as pw:
        if not Path(pw.chromium.executable_path).is_file():
            return False
        browser = pw.chromium.launch(headless=True, channel="chromium")
        browser.close()
    return True


def install_browser():
    # Same bundled driver and environment used by playwright's own CLI.
    from playwright._impl._driver import compute_driver_executable, get_driver_env
    node, cli = compute_driver_executable()
    result = subprocess.run(
        [node, cli, "install", "chromium"], env=get_driver_env(),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW, timeout=600,
    )
    if result.returncode:
        raise RuntimeError("No se pudo descargar Chromium. Revisa conexión, espacio y permisos; luego reintenta.")


def prepare(status):
    status("Comprobando componentes…")
    if not check_runtime():
        status("Descargando Chromium oficial. La primera instalación puede tardar varios minutos…")
        install_browser()
        status("Verificando el navegador instalado…")
        if not check_runtime():
            raise RuntimeError("La instalación no dejó un navegador disponible.")


def main():
    root = tk.Tk()
    root.title("Preparación de ARCA RPA")
    root.geometry("580x200")
    status = tk.StringVar(value="Comprobando componentes…")
    ttk.Label(root, textvariable=status, wraplength=540, padding=18).pack()
    progress = ttk.Progressbar(root, mode="indeterminate")
    progress.pack(fill="x", padx=18, pady=8)
    retry = ttk.Button(root, text="Reintentar")
    retry.pack()
    messages = queue.Queue()
    busy = False

    def worker():
        try:
            prepare(lambda value: messages.put(("status", value)))
            messages.put(("ready", None))
        except RuntimeError as exc:
            messages.put(("error", str(exc)))
        except Exception:
            messages.put(("error", "No se pudieron preparar los componentes. Revisa conexión, espacio, permisos y compatibilidad de Windows."))

    def start():
        nonlocal busy
        busy = True
        retry.configure(state="disabled")
        progress.start()
        threading.Thread(target=worker, daemon=True).start()

    def poll():
        nonlocal busy
        try:
            while True:
                kind, value = messages.get_nowait()
                if kind == "status":
                    status.set(value)
                elif kind == "error":
                    busy = False
                    progress.stop()
                    status.set(value)
                    retry.configure(state="normal")
                elif kind == "ready":
                    root.destroy()
                    from main import main as run_app
                    run_app()
                    return
        except queue.Empty:
            pass
        root.after(100, poll)

    def close():
        if busy:
            status.set("Espera a que termine la preparación antes de cerrar (máximo 10 minutos por descarga).")
        else:
            root.destroy()

    retry.configure(command=start)
    root.protocol("WM_DELETE_WINDOW", close)
    start()
    root.after(100, poll)
    root.mainloop()


if __name__ == "__main__":
    if "--check-runtime" in sys.argv:
        try:
            root = tk.Tk(); root.withdraw(); root.destroy()
            sys.exit(0 if check_runtime() else 2)
        except Exception:
            sys.exit(1)
    elif "--install-runtime" in sys.argv:
        try:
            prepare(lambda message: None)
            sys.exit(0)
        except Exception:
            sys.exit(1)
    else:
        main()
