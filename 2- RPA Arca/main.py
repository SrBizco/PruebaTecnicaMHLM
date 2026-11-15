"""Local ARCA services viewer. Does not log, export, or persist portal results."""

from __future__ import annotations

from queue import Empty, Queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from arca_browser import WorkflowResult, run_workflow
from credential_store import (
    CredentialStoreError,
    Profile,
    delete_profile,
    list_profiles,
    save_profile,
)


class ArcaApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Consulta local de servicios ARCA")
        self.root.geometry("730x640")
        self.root.minsize(640, 560)

        self.mode = tk.StringVar(value="manual")
        self.status = tk.StringVar(value="Elige un modo para comenzar.")
        self.messages: Queue[tuple[str, Any]] = Queue()
        self.cuit_continue_event = threading.Event()
        self.services_continue_event = threading.Event()
        self.finish_event = threading.Event()
        self.worker: threading.Thread | None = None
        self.profiles: list[Profile] = []
        self.closing = False
        self.ready_for_continue = False
        self.action_stage: str | None = None
        self.has_results = False

        self._build_ui()
        self.refresh_profiles()
        self._set_mode_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(150, self.poll_messages)

    def _build_ui(self) -> None:
        shell = ttk.Frame(self.root, padding=18)
        shell.pack(fill="both", expand=True)

        ttk.Label(shell, text="Consultar servicios habilitados", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        ttk.Label(
            shell,
            text=(
                "El navegador se abrirá de forma visible en el acceso oficial de ARCA. "
                "La aplicación no guarda la sesión ni los resultados."
            ),
            wraplength=680,
        ).pack(anchor="w", pady=(5, 14))

        modes = ttk.LabelFrame(shell, text="Modo de acceso", padding=10)
        modes.pack(fill="x")
        ttk.Radiobutton(
            modes,
            text="Ingresar manualmente (recomendado)",
            variable=self.mode,
            value="manual",
            command=self._set_mode_ui,
        ).pack(anchor="w")
        ttk.Label(
            modes,
            text="Escribes la CUIT y la clave directamente en el navegador de ARCA.",
            wraplength=650,
        ).pack(anchor="w", padx=(24, 0), pady=(0, 8))
        ttk.Radiobutton(
            modes,
            text="Usar un perfil guardado en Windows (opcional)",
            variable=self.mode,
            value="profiles",
            command=self._set_mode_ui,
        ).pack(anchor="w")
        ttk.Label(
            modes,
            text="El perfil seleccionado completa el formulario oficial; tú revisas y lo envías.",
            wraplength=650,
        ).pack(anchor="w", padx=(24, 0), pady=(0, 4))

        self.profile_frame = ttk.Frame(shell, padding=(0, 10, 0, 8))
        self.profile_frame.pack(fill="x")
        ttk.Label(self.profile_frame, text="Perfil:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.profile_combo = ttk.Combobox(
            self.profile_frame, state="readonly", width=50
        )
        self.profile_combo.grid(row=0, column=1, sticky="ew")
        self.profile_frame.columnconfigure(1, weight=1)
        self.add_profile_button = ttk.Button(
            self.profile_frame, text="Agregar perfil…", command=self.add_profile
        )
        self.add_profile_button.grid(row=0, column=2, padx=(8, 4))
        self.remove_profile_button = ttk.Button(
            self.profile_frame, text="Eliminar", command=self.remove_profile
        )
        self.remove_profile_button.grid(row=0, column=3)

        self.start_button = ttk.Button(shell, text="Abrir ARCA", command=self.start_workflow)
        self.start_button.pack(anchor="w", pady=(4, 10))
        ttk.Label(shell, textvariable=self.status, wraplength=680).pack(anchor="w", pady=(0, 8))

        self.continue_button = ttk.Button(
            shell,
            text="Reintentar consulta",
            command=self.continue_workflow,
            state="disabled",
        )
        self.continue_button.pack(anchor="w", pady=(0, 8))
        self.finish_button = ttk.Button(
            shell,
            text="Cancelar consulta / cerrar navegador",
            command=self.finish_workflow,
            state="disabled",
        )
        self.finish_button.pack(anchor="w", pady=(0, 10))

        result_frame = ttk.LabelFrame(shell, text="Servicios visibles", padding=8)
        result_frame.pack(fill="both", expand=True)
        self.result_text = tk.Text(result_frame, height=12, wrap="word", state="disabled")
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)
        self.result_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        ttk.Label(
            shell,
            text=(
                "Seguridad: no ingreses la clave si la barra del navegador no muestra HTTPS y un dominio oficial de ARCA. "
                "La opción de perfiles persiste la clave en Windows y la utiliza en memoria."
            ),
            wraplength=680,
            foreground="#555555",
        ).pack(anchor="w", pady=(10, 0))

    def _set_mode_ui(self) -> None:
        visible = self.mode.get() == "profiles"
        self.profile_combo.configure(state="readonly" if visible else "disabled")
        self.add_profile_button.configure(state="normal" if visible else "disabled")
        self.remove_profile_button.configure(state="normal" if visible else "disabled")
        if visible:
            self.refresh_profiles()

    def refresh_profiles(self) -> bool:
        current_profile = self._selected_profile()
        previous_id = current_profile.profile_id if current_profile else None
        try:
            self.profiles = list_profiles()
        except CredentialStoreError as exc:
            self.profiles = []
            self.status.set(str(exc))
            self.profile_combo.configure(values=[])
            self.profile_combo.set("")
            return False
        values = [profile.display_name for profile in self.profiles]
        self.profile_combo.configure(values=values)
        selected_index = next(
            (i for i, profile in enumerate(self.profiles) if profile.profile_id == previous_id),
            0 if self.profiles else -1,
        )
        if selected_index >= 0:
            self.profile_combo.current(selected_index)
        else:
            self.profile_combo.set("")
        return True

    def _selected_profile(self) -> Profile | None:
        index = self.profile_combo.current()
        if 0 <= index < len(self.profiles):
            return self.profiles[index]
        return None

    def add_profile(self) -> None:
        if self.mode.get() != "profiles":
            messagebox.showinfo("Perfiles", "Selecciona primero el modo de perfiles.", parent=self.root)
            return
        self._profile_dialog()

    def _profile_dialog(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Agregar perfil ARCA")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        frame = ttk.Frame(dialog, padding=16)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Guardar un perfil en Windows Credential Manager", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )
        ttk.Label(
            frame,
            text=(
                "La aplicación recibirá la clave durante el alta y Windows la guardará cifrada "
                "para tu usuario. No se enviará a otro servicio. Podrás borrar el perfil desde esta ventana."
            ),
            wraplength=430,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 12))

        label_var, cuit_var, password_var = tk.StringVar(), tk.StringVar(), tk.StringVar()
        ttk.Label(frame, text="Nombre del perfil:").grid(row=2, column=0, sticky="w", pady=4)
        label_entry = ttk.Entry(frame, textvariable=label_var, width=36)
        label_entry.grid(row=2, column=1, sticky="ew", pady=4)
        ttk.Label(frame, text="CUIT:").grid(row=3, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=cuit_var, width=36).grid(row=3, column=1, sticky="ew", pady=4)
        ttk.Label(frame, text="Clave fiscal:").grid(row=4, column=0, sticky="w", pady=4)
        password_entry = ttk.Entry(frame, textvariable=password_var, show="●", width=36)
        password_entry.grid(row=4, column=1, sticky="ew", pady=4)

        consent_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frame,
            text="Entiendo que el perfil guardará la clave localmente en Windows.",
            variable=consent_var,
        ).grid(row=5, column=0, columnspan=2, sticky="w", pady=(10, 4))
        buttons = ttk.Frame(frame)
        buttons.grid(row=6, column=0, columnspan=2, sticky="e", pady=(12, 0))

        def cancel() -> None:
            password_var.set("")
            dialog.destroy()

        def save() -> None:
            if not consent_var.get():
                messagebox.showwarning("Falta confirmar", "Confirma que comprendes dónde se guardará el perfil.", parent=dialog)
                return
            password = password_var.get()
            password_var.set("")
            try:
                profile = save_profile(label_var.get(), cuit_var.get(), password)
            except CredentialStoreError as exc:
                password = ""
                messagebox.showerror("No se guardó el perfil", str(exc), parent=dialog)
                return
            finally:
                password = ""
            label_var.set("")
            cuit_var.set("")
            refreshed = self.refresh_profiles()
            profile_index = next(
                (i for i, saved in enumerate(self.profiles) if saved.profile_id == profile.profile_id),
                None,
            )
            if profile_index is not None:
                self.profile_combo.current(profile_index)
            if refreshed and profile_index is not None:
                self.status.set("El perfil quedó guardado en el almacén local de Windows.")
            else:
                self.status.set("El perfil se guardó, pero no se pudo actualizar la lista. Vuelve a cargarla antes de usarlo.")
            dialog.destroy()

        ttk.Button(buttons, text="Cancelar", command=cancel).pack(side="right", padx=(6, 0))
        ttk.Button(buttons, text="Guardar perfil", command=save).pack(side="right")
        dialog.protocol("WM_DELETE_WINDOW", cancel)
        label_entry.focus_set()
        dialog.bind("<Return>", lambda _event: save())
        dialog.bind("<Escape>", lambda _event: cancel())

    def remove_profile(self) -> None:
        profile = self._selected_profile()
        if profile is None:
            messagebox.showinfo("Eliminar perfil", "Selecciona un perfil guardado.", parent=self.root)
            return
        if not messagebox.askyesno(
            "Eliminar perfil",
            f"¿Eliminar el perfil «{profile.label}» y su clave guardada en Windows? Esto no cambia la clave de ARCA.",
            parent=self.root,
        ):
            return
        try:
            delete_profile(profile)
        except CredentialStoreError as exc:
            messagebox.showerror("No se pudo eliminar", str(exc), parent=self.root)
            self.refresh_profiles()
            return
        self.refresh_profiles()
        self.status.set("El perfil y su clave guardada se eliminaron de Windows.")

    def start_workflow(self) -> None:
        if self.worker is not None and self.worker.is_alive():
            return
        profile = None
        if self.mode.get() == "profiles":
            profile = self._selected_profile()
            if profile is None:
                messagebox.showwarning("Selecciona un perfil", "Agrega o selecciona un perfil guardado.", parent=self.root)
                return
            if not messagebox.askokcancel(
                "Usar perfil guardado",
                f"Se leerá la clave del perfil «{profile.label}» solo después de que avances desde la etapa de CUIT a la pantalla de clave HTTPS oficial de ARCA. ¿Continuar?",
                parent=self.root,
            ):
                return

        self.cuit_continue_event = threading.Event()
        self.services_continue_event = threading.Event()
        self.finish_event = threading.Event()
        self.ready_for_continue = False
        self.action_stage = None
        self.has_results = False
        self._set_results("")
        self.status.set("Abriendo el portal oficial de ARCA…")
        self.start_button.configure(state="disabled")
        self.continue_button.configure(state="disabled", text="Continuar en ARCA…")
        self.finish_button.configure(text="Cancelar consulta / cerrar navegador", state="disabled")
        mode = self.mode.get()
        self.worker = threading.Thread(
            target=run_workflow,
            args=(
                mode,
                profile,
                self.cuit_continue_event,
                self.services_continue_event,
                self.finish_event,
                self.messages,
            ),
            name="arca-browser-worker",
            daemon=True,
        )
        self.worker.start()

    def continue_workflow(self) -> None:
        if self.has_results:
            return
        if self.ready_for_continue:
            self.ready_for_continue = False
            self.continue_button.configure(state="disabled")
            if self.action_stage == "cuit":
                self.status.set("Esperando que el paso de clave de ARCA esté listo…")
                self.cuit_continue_event.set()
            else:
                self.status.set("Validando la página y leyendo los servicios visibles…")
                self.services_continue_event.set()

    def finish_workflow(self) -> None:
        if not self.has_results:
            self.finish_event.set()
            self.cuit_continue_event.set()
            self.services_continue_event.set()
            self.status.set("Cancelando y cerrando el navegador…")
            self.finish_button.configure(state="disabled")
            return
        self.finish_event.set()
        self.finish_button.configure(state="disabled")
        self.status.set("Cerrando sesión en ARCA…")

    def _bring_to_front(self) -> None:
        """Return attention to results once, without remaining above other apps."""
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.focus_force()
        self.root.after(500, lambda: self.root.attributes("-topmost", False))

    def _set_results(self, text: str) -> None:
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        if text:
            self.result_text.insert("1.0", text)
        self.result_text.configure(state="disabled")

    def poll_messages(self) -> None:
        try:
            while True:
                kind, payload = self.messages.get_nowait()
                if kind == "ready_cuit":
                    self.status.set(payload)
                    self.ready_for_continue = True
                    self.action_stage = "cuit"
                    self.continue_button.configure(text="Ya avancé a la pantalla de clave")
                    self.continue_button.configure(state="normal")
                    self.finish_button.configure(state="normal")
                elif kind == "waiting_services":
                    self.status.set(payload)
                    self.ready_for_continue = False
                    self.action_stage = "services"
                    self.continue_button.configure(text="Esperando ingreso en ARCA…", state="disabled")
                    self.finish_button.configure(state="normal")
                elif kind == "ready_services":
                    self.status.set(payload)
                    self.ready_for_continue = True
                    self.action_stage = "services"
                    self.continue_button.configure(text="Reintentar consulta")
                    self.continue_button.configure(state="normal")
                    self.finish_button.configure(state="normal")
                elif kind == "results":
                    result: WorkflowResult = payload
                    lines = [f"{result.account_hint} · {len(result.services)} servicio(s)", ""]
                    lines.extend(f"• {service}" for service in result.services)
                    self._set_results("\n".join(lines))
                    self.status.set(
                        "Títulos leídos de las tarjetas de Mis servicios. Puedes cerrar la sesión y el navegador desde Finalizar."
                    )
                    self.has_results = True
                    self.action_stage = "results"
                    self._bring_to_front()
                    self.finish_button.configure(state="normal")
                    self.finish_button.configure(text="Cerrar sesión y finalizar")
                elif kind == "logout_status":
                    self.status.set(payload)
                elif kind == "logout_error":
                    self.closing = False
                    self.status.set(payload)
                    self.finish_button.configure(text="Reintentar cierre de sesión", state="normal")
                    self._bring_to_front()
                elif kind == "error":
                    self.status.set(payload)
                    self._set_results("")
                    self.continue_button.configure(state="disabled")
                    self.finish_button.configure(state="normal")
                    self.finish_button.configure(text="Cerrar navegador / finalizar")
                    self.has_results = False
                elif kind == "finished":
                    self.worker = None
                    self.start_button.configure(state="normal")
                    self.continue_button.configure(state="disabled")
                    self.finish_button.configure(state="disabled")
                    self.ready_for_continue = False
                    self.action_stage = None
                    self.has_results = False
                    if self.closing:
                        self.root.destroy()
                        return
                    if self.status.get().startswith("Cerrando"):
                        self.status.set("Navegador cerrado. Puedes iniciar otra consulta.")
        except Empty:
            pass
        if self.closing and (self.worker is None or not self.worker.is_alive()):
            self.root.destroy()
            return
        self.root.after(150, self.poll_messages)

    def on_close(self) -> None:
        if self.worker is not None and self.worker.is_alive():
            if self.has_results:
                self.closing = True
                self.finish_workflow()
                return
            if not messagebox.askokcancel(
                "Cerrar aplicación",
                "La sesión puede seguir abierta en el navegador. Cierra sesión en ARCA antes de cerrar. ¿Continuar?",
                parent=self.root,
            ):
                return
            self.closing = True
            self.finish_event.set()
            self.cuit_continue_event.set()
            self.services_continue_event.set()
            self.status.set("Cerrando navegador y aplicación…")
            return
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    ArcaApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
