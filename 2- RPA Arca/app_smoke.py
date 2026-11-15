import tkinter as tk
from unittest.mock import patch
from main import ArcaApp
from arca_browser import WorkflowResult
import credential_store as store
from uuid import uuid4


def run():
    root=tk.Tk(); root.withdraw()
    failures=[]
    root.report_callback_exception=lambda typ,value,tb: failures.append(typ.__name__)
    prefix='PruebaTecnicaMHLM/Smoke/'+uuid4().hex+'/'
    with patch.object(store,'PROFILE_PREFIX',prefix+'Profile/'), patch.object(store,'SECRET_PREFIX',prefix+'Secret/'):
        profile=None
        try:
            app=ArcaApp(root)
            profile=store.save_profile('Prueba ficticia','00000000000','no-es-una-clave-real')
            if not store.list_profiles(): return 21
            from launcher import configure_browser_path
            from playwright.sync_api import sync_playwright
            from arca_browser import _extract_visible_services
            configure_browser_path()
            with sync_playwright() as pw:
                browser=pw.chromium.launch(headless=True,channel="chromium")
                try:
                    page=browser.new_page()
                    page.route('**/*',lambda route: route.fulfill(content_type='text/html',body='<main><section><h3>Mis servicios</h3><a role="button"><h3>Servicio ficticio</h3></a></section></main>'))
                    page.goto('https://portalcf.cloud.afip.gob.ar/portal/app/mis-servicios')
                    services=_extract_visible_services(page)
                finally:
                    browser.close()
            app.messages.put(('results',WorkflowResult(services,'Prueba')))
            app.poll_messages()
            if 'Servicio ficticio' not in app.result_text.get('1.0','end'): return 22
            if failures: return 23
        except ModuleNotFoundError:
            return 24
        except Exception:
            return 25
        finally:
            if profile: store.delete_profile(profile)
            root.destroy()
    return 0
