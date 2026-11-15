"""Visible, read-only ARCA browser workflow."""

from __future__ import annotations

from dataclasses import dataclass
from queue import Queue
import re
import threading
import time
from typing import Any
from urllib.parse import urlparse

from playwright.sync_api import Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from credential_store import CredentialStoreError, Profile, get_password


ARCA_START_URL = "https://www.arca.gob.ar/claveFiscal/"
LOGIN_HOST = "auth.afip.gob.ar"
LOGIN_TITLE = re.compile(r"Ingresar con Clave Fiscal", re.IGNORECASE)
SERVICE_LIST_TITLE = re.compile(
    r"^(?:todos los servicios|ver todos los servicios|servicios habilitados|servicios disponibles)$",
    re.IGNORECASE,
)
EXCLUDED_LINKS = {
    "inicio", "volver", "ayuda", "salir", "cerrar sesión", "cerrar sesion",
    "ver todos", "ver todos los servicios", "administrar", "buscar", "más",
    "mas", "anterior", "siguiente", "página siguiente", "pagina siguiente",
}


class WorkflowError(Exception):
    """A brief error safe to show in the local UI."""


@dataclass(frozen=True)
class WorkflowResult:
    services: list[str]
    account_hint: str


def _host_is_official(host: str) -> bool:
    host = host.rstrip(".").lower()
    return any(host == root or host.endswith("." + root) for root in ("arca.gob.ar", "afip.gob.ar"))


def _require_https_official(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme.lower() != "https" or not parsed.hostname or not _host_is_official(parsed.hostname):
        raise WorkflowError(
            "La página actual no pertenece a un dominio HTTPS reconocido de ARCA/AFIP. El RPA se detuvo."
        )
    return parsed.hostname.lower()


def _official_login_url(page: Page) -> str:
    page.goto(ARCA_START_URL, wait_until="domcontentloaded", timeout=30_000)
    _require_https_official(page.url)
    links = page.locator("a[href]").evaluate_all(
        "nodes => nodes.map(a => ({href: a.href, text: (a.innerText || '').trim()}))"
    )
    for link in links:
        parsed = urlparse(link.get("href", ""))
        text = link.get("text", "")
        if parsed.scheme == "https" and parsed.hostname == LOGIN_HOST and re.search(
            r"ingresar|portal|clave fiscal", text, re.IGNORECASE
        ):
            return link["href"]
    raise WorkflowError(
        "No se encontró el enlace de ingreso en la página oficial de ARCA. Verifica el portal e inténtalo más tarde."
    )


def _fill_cuit_form(page: Page, cuit: str) -> None:
    if _require_https_official(page.url) != LOGIN_HOST:
        raise WorkflowError("La dirección de autenticación no coincide con el host oficial esperado.")
    try:
        page.locator('input[id="F1:username"]').wait_for(state="visible", timeout=15_000)
        if _require_https_official(page.url) != LOGIN_HOST:
            raise WorkflowError("La dirección cambió durante la espera del campo CUIT. No se completó.")
        password_fields = page.locator("input[type='password']")
        if any(password_fields.nth(i).is_visible() for i in range(password_fields.count())):
            raise WorkflowError("ARCA mostró un formulario combinado o distinto. No se completó.")
        text_fields = page.locator(
            "input[type='number'], input[type='text'], input[type='tel'], input[inputmode='numeric']"
        )
        visible_text_fields = [
            text_fields.nth(index)
            for index in range(text_fields.count())
            if text_fields.nth(index).is_visible() and text_fields.nth(index).is_enabled()
        ]
        if len(visible_text_fields) != 1:
            raise WorkflowError(
                "El campo de CUIT de ARCA no se pudo identificar sin ambigüedad. No se completó."
            )
        user_field = visible_text_fields[0]
        identity = " ".join(
            filter(
                None,
                [
                    user_field.get_attribute("aria-label"),
                    user_field.get_attribute("placeholder"),
                    user_field.get_attribute("name"),
                    user_field.get_attribute("id"),
                ],
            )
        )
        body = page.locator("body").inner_text(timeout=5_000)
        if not re.search(r"CUIT\s*/?\s*CUIL", body, re.IGNORECASE) and not re.search(
            r"CUIT|CUIL", identity, re.IGNORECASE
        ):
            raise WorkflowError(
                "No se reconoció el campo CUIT/CUIL del formulario oficial. No se completó."
            )
        if user_field.get_attribute("id") != "F1:username":
            raise WorkflowError("El campo no coincide con el acceso oficial observado. No se completó.")
        handle = user_field.element_handle(timeout=5_000)
        if handle is None or _require_https_official(page.url) != LOGIN_HOST:
            raise WorkflowError("La pantalla cambió antes de completar la CUIT.")
        handle.fill(cuit, timeout=5_000)
    except PlaywrightTimeoutError as exc:
        raise WorkflowError(
            "El paso de CUIT del formulario oficial no respondió como se esperaba. No se completó."
        ) from exc


def _fill_password_form(page: Page, profile: Profile, *, submitted_cuit: str | None = None) -> None:
    def validate_current_password_screen(wait_for_field: bool = True):
        if _require_https_official(page.url) != LOGIN_HOST:
            raise WorkflowError("La pantalla de clave no está en el host oficial de autenticación.")
        fields = page.locator("input[type='password']")
        if wait_for_field:
            fields.first.wait_for(state="visible", timeout=15_000)
        if _require_https_official(page.url) != LOGIN_HOST:
            raise WorkflowError("ARCA cambió de host durante la validación. La clave no se recuperó.")
        visible = [
            fields.nth(i)
            for i in range(fields.count())
            if fields.nth(i).is_visible() and fields.nth(i).is_enabled()
        ]
        body = page.locator("body").inner_text(timeout=5_000)
        if len(visible) != 1 or not re.search(r"clave fiscal|contraseña", body, re.IGNORECASE):
            raise WorkflowError(
                "ARCA no mostró una pantalla de clave reconocible. No se recuperó ni completó la contraseña."
            )
        page_digits = re.sub(r"\D", "", body)
        identity_fields = page.locator("input:not([type='password'])")
        identity_matches = False
        for index in range(identity_fields.count()):
            field = identity_fields.nth(index)
            if not field.is_visible():
                continue
            value_digits = re.sub(r"\D", "", field.input_value())
            if value_digits == profile.cuit:
                identity_matches = True
                break
        # A controlled CUIT -> password transition on this same page is also
        # identity evidence; ARCA need not repeat the CUIT visibly.
        shown_cuits = re.findall(r"\b\d{2}-\d{8}-\d\b", body)
        if shown_cuits and any(re.sub(r"\D", "", value) != profile.cuit for value in shown_cuits):
            raise WorkflowError("La pantalla muestra una CUIT distinta. No se recuperó la clave.")
        if not identity_matches and profile.cuit not in page_digits and submitted_cuit != profile.cuit:
            raise WorkflowError(
                "No se pudo comprobar que la pantalla de clave corresponde a la CUIT del perfil. La clave no se recuperó."
            )
        if _require_https_official(page.url) != LOGIN_HOST:
            raise WorkflowError("ARCA cambió de host durante la validación. La clave no se recuperó.")
        return visible[0]

    try:
        password_field = validate_current_password_screen()
        password_handle = password_field.element_handle(timeout=5_000)
        if password_handle is None:
            raise WorkflowError("El campo de clave cambió antes de ser validado. No se completó.")
        # Revalidate after resolving a concrete node. A later navigation cannot retarget this handle.
        validate_current_password_screen(wait_for_field=False)
        if _require_https_official(page.url) != LOGIN_HOST:
            raise WorkflowError("La dirección cambió antes de recuperar la clave. No se completó.")
        try:
            password = get_password(profile)
        except CredentialStoreError as exc:
            raise WorkflowError(str(exc)) from exc
        # Recheck origin, field and displayed CUIT immediately before sending the secret to the page.
        validate_current_password_screen(wait_for_field=False)
        if _require_https_official(page.url) != LOGIN_HOST:
            raise WorkflowError("La dirección cambió antes de completar la clave. No se completó.")
        password_handle.fill(password, timeout=5_000)
        password = None
    except PlaywrightTimeoutError as exc:
        raise WorkflowError("El paso de clave del formulario oficial no respondió como se esperaba.") from exc
    finally:
        password = None


def _fill_profile_login(page: Page, profile: Profile) -> None:
    """Keep both stages on the same page and advance only the validated CUIT form."""
    _fill_cuit_form(page, profile.cuit)
    field = page.locator('input[id="F1:username"]')
    if _require_https_official(page.url) != LOGIN_HOST or field.input_value() != profile.cuit:
        raise WorkflowError("La CUIT o la dirección cambió antes de avanzar. No se recuperó la clave.")
    next_button = page.locator('input[id="F1:btnSiguiente"][type="submit"]')
    next_button.click(timeout=5_000)
    # No manual handoff: wait for the password stage in the same browser page.
    _fill_password_form(page, profile, submitted_cuit=profile.cuit)
    if _require_https_official(page.url) != LOGIN_HOST:
        raise WorkflowError("La dirección cambió antes de enviar el ingreso.")
    # Semantic selector: do not guess an arbitrary submit control or retry passwords.
    submit = page.get_by_role("button", name=re.compile(r"^Ingresar$", re.I))
    submit.click(timeout=5_000)



def _latest_official_page(
    context: BrowserContext, expected_host: str | None = None, exclude_login: bool = False
) -> Page | None:
    for candidate in reversed(context.pages):
        if candidate.is_closed() or not candidate.url:
            continue
        parsed = urlparse(candidate.url)
        if parsed.scheme.lower() != "https" or not parsed.hostname or not _host_is_official(parsed.hostname):
            continue
        host = parsed.hostname.lower()
        if expected_host and host != expected_host:
            continue
        if exclude_login and host == LOGIN_HOST:
            continue
        return candidate
    return None


def _wait_for_action(
    context: BrowserContext,
    page: Page,
    action_event: threading.Event,
    finish_event: threading.Event,
    expected_host: str | None = None,
    exclude_login: bool = False,
    timeout: int = 900,
) -> Page | None:
    """Keep the synchronous Playwright dispatcher active while the person acts."""
    deadline = time.monotonic() + timeout
    while not action_event.is_set() and not finish_event.is_set():
        replacement = _latest_official_page(context, expected_host, exclude_login)
        if replacement is not None:
            page = replacement
        if page.is_closed():
            replacement = _latest_official_page(context, expected_host, exclude_login)
            if replacement is None:
                raise WorkflowError("El navegador se cerró antes de completar la consulta.")
            page = replacement
        if time.monotonic() >= deadline:
            return None
        page.wait_for_timeout(200)
    if not action_event.is_set() or finish_event.is_set():
        return None
    replacement = _latest_official_page(context, expected_host, exclude_login)
    return replacement or page


def _select_active_page(context: BrowserContext) -> Page:
    for page in reversed(context.pages):
        if page.is_closed() or not page.url:
            continue
        if urlparse(page.url).hostname == LOGIN_HOST:
            continue
        _require_https_official(page.url)
        return page
    raise WorkflowError(
        "No se encontró una página autenticada de ARCA. Completa el ingreso y abre la sección de servicios."
    )


PORTAL_HOST = "portalcf.cloud.afip.gob.ar"
SERVICES_PATH = "/portal/app/mis-servicios"


def _is_portal(page: Page, services_only=False) -> bool:
    url = urlparse(page.url)
    paths = (SERVICES_PATH,) if services_only else ("/portal/app", SERVICES_PATH)
    return (url.scheme == "https" and url.hostname == PORTAL_HOST
            and url.port in (None, 443) and not url.username
            and url.path.rstrip("/") in paths)


def _open_services(context, page, finish_event, timeout=900):
    """Observe manual login, then follow only the observed services route."""
    deadline = time.monotonic() + timeout
    while not finish_event.is_set():
        if time.monotonic() >= deadline:
            raise WorkflowError("Se agotó la espera de ingreso al portal.")
        candidates = [p for p in context.pages if not p.is_closed() and _is_portal(p)]
        for candidate in reversed(candidates):
            if _is_portal(candidate, services_only=True):
                return candidate
            links = candidate.get_by_role("link", name=re.compile(r"^Ver todos$", re.I))
            valid = []
            for i in range(links.count()):
                link = links.nth(i)
                if link.is_visible() and link.get_attribute("href") == SERVICES_PATH:
                    valid.append(link)
            if len(valid) > 1:
                raise WorkflowError("Hay varios accesos a servicios; no se eligió uno al azar.")
            if len(valid) == 1:
                valid[0].click(timeout=10_000)
                candidate.wait_for_url(
                    lambda url: urlparse(url).hostname == PORTAL_HOST
                    and urlparse(url).path.rstrip("/") == SERVICES_PATH,
                    timeout=15_000,
                )
                if not _is_portal(candidate, services_only=True):
                    raise WorkflowError("El acceso a servicios redirigió a una dirección inesperada.")
                return candidate
        live = [p for p in context.pages if not p.is_closed()]
        if not live:
            raise WorkflowError("El navegador se cerró antes de completar la consulta.")
        page = live[-1]
        page.wait_for_timeout(250)
    return None


def _extract_visible_services(page: Page) -> list[str]:
    if not _is_portal(page, services_only=True):
        raise WorkflowError("La página no es el listado del portal de Clave Fiscal reconocido.")
    main = page.locator("main, [role='main']")
    title = main.get_by_role("heading", name=re.compile(r"^Mis servicios$", re.I))
    title.wait_for(state="visible", timeout=15_000)
    if main.count() != 1 or title.count() != 1:
        raise WorkflowError("No se identificó una única sección Mis servicios.")
    section = title.locator("xpath=ancestor::section[1]")
    if section.count() != 1:
        raise WorkflowError("No se pudo delimitar la sección de servicios.")
    # This search belongs to the observed service list, not the global portal search.
    search = section.locator("#contBuscador input")
    for i in range(search.count()):
        field = search.nth(i)
        if field.is_visible() and field.input_value().strip():
            field.fill("")
    more = section.get_by_role("button", name=re.compile(r"siguiente|cargar más|ver más", re.I))
    more_links = section.get_by_role("link", name=re.compile(r"siguiente|cargar más|ver más", re.I))
    if any(loc.nth(i).is_visible() for loc in (more, more_links) for i in range(loc.count())):
        raise WorkflowError("La lista requiere más páginas; no se informará un resultado parcial.")
    # Observed cards are anchors with role=button and a heading, not ordinary links.
    cards = section.get_by_role("button").filter(has=page.get_by_role("heading"))
    cards.first.wait_for(state="visible", timeout=15_000)
    previous = None
    stable_since = time.monotonic()
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if not _is_portal(page, services_only=True):
            raise WorkflowError("La página cambió durante la lectura.")
        names = []
        for i in range(cards.count()):
            card = cards.nth(i)
            if not card.is_visible():
                continue
            heading = card.get_by_role("heading")
            if heading.count() != 1:
                raise WorkflowError("Una tarjeta tiene un título ambiguo.")
            name = re.sub(r"\s+", " ", heading.inner_text()).strip()
            if not name:
                raise WorkflowError("Una tarjeta no tiene nombre.")
            names.append(name)
        if names != previous:
            previous = names
            stable_since = time.monotonic()
        elif names and time.monotonic() - stable_since >= 1:
            return list(dict.fromkeys(names))
        page.wait_for_timeout(200)
    raise WorkflowError("El listado no terminó de estabilizarse. No se confirmó el resultado.")


def _wait_for_services(context, page, action_event, finish_event, messages) -> list[str] | None:
    """Keep recoverable validation failures in the visible session for a manual retry."""
    retry = False
    while not finish_event.is_set():
        if retry:
            active_page = _wait_for_action(context, page, action_event, finish_event)
            action_event.clear()
            if active_page is None:
                return None
            page = active_page
        try:
            active_page = _open_services(context, page, finish_event)
            if active_page is None:
                return None
            page = active_page
            return _extract_visible_services(active_page)
        except (WorkflowError, PlaywrightTimeoutError) as exc:
            if not any(not p.is_closed() for p in context.pages):
                raise WorkflowError("El navegador se cerró antes de completar la consulta.") from exc
            detail = str(exc) if isinstance(exc, WorkflowError) else "No se reconoció el listado completo dentro del tiempo esperado."
            messages.put(("ready_services", detail + " El navegador sigue abierto. Puedes reintentar o cerrar sesión y cancelar."))
            retry = True
    return None


def _logout_portal(page: Page, timeout: int = 15_000) -> None:
    """Use the observed menu; verify protected access redirects to the login form."""
    if not _is_portal(page):
        raise WorkflowError("No se encontró el portal esperado para cerrar sesión.")
    logout = page.locator('#contBtnContribuyente button[title="Salir"]')
    if not logout.is_visible():
        page.locator("header #iconoChicoContribuyenteAFIP").click(timeout=timeout)
    logout.wait_for(state="visible", timeout=timeout)
    if not _is_portal(page):
        raise WorkflowError("La dirección cambió antes de cerrar sesión.")
    logout.click(timeout=timeout)
    # Probe in a separate page to avoid cancelling the logout request by navigating
    # its own page. The ephemeral context shares the same session cookies.
    deadline = time.monotonic() + timeout / 1000
    while time.monotonic() < deadline:
        if page.is_closed():
            raise WorkflowError("Se cerró la pestaña sin poder verificar la salida.")
        url = urlparse(page.url)
        if url.scheme == "https" and url.hostname == LOGIN_HOST:
            if page.locator('input[id="F1:username"]').is_visible():
                return
        if not _is_portal(page):
            break
        page.wait_for_timeout(200)
    probe = page.context.new_page()
    try:
        probe.goto("https://" + PORTAL_HOST + SERVICES_PATH,
                   wait_until="domcontentloaded", timeout=timeout)
        probe.wait_for_url(lambda url: urlparse(url).scheme == "https"
                          and urlparse(url).hostname == LOGIN_HOST, timeout=timeout)
        probe.locator('input[id="F1:username"]').wait_for(state="visible", timeout=timeout)
    except PlaywrightTimeoutError as exc:
        raise WorkflowError("No se pudo confirmar el cierre de sesión. El navegador sigue abierto para revisar o reintentar.") from exc
    finally:
        probe.close()


def _finish_session(context, finish_event, messages):
    while True:
        live = [p for p in context.pages if not p.is_closed()]
        if not live:
            messages.put(("logout_status", "Navegador cerrado externamente; no se pudo verificar la salida de ARCA."))
            return
        if not finish_event.is_set():
            live[-1].wait_for_timeout(200)
            continue
        finish_event.clear()
        try:
            portals = [p for p in live if _is_portal(p)]
            if not portals and any(urlparse(p.url).hostname == LOGIN_HOST
                                   and p.locator('input[id="F1:username"]').is_visible() for p in live):
                messages.put(("logout_status", "ARCA solicita nuevamente el ingreso. Cerrando navegador…"))
                return
            if not portals:
                raise WorkflowError("No se encontró el portal para verificar el cierre de sesión.")
            _logout_portal(portals[-1])
        except (WorkflowError, PlaywrightTimeoutError):
            messages.put(("logout_status", "No se pudo verificar la salida en ARCA. Se cerrará el navegador local; no se confirma el cierre de sesión del servidor."))
            return
        messages.put(("logout_status", "Sesión cerrada: ARCA volvió a solicitar el ingreso. Cerrando navegador…"))
        return


def run_workflow(
    mode: str,
    profile: Profile | None,
    cuit_continue_event: threading.Event,
    services_continue_event: threading.Event,
    finish_event: threading.Event,
    messages: Queue[tuple[str, Any]],
) -> None:
    """Run Playwright on its own thread; UI communicates only via queue/events."""
    browser: Browser | None = None
    context: BrowserContext | None = None
    password: str | None = None
    try:
        if mode == "profiles" and profile is None:
            raise WorkflowError("Selecciona un perfil guardado antes de iniciar.")

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False)
            try:
                context = browser.new_context()
                context.set_default_timeout(10_000)
                page = context.new_page()
                if mode == "profiles":
                    session = context.new_cdp_session(page)
                    try:
                        window_id = session.send("Browser.getWindowForTarget")["windowId"]
                        session.send("Browser.setWindowBounds", {
                            "windowId": window_id, "bounds": {"windowState": "minimized"}
                        })
                    finally:
                        session.detach()

                page.set_default_navigation_timeout(30_000)

                login_url = _official_login_url(page)
                parsed_login = urlparse(login_url)
                if parsed_login.scheme != "https" or parsed_login.hostname != LOGIN_HOST:
                    raise WorkflowError("El enlace oficial de autenticación cambió. El RPA se detuvo.")
                page.goto(login_url, wait_until="domcontentloaded", timeout=30_000)
                if _require_https_official(page.url) != LOGIN_HOST:
                    raise WorkflowError("El portal redirigió a un host inesperado antes del acceso.")

                if mode == "profiles":
                    _fill_profile_login(page, profile)
                    messages.put((
                        "waiting_services",
                        "Ingreso enviado a ARCA. Si requiere verificación, abre el navegador minimizado desde la barra de tareas. El robot leerá Mis servicios automáticamente.",
                    ))
                else:
                    messages.put((
                        "waiting_services",
                        "Ingresa manualmente en el navegador oficial. Al terminar, el robot abrirá y leerá Mis servicios automáticamente.",
                    ))

                services = _wait_for_services(
                    context, page, services_continue_event, finish_event, messages
                )
                if services is None:
                    return
                hint = f"Perfil elegido: {profile.label} (cuenta autenticada no verificada)" if profile else "Cuenta manual (identidad no verificada)"
                messages.put(("results", WorkflowResult(services=services, account_hint=hint)))

                _finish_session(context, finish_event, messages)
            finally:
                password = None
                if context is not None:
                    try:
                        context.close()
                    except Exception:
                        pass
                if browser is not None:
                    try:
                        browser.close()
                    except Exception:
                        pass
    except WorkflowError as exc:
        messages.put(("error", str(exc)))
    except CredentialStoreError as exc:
        messages.put(("error", str(exc)))
    except PlaywrightTimeoutError:
        messages.put(("error", "ARCA tardó demasiado en responder. No se confirmó ningún resultado."))
    except Exception:
        messages.put(("error", "Ocurrió un error inesperado. No se guardó un diagnóstico con datos de la cuenta."))
    finally:
        password = None
        messages.put(("finished", None))
