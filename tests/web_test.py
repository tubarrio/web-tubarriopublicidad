#!/usr/bin/env python3
"""Pruebas de la web principal (sin internet).

Uso:   python3 tests/web_test.py [carpeta_de_capturas]
Necesita: pip install playwright pillow  y un Chromium (ruta en CHROMIUM abajo o variable CHROMIUM).

Qué hace: sirve public/ en local con las mismas cabeceras (CSP) que tendrá en producción, y
simula con Playwright las dos apps (wildposting y carteleria): fotos.json de mentira con CORS y
fotos de prueba generadas. Comprueba el HTML, la CSP, el carrusel, los fallos del JSON, el móvil
(390 px) y el escritorio (1280 px), y deja capturas en la carpeta indicada.
"""
import io, json, os, re, sys, threading, time, functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from playwright.sync_api import sync_playwright
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC = os.path.join(RAIZ, 'public')
CAPT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'tests', 'capturas')
CHROMIUM = os.environ.get('CHROMIUM', '/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
WILD, CART = 'https://wildposting.tubarriopublicidad.es', 'https://carteleria.tubarriopublicidad.es'
CSP = ("default-src 'self'; img-src 'self' data: %s %s; connect-src %s %s; frame-ancestors 'none'; base-uri 'self'"
       % (WILD, CART, WILD, CART))
PUERTO = 8765
BASE = 'http://127.0.0.1:%d' % PUERTO
os.makedirs(CAPT, exist_ok=True)

fallos = []
def ok(cond, msg):
    print(('  ok  ' if cond else '  FALLA ') + msg)
    if not cond: fallos.append(msg)

PREFIJO = '/portada'   # la web se sirve desde /portada/ y, por una regla nginx, también desde /

class H(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # imita nginx (docs/nginx.conf.example): "/" -> /portada/index.html y /portada/x -> public/x
        ruta = path.split('?')[0].split('#')[0]
        if ruta == '/':
            ruta = '/index.html'
        elif ruta.startswith(PREFIJO + '/'):
            ruta = ruta[len(PREFIJO):]
        else:
            ruta = '/__no_existe__'
        return super().translate_path(ruta)
    def end_headers(self):
        self.send_header('Content-Security-Policy', CSP)
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()
    def log_message(self, *a): pass

def servir():
    s = ThreadingHTTPServer(('127.0.0.1', PUERTO), functools.partial(H, directory=PUBLIC))
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s

def jpg(color, texto):
    im = Image.new('RGB', (800, 600), color)
    from PIL import ImageDraw
    d = ImageDraw.Draw(im); d.rectangle([60, 60, 740, 540], outline='white', width=12)
    d.text((100, 100), texto, fill='white')
    b = io.BytesIO(); im.save(b, 'JPEG'); return b.getvalue()

CORS = {'Access-Control-Allow-Origin': '*'}
def rutas(page, modo, n=3, fotos_extra=None):
    """modo: ok | vacio | roto | caido | unarota"""
    def json_(host):
        def f(route):
            if modo == 'caido': return route.abort()
            if modo == 'roto': return route.fulfill(status=500, headers=CORS, body='no es json')
            if modo == 'vacio': return route.fulfill(status=200, headers=CORS, content_type='application/json', body='{"fotos":[]}')
            fotos = [{'url': host + '/demo/f/%d.jpg' % i, 'miniatura': host + '/demo/m/%d.jpg' % i, 'punto': 'Calle Mayor %d' % (i + 1),
                      'ciudad': 'Ciudad de prueba', 'fecha': '2026-10-%02d 10:30:00' % (i + 10), 'comentario': 'Foto de prueba <b>%d</b>' % i}
                     for i in range(n)]
            if fotos_extra is not None: fotos = [dict(x, url=host + '/demo/f/%d.jpg' % i, miniatura=host + '/demo/m/%d.jpg' % i) for i, x in enumerate(fotos_extra)]
            if modo == 'unarota': fotos[1]['miniatura'] = host + '/demo/m/rota.jpg'
            route.fulfill(status=200, headers=CORS, content_type='application/json', body=json.dumps({'fotos': fotos}))
        return f
    def foto(route):
        i = int(re.search(r'/(\d)\.jpg', route.request.url).group(1))
        body = jpg(['#2e7d32', '#1565c0', '#6a1b9a'][i % 3], 'Foto %d' % i)
        route.fulfill(status=200, headers=CORS, content_type='image/jpeg', body=body)
    for host in (WILD, CART):
        page.route(host + '/demo/fotos.json', json_(host))
        page.route(host + '/demo/m/*.jpg', foto)
        page.route(host + '/demo/f/*.jpg', foto)
        page.route(host + '/demo/m/rota.jpg', lambda r: r.fulfill(status=404, body='x'))
        page.route(host + '/demo', lambda r: r.fulfill(status=200, content_type='text/html', body='demo'))

INIT = """
window.__csp = []; window.__cls = 0;
document.addEventListener('securitypolicyviolation', e => window.__csp.push(e.violatedDirective + ' ' + e.blockedURI));
try { new PerformanceObserver(l => { for (const e of l.getEntries()) if (!e.hadRecentInput) window.__cls += e.value; })
      .observe({type: 'layout-shift', buffered: true}); } catch (e) {}
"""

def nueva(b, ancho, alto=900, **kw):
    ctx = b.new_context(viewport={'width': ancho, 'height': alto}, **kw)
    ctx.add_init_script(INIT)
    pg = ctx.new_page()
    errs, pe = [], []
    pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
    pg.on('pageerror', lambda e: pe.append(str(e)))
    return ctx, pg, errs, pe

def activa(pg, i):
    """índice de la foto activa del carrusel i"""
    return pg.evaluate("""i => { const c = document.querySelectorAll('.carrusel')[i];
        return [...c.querySelectorAll('.slide')].findIndex(s => s.classList.contains('activa')); }""", i)

# ------------------------------------------------------------------ estático
def estatico():
    print('HTML y ficheros')
    html = open(os.path.join(PUBLIC, 'index.html'), encoding='utf-8').read()
    legal = open(os.path.join(PUBLIC, 'aviso-legal.html'), encoding='utf-8').read()
    for nombre, t in (('index', html), ('aviso-legal', legal)):
        ok(not re.search(r'\sstyle\s*=', t, re.I), nombre + ': sin style=""')
        ok(not re.search(r'\son[a-z]+\s*=', t, re.I), nombre + ': sin onclick= y similares')
        ok(not re.search(r'<style', t, re.I), nombre + ': sin <style>')
        sc = re.findall(r'<script\b([^>]*)>', t, re.I)
        malos = [a for a in sc if 'src=' not in a and 'application/ld+json' not in a]
        ok(not malos, nombre + ': ningún <script> con código dentro (solo src o JSON-LD)')
        ok('javascript:' not in t.lower(), nombre + ': sin javascript:')
        ok('lang="es"' in t, nombre + ': lang="es"')
        for im in re.findall(r'<img\b[^>]*>', t):
            ok('width=' in im and 'height=' in im and 'alt=' in im, nombre + ': img con ancho, alto y alt -> ' + im[:60])
    ok('<link rel="canonical" href="https://tubarriopublicidad.es/">' in html, 'canonical de la portada')
    rutas_loc = re.findall(r'(?:src|href)="(/[^"]*)"', html + legal)
    ok(all(r == '/' or r.startswith('/portada/') for r in rutas_loc), 'todas las rutas locales llevan /portada/ (valen desde / y desde /portada/)')
    ok('/portada/assets/img/og.png' in html, 'imagen para compartir con ruta /portada/')
    for k in ('og:title', 'og:description', 'og:image', 'og:url', 'twitter:card', 'name="description"'):
        ok(k in html, 'meta ' + k)
    ld = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    j = json.loads(ld.group(1))
    ok(j['@type'] == 'LocalBusiness', 'JSON-LD LocalBusiness')
    ok('address' not in j and 'telephone' not in j, 'JSON-LD sin dirección ni teléfono')
    ok('Quiero%20presupuesto' in html and 'mailto:tubarriopublicidad@gmail.com' in html, 'mailto con asunto en el HTML')
    ok('[RAZÓN SOCIAL]' in legal and '[NIF]' in legal and '[DOMICILIO]' in legal, 'aviso legal con marcadores')
    ok(os.path.getsize(os.path.join(PUBLIC, 'assets', 'web.js')) < 10240, 'web.js pesa menos de 10 KB (%d bytes)' % os.path.getsize(os.path.join(PUBLIC, 'assets', 'web.js')))
    im = Image.open(os.path.join(PUBLIC, 'assets', 'img', 'og.png'))
    ok(im.size == (1200, 630), 'og.png 1200x630')
    ok(open(os.path.join(PUBLIC, 'robots.txt')).read().find('Sitemap: https://tubarriopublicidad.es/sitemap.xml') >= 0, 'robots.txt con sitemap')
    ok('<loc>https://tubarriopublicidad.es/</loc>' in open(os.path.join(PUBLIC, 'sitemap.xml')).read(), 'sitemap.xml con la portada')
    js = open(os.path.join(PUBLIC, 'assets', 'web.js'), encoding='utf-8').read()
    css = open(os.path.join(PUBLIC, 'assets', 'web.css'), encoding='utf-8').read()
    ok(not re.search(r'https?://(?!(wildposting|carteleria)\.tubarriopublicidad\.es|wa\.me)', js + css), 'sin dominios externos en JS/CSS')
    ng = open(os.path.join(RAIZ, 'docs', 'nginx.conf.example'), encoding='utf-8').read()
    ok(CSP in ng, 'la CSP de docs/nginx.conf.example es la misma que usan estas pruebas')

# ------------------------------------------------------------------ navegador
def pagina_ok(b):
    print('Escritorio 1280 px, fotos reales')
    ctx, pg, errs, pe = nueva(b, 1280)
    rutas(pg, 'ok')
    pg.goto(BASE + '/'); pg.wait_for_load_state('networkidle')
    pg.wait_for_selector('.carrusel.con-fotos .slide.real')
    ok(pg.locator('.carrusel').count() == 2, 'dos carruseles')
    ok(pg.locator('.carrusel.con-fotos').count() == 2, 'los dos cargan las fotos reales del JSON')
    ok(pg.locator('.carrusel .slide.real').count() == 6, '3 fotos reales por carrusel (6)')
    alt = pg.locator('.carrusel .slide.real img').first.get_attribute('alt')
    ok('Calle Mayor' in alt and '<b>' in alt, 'alt útil con punto y comentario (texto literal, sin HTML): ' + alt)
    ok(pg.locator('.carrusel .slide.real b').count() == 0, 'el comentario no se interpreta como HTML')
    ok(pg.locator('.pie-foto').first.inner_text().startswith('Calle Mayor 1'), 'pie de foto: ' + pg.locator('.pie-foto').first.inner_text())
    ok('octubre' not in pg.locator('.pie-foto').first.inner_text() and '2026' not in pg.locator('.pie-foto').first.inner_text(), 'sin fecha en el pie')
    ok(pg.locator('.carrusel img[src^="https://wildposting"]').count() == 3 and pg.locator('.carrusel img[src^="https://carteleria"]').count() == 3, 'cada carrusel usa las fotos de su app')
    for k, (nom, host) in enumerate((('Wildposting', 'wildposting'), ('Cartelería', 'carteleria'))):
        t = pg.locator('.tarjeta').nth(k)
        for sel in ('.enlace-nombre', '.boton-mini'):
            a = t.locator(sel)
            ok(a.get_attribute('href') == 'https://%s.tubarriopublicidad.es/demo' % host and a.get_attribute('target') == '_blank' and 'noopener' in a.get_attribute('rel'), '%s %s: enlace a su demo en pestaña nueva' % (nom, sel))
            ok(a.bounding_box()['height'] >= 43.5, '%s %s: objetivo táctil >= 44 px' % (nom, sel))
        ok(t.locator('.enlace-nombre').get_attribute('aria-label').startswith('Ver el ejemplo en vivo de ' + nom), 'aria-label del nombre')
        ok(t.locator('.boton.boton-sec').count() == 1 and 'Sin registro' in t.locator('.nota').inner_text(), 'se mantienen el botón grande y la frase')
    n0, m0 = pg.locator('.tarjeta').nth(0).locator('.enlace-nombre').bounding_box(), pg.locator('.tarjeta').nth(0).locator('.boton-mini').bounding_box()
    ok(abs((n0['y'] + n0['height'] / 2) - (m0['y'] + m0['height'] / 2)) < 4, 'en PC el botón pequeño va en la misma fila que el nombre')
    pg.locator('.tarjeta').nth(0).locator('.enlace-nombre').focus()
    ok(pg.evaluate("getComputedStyle(document.activeElement).outlineStyle") != 'none', 'foco visible en el nombre')
    pg.screenshot(path=CAPT + '/escritorio-1280-completa.png', full_page=True)
    # botones
    ok(activa(pg, 0) == 0, 'empieza en la primera')
    pg.locator('.carrusel').nth(0).locator('.sig').click(); ok(activa(pg, 0) == 1, 'siguiente')
    pg.locator('.carrusel').nth(0).locator('.ant').click(); ok(activa(pg, 0) == 0, 'anterior')
    pg.locator('.carrusel').nth(0).locator('.ant').click(); ok(activa(pg, 0) == 2, 'anterior desde la primera da la vuelta')
    pg.locator('.carrusel').nth(0).locator('.punto').nth(1).click(); ok(activa(pg, 0) == 1, 'punto 2')
    ok(pg.locator('.carrusel').nth(0).locator('.punto[aria-current]').count() == 1, 'un solo punto marcado (aria-current)')
    ok(activa(pg, 1) == 0, 'el otro carrusel no se mueve')
    # teclado
    pg.locator('.carrusel').nth(1).focus()
    pg.keyboard.press('ArrowRight'); ok(activa(pg, 1) == 1, 'flecha derecha del teclado')
    pg.keyboard.press('ArrowLeft'); ok(activa(pg, 1) == 0, 'flecha izquierda del teclado')
    pg.keyboard.press('Tab'); ok(pg.evaluate("document.activeElement.className") in ('flecha ant', 'ant flecha', 'flecha ant '), 'Tab llega a los botones del carrusel')
    # nombres accesibles
    ok(pg.locator('.carrusel').nth(0).locator('button[aria-label]').count() >= 6, 'botones con aria-label')
    # botones de enlace
    h = pg.eval_on_selector_all('a.boton-sec', "els => els.map(e => [e.href, e.target, e.rel])")
    ok(h == [[WILD + '/demo', '_blank', 'noopener'], [CART + '/demo', '_blank', 'noopener']], 'Ver ejemplo en vivo: URLs, pestaña nueva y noopener ' + str(h))
    ok(pg.locator('text=Sin registro: es el seguimiento real de una campaña de ejemplo').count() == 2, 'frase «Sin registro…» bajo cada ejemplo')
    ok(pg.get_attribute('#pide-presupuesto', 'href') == 'mailto:tubarriopublicidad@gmail.com?subject=Quiero%20presupuesto', 'mailto del botón Pide presupuesto')
    ok(not pg.is_visible('#bloque-telefono'), 'teléfono/WhatsApp oculto mientras no se rellene')
    ok(pg.get_attribute('a.boton', 'href') == '#servicios', '«Conoce nuestros servicios» baja a #servicios')
    pg.click('a.boton >> nth=0'); time.sleep(.6)
    ok(pg.evaluate("document.getElementById('servicios').getBoundingClientRect().top") < 200, 'el botón de la cabecera baja a la sección')
    # todos los ficheros enlazados existen (desde / y desde /portada/)
    for desde in ('/', '/portada/'):
        pg.goto(BASE + desde); pg.wait_for_load_state('load')
        urls = pg.evaluate("""() => [...document.querySelectorAll('link[href],img[src],script[src],a[href]')]
            .map(e => e.getAttribute('href') || e.getAttribute('src')).filter(u => u && u.startsWith('/'))""")
        malos = [u for u in set(urls) if pg.request.get(BASE + u).status != 200]
        ok(not malos, 'ficheros locales enlazados desde %s (%d) existen %s' % (desde, len(set(urls)), malos))
    pg.goto(BASE + '/'); pg.wait_for_load_state('networkidle'); pg.wait_for_selector('.carrusel.con-fotos .slide.real')
    # ausencia de errores
    ok(pg.evaluate('window.__csp') == [], 'sin violaciones de CSP: %s' % pg.evaluate('window.__csp'))
    ok(not errs and not pe, 'sin errores de consola ni de JS: %s %s' % (errs, pe))
    ok(pg.evaluate('window.__cls') < 0.01, 'CLS %.4f' % pg.evaluate('window.__cls'))
    # avance automático (5 s) y pausa
    pg.reload(); pg.wait_for_selector('.carrusel.con-fotos .slide.real')
    a0 = activa(pg, 0); time.sleep(5.8)
    ok(activa(pg, 0) != a0, 'avance automático')
    pg.hover('.carrusel >> nth=0'); a1 = activa(pg, 0); time.sleep(5.8)
    ok(activa(pg, 0) == a1, 'se pausa con el ratón encima')
    pg.mouse.move(5, 5); time.sleep(5.8)
    ok(activa(pg, 0) != a1, 'al quitar el ratón sigue')
    pg.locator('.carrusel').nth(0).locator('.sig').focus(); a2 = activa(pg, 0); time.sleep(5.8)
    ok(activa(pg, 0) == a2, 'se pausa con el foco dentro')
    pg.evaluate("document.activeElement.blur()")
    pg.locator('.carrusel').nth(0).locator('.pp').click(); pg.mouse.move(5, 5); a3 = activa(pg, 0); time.sleep(5.8)
    ok(activa(pg, 0) == a3, 'el botón de pausa detiene el avance')
    ctx.close()

    print('Móvil 390 px')
    ctx, pg, errs, pe = nueva(b, 390, 844, has_touch=True, is_mobile=True, device_scale_factor=2)
    rutas(pg, 'ok')
    pg.goto(BASE + '/'); pg.wait_for_load_state('networkidle'); pg.wait_for_selector('.carrusel.con-fotos .slide.real')
    pg.screenshot(path=CAPT + '/movil-390-portada.png')
    pg.screenshot(path=CAPT + '/movil-390-completa.png', full_page=True)
    pg.locator('#servicios').scroll_into_view_if_needed()
    pg.evaluate("document.getElementById('t-wild').scrollIntoView()")
    pg.screenshot(path=CAPT + '/movil-390-tarjeta.png')
    ok(pg.evaluate("matchMedia('(min-width: 760px)').matches") is False, 'diseño móvil')
    t = pg.eval_on_selector_all('.tarjeta', "els => els.map(e => e.getBoundingClientRect().top)")
    ok(t[1] > t[0] + 300, 'tarjetas apiladas en móvil')
    # deslizar con el dedo (CDP)
    cdp = ctx.new_cdp_session(pg)
    box = pg.locator('.carrusel').nth(0).bounding_box()
    pg.evaluate("window.scrollTo(0, document.querySelector('.carrusel').getBoundingClientRect().top + scrollY - 100)")
    box = pg.locator('.carrusel').nth(0).bounding_box()
    y = box['y'] + box['height'] / 2
    def swipe(x1, x2):
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x1, 'y': y}]})
        for k in range(1, 6):
            cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x1 + (x2 - x1) * k / 5, 'y': y}]})
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
        time.sleep(.3)
    a = activa(pg, 0); swipe(300, 80); ok(activa(pg, 0) == (a + 1) % 3, 'deslizar a la izquierda = siguiente')
    swipe(80, 300); ok(activa(pg, 0) == a, 'deslizar a la derecha = anterior')
    ok(pg.evaluate('window.__csp') == [], 'móvil: sin violaciones de CSP')
    ok(not errs and not pe, 'móvil: sin errores de consola: %s %s' % (errs, pe))
    ctx.close()

def pies(b):
    print('Pie de foto: con pie, compuesto en cliente, JSON antiguo')
    casos = [
        {'pie': 'Cubo elecciones · Granada · Albolote · Zaidín', 'punto': 'X', 'ciudad': 'Y', 'fecha': '2026-10-10 10:00:00', 'comentario': 'c <i>1</i>'},
        {'punto': 'Discos Bora Bora tienda de discos', 'categoria': 'Tienda de discos', 'ciudad': 'Granada', 'pueblo': 'Granada', 'barrio': 'Centro', 'fecha': '2026-10-11 10:00:00'},
        {'punto': 'Bar Paco', 'categoria': 'Bar', 'ciudad': 'Granada', 'pueblo': '', 'barrio': None},
        {'punto': 'Calle Mayor 4', 'ciudad': 'Ciudad de prueba', 'fecha': '2026-10-12 10:00:00', 'comentario': 'Foto <b>3</b>'},
    ]
    ctx, pg, errs, pe = nueva(b, 1280)
    rutas(pg, 'ok', n=4, fotos_extra=casos)
    pg.goto(BASE + '/'); pg.wait_for_load_state('networkidle'); pg.wait_for_selector('.carrusel.con-fotos .slide.real')
    p = pg.locator('.carrusel').nth(0).locator('.pie-foto').all_text_contents()
    ok(p[0] == 'Cubo elecciones · Granada · Albolote · Zaidín', 'usa el pie de la app tal cual: ' + p[0])
    ok(pg.locator('.carrusel').nth(0).locator('.slide.real img').nth(0).get_attribute('alt').startswith('Wildposting: Cubo elecciones · Granada') or 'Cubo elecciones · Granada · Albolote' in pg.locator('.carrusel').nth(0).locator('.slide.real img').nth(0).get_attribute('alt'), 'el alt usa el pie')
    ok(p[1] == 'Discos Bora Bora tienda de discos · Granada · Centro', 'categoría contenida en el nombre (sin tildes/mayúsculas) y duplicados omitidos: ' + p[1])
    ok(p[2] == 'Bar Paco · Granada', 'sin categoría repetida ni pueblo/barrio vacíos: ' + p[2])
    ok(p[3] == 'Calle Mayor 4 · Ciudad de prueba', 'JSON antiguo (sin pie ni categoría): ' + p[3])
    ok(all('2026' not in t and 'octubre' not in t for t in p), 'ningún pie lleva fecha')
    ok(pg.locator('.carrusel .slide.real b, .carrusel .slide.real i').count() == 0, 'todo es texto, nunca HTML')
    pg.screenshot(path=CAPT + '/escritorio-1280-pies.png')
    ctx.close()
    ctx, pg, errs, pe = nueva(b, 390, 844)
    rutas(pg, 'ok', n=4, fotos_extra=casos)
    pg.goto(BASE + '/'); pg.wait_for_load_state('networkidle'); pg.wait_for_selector('.carrusel.con-fotos .slide.real')
    pg.locator('.carrusel').nth(0).scroll_into_view_if_needed()
    pg.screenshot(path=CAPT + '/movil-390-pies.png')
    ok(pg.evaluate('document.documentElement.scrollWidth <= document.documentElement.clientWidth'), 'sin scroll horizontal a 390 px con pies largos')
    pg.locator('.titulo-fila').first.scroll_into_view_if_needed(); pg.screenshot(path=CAPT + '/movil-390-titulo-tarjeta.png')
    for sel in ('.enlace-nombre', '.boton-mini'):
        bb = pg.locator('.tarjeta').nth(0).locator(sel).bounding_box()
        ok(bb['height'] >= 43.5 and bb['x'] + bb['width'] <= 390, 'móvil: %s >= 44 px y dentro de pantalla' % sel)
    ok(pg.evaluate('window.__csp') == [] and not pe, 'sin CSP ni errores de JS')
    ctx.close()

def escritorio_y_anchos(b):
    print('Sin desplazamiento horizontal ni saltos')
    for w in (360, 390, 768, 1024, 1280, 1440):
        ctx, pg, errs, pe = nueva(b, w, 900)
        rutas(pg, 'ok')
        for ruta in ('/', '/portada/', '/portada/aviso-legal.html'):
            pg.goto(BASE + ruta); pg.wait_for_load_state('networkidle'); time.sleep(.3)
            sw, cw = pg.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
            ok(sw <= cw, 'sin scroll horizontal a %d px en %s (%d/%d)' % (w, ruta, sw, cw))
        pg.goto(BASE + '/'); pg.wait_for_load_state('networkidle'); time.sleep(.5)
        ok(pg.evaluate('window.__cls') < 0.01, 'CLS a %d px: %.4f' % (w, pg.evaluate('window.__cls')))
        if w == 1280:
            pg.screenshot(path=CAPT + '/escritorio-1280-portada.png')
            ok(pg.evaluate("""(() => { const t = [...document.querySelectorAll('.tarjeta')].map(e => e.getBoundingClientRect());
                return Math.abs(t[0].top - t[1].top) < 2 && t[1].left > t[0].right - 1; })()"""), 'dos tarjetas lado a lado en PC')
            pg.evaluate("document.getElementById('como').scrollIntoView()")
            pg.screenshot(path=CAPT + '/escritorio-1280-como-contacto.png')
        ctx.close()

def fallbacks(b):
    for modo in ('caido', 'roto', 'vacio'):
        print('Relleno cuando el JSON falla: ' + modo)
        ctx, pg, errs, pe = nueva(b, 1280)
        rutas(pg, modo)
        pg.goto(BASE + '/'); pg.wait_for_load_state('networkidle'); time.sleep(.5)
        ok(pg.locator('.carrusel.con-fotos').count() == 0, 'no se marca con-fotos')
        ok(pg.locator('.carrusel .slide').count() == 6, 'siguen las 6 imágenes de relleno propias')
        ok(pg.locator('.carrusel img[src$=".svg"]').count() == 6, 'son SVG propios')
        ok(activa(pg, 0) == 0, 'primera visible')
        ok(pg.evaluate('window.__csp') == [] and not pe, 'sin CSP ni errores de JS (%s)' % pe)
        if modo == 'caido':
            pg.screenshot(path=CAPT + '/escritorio-1280-relleno.png')
            ok(all(e.startswith('Failed to load resource') for e in errs), 'solo el aviso propio del navegador por la red caída: %s' % errs)
        ctx.close()
    print('Una sola foto y una foto que no carga')
    ctx, pg, errs, pe = nueva(b, 390, 844)
    rutas(pg, 'ok', n=1)
    pg.goto(BASE + '/'); pg.wait_for_load_state('networkidle')
    ok(pg.locator('.carrusel').nth(0).locator('.sig').is_hidden(), 'con una sola foto no hay flechas')
    ctx.close()
    ctx, pg, errs, pe = nueva(b, 390, 844)
    rutas(pg, 'unarota')
    pg.goto(BASE + '/'); pg.wait_for_load_state('networkidle'); time.sleep(.5)
    ok(pg.locator('.carrusel').nth(0).locator('.slide').count() == 2, 'una foto que no carga se descarta y quedan las otras 2')
    ok(pg.locator('.carrusel').nth(0).locator('.punto').count() == 2, 'y los puntos se actualizan')
    ok(pg.evaluate('window.__csp') == [] and not pe, 'sin CSP ni errores de JS')
    ctx.close()

def sin_js_y_movimiento(b):
    print('Sin JavaScript')
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, java_script_enabled=False)
    pg = ctx.new_page(); rutas(pg, 'ok')
    pg.goto(BASE + '/'); pg.wait_for_load_state('load')
    vis = pg.eval_on_selector_all('.carrusel', "cs => cs.map(c => [...c.querySelectorAll('.slide')].filter(s => getComputedStyle(s).display !== 'none').length)")
    ok(vis == [1, 1], 'sin JS cada carrusel enseña solo su primera imagen ' + str(vis))
    ok(pg.locator('.carrusel img').first.evaluate('i => i.complete && i.naturalWidth > 0'), 'la primera imagen se ve')
    ok(pg.locator('.carrusel button').count() == 0, 'sin JS no hay botones que no funcionen')
    ok(pg.get_attribute('#pide-presupuesto', 'href').startswith('mailto:'), 'el mailto funciona sin JS')
    ok(pg.get_attribute('a.boton-sec >> nth=0', 'href').endswith('/demo'), 'los enlaces funcionan sin JS')
    pg.screenshot(path=CAPT + '/movil-390-sin-js.png', full_page=True)
    ctx.close()
    print('Movimiento reducido')
    ctx, pg, errs, pe = nueva(b, 1280, reduced_motion='reduce')
    rutas(pg, 'ok')
    pg.goto(BASE + '/'); pg.wait_for_load_state('networkidle'); pg.wait_for_selector('.carrusel.con-fotos .slide.real')
    a = activa(pg, 0); time.sleep(6)
    ok(activa(pg, 0) == a, 'con prefers-reduced-motion no avanza solo')
    ok(pg.locator('.carrusel').nth(0).locator('.pp').is_hidden(), 'sin botón de pausa (no hay nada que pausar)')
    pg.locator('.carrusel').nth(0).locator('.sig').click(); ok(activa(pg, 0) == (a + 1) % 3, 'a mano sí funciona')
    ok(pg.evaluate("getComputedStyle(document.querySelector('.slide')).transitionDuration") == '0s', 'sin transición')
    ctx.close()

def telefono(b):
    print('Teléfono / WhatsApp con la constante rellena')
    ctx, pg, errs, pe = nueva(b, 390, 844)
    js = open(os.path.join(PUBLIC, 'assets', 'web.js'), encoding='utf-8').read().replace("var TELEFONO = '';", "var TELEFONO = '+34 600 123 456';")
    pg.route(BASE + '/portada/assets/web.js', lambda r: r.fulfill(status=200, content_type='application/javascript', body=js))
    rutas(pg, 'caido')
    pg.goto(BASE + '/'); pg.wait_for_load_state('networkidle')
    ok(pg.is_visible('#bloque-telefono'), 'se muestra el bloque')
    ok(pg.get_attribute('#enlace-telefono', 'href') == 'tel:+34600123456', 'tel: ' + pg.get_attribute('#enlace-telefono', 'href'))
    ok(pg.get_attribute('#enlace-whatsapp', 'href') == 'https://wa.me/34600123456', 'wa.me')
    pg.evaluate("document.getElementById('contacto').scrollIntoView()")
    pg.screenshot(path=CAPT + '/movil-390-contacto-con-telefono.png')
    ctx.close()

def main():
    estatico()
    srv = servir()
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROMIUM, args=['--no-sandbox', '--disable-gpu'])
        for f in (pagina_ok, pies, escritorio_y_anchos, fallbacks, sin_js_y_movimiento, telefono):
            f(b)
        b.close()
    srv.shutdown()
    print('\n%s' % ('TODO BIEN' if not fallos else 'FALLOS (%d):\n - ' % len(fallos) + '\n - '.join(fallos)))
    sys.exit(1 if fallos else 0)

if __name__ == '__main__':
    main()
