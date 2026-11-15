import unittest
import threading
from playwright.sync_api import sync_playwright
from arca_browser import _open_services, _extract_visible_services, _logout_portal, WorkflowError

HOME = '<main><section><h3>Servicios | Más utilizados</h3><a href="/portal/app/mis-servicios">Ver todos</a></section></main>'
LIST = '''<main role="main"><section><div><h3>Mis servicios</h3>
<div role="alert"><a href="#">Administrador de Relaciones</a></div>
<div id="contBuscador"><input placeholder="Busca y/o agrega servicios"></div>
<div class="row panels-row">
<a role="button"><div><h3>Servicio ficticio A</h3><p>Descripción que no debe extraerse</p></div></a>
<a role="button"><div><h3>Servicio ficticio B</h3><p>Otra descripción</p></div></a>
</div><a href="/portal/app/">Volver</a></div></section></main>'''

class PortalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def setUp(self):
        self.context = self.browser.new_context()
        self.context.route('**/*', lambda route: route.fulfill(content_type='text/html', body=LIST if route.request.url.endswith('mis-servicios') else HOME))
        self.page = self.context.new_page()

    def tearDown(self):
        self.context.close()

    def test_auto_navigation_and_card_titles_without_logout(self):
        self.page.goto('https://portalcf.cloud.afip.gob.ar/portal/app/')
        result = _open_services(self.context, self.page, threading.Event(), timeout=2)
        self.assertEqual(_extract_visible_services(result), ['Servicio ficticio A', 'Servicio ficticio B'])

    def test_reject_public_or_unexpected_origin(self):
        self.page.goto('https://www.arca.gob.ar/portal/app/mis-servicios')
        with self.assertRaises(WorkflowError):
            _extract_visible_services(self.page)

    def test_clears_local_search(self):
        self.page.goto('https://portalcf.cloud.afip.gob.ar/portal/app/mis-servicios')
        self.page.locator('input').fill('texto')
        self.assertEqual(len(_extract_visible_services(self.page)), 2)
        self.assertEqual(self.page.locator('input').input_value(), '')

    def test_reject_pagination(self):
        self.page.goto('https://portalcf.cloud.afip.gob.ar/portal/app/mis-servicios')
        self.page.locator('section').evaluate("node => {const b=document.createElement('button'); b.textContent='Siguiente'; node.append(b);}")
        with self.assertRaises(WorkflowError):
            _extract_visible_services(self.page)

    def test_logout_opens_menu_and_returns_to_login(self):
        self.context.route('https://auth.afip.gob.ar/**', lambda route: route.fulfill(
            content_type='text/html', body='<h1>Ingresar con Clave Fiscal</h1>'))
        self.page.goto('https://portalcf.cloud.afip.gob.ar/portal/app/mis-servicios')
        self.page.set_content("""<header><div id="iconoChicoContribuyenteAFIP"
            onclick="document.getElementById('contBtnContribuyente').hidden=false">Usuario de prueba</div></header>
            <div id="contBtnContribuyente" hidden><button title="Salir"
            onclick="location.href='https://auth.afip.gob.ar/contribuyente_/login.xhtml'">Cerrar sesión</button></div>""")
        _logout_portal(self.page, timeout=1000)
        self.assertIn('auth.afip.gob.ar', self.page.url)

    def test_logout_does_not_claim_success_when_session_remains(self):
        self.page.goto('https://portalcf.cloud.afip.gob.ar/portal/app/mis-servicios')
        self.page.set_content('<div id="contBtnContribuyente"><button title="Salir">Cerrar sesión</button></div>')
        with self.assertRaises(WorkflowError):
            _logout_portal(self.page, timeout=300)
        self.assertFalse(self.page.is_closed())
        self.assertEqual(len(self.context.pages), 1)

if __name__ == '__main__':
    unittest.main()
