# Web principal de Tu Barrio Publicidad

Página estática de `tubarriopublicidad.es`: presenta Wildposting y Cartelería, con un carrusel de fotos reales de
cada una (las lee de sus «ejemplos en vivo») y un botón para pedir presupuesto.
**HTML + CSS + JavaScript normal, sin compilar**: no hay Node, ni frameworks, ni CDNs, ni fuentes remotas, ni cookies,
ni formularios, ni analítica. Cómo se publica: [`PUBLICAR.md`](PUBLICAR.md).

## Qué hay

| Ruta | Para qué |
|---|---|
| `public/index.html` | La portada (franja de acceso clientes, cabecera con las dos entradas a los mapas, servicios, cómo funciona, área de clientes `#clientes`, contacto, pie) y los datos para buscadores (JSON-LD) |
| `public/aviso-legal.html` | Aviso legal con `[RAZÓN SOCIAL]`, `[NIF]`, `[DOMICILIO]` por rellenar |
| `public/assets/web.css` | Todo el diseño. Colores en `:root` (sacados del logo) |
| `public/assets/web.js` | Carrusel, contacto y nota de alta. Unos 10 KB (3,5 KB comprimido; las pruebas exigen menos de 10 KB). **Configuración al principio del fichero** |
| `public/assets/img/` | Logo, imagen para compartir (`og.png`, 1200×630), iconos y las 6 ilustraciones de relleno (`relleno-*.svg`) |
| `public/robots.txt`, `public/sitemap.xml`, `public/favicon.ico` | Buscadores y pestaña |
| `docs/nginx.conf.example` | Reglas nginx (cabeceras de seguridad, caché y «/» → portada), para CloudPanel |
| `tools/generar_imagenes.py` | Genera las ilustraciones de relleno, `og.png` y los iconos (necesita Pillow) |
| `tools/copia-antes.sh`, `tools/restaurar-bd-wordpress.sh` | Copia de seguridad previa y restauración de la base de datos de WordPress (los usa `PUBLICAR.md`) |
| `tests/web_test.py` | Pruebas con Playwright (ver abajo) |

## Dónde se sirve (importante)

El sitio actual es un WordPress que se mantiene. Esta web vive en **`/portada/`** y una regla de nginx hace que
`/` también la enseñe. Por eso **todas las rutas del HTML empiezan por `/portada/`** (`/portada/assets/web.css`,
etc.): así valen igual desde `/` y desde `/portada/`. El `canonical` y las direcciones de Open Graph son
absolutas (`https://tubarriopublicidad.es/...`).

### Servirla desde la raíz (si algún día no hay WordPress)

Si la web pasara a ser la raíz del sitio (carpeta `public/` como «root», sin `portada/`), quita el prefijo:

```
sed -i 's#/portada/#/#g' public/index.html public/aviso-legal.html
```

y cambia en `index.html` las direcciones de `og:image`, `twitter:image` y `logo`/`image` del JSON-LD
(`https://tubarriopublicidad.es/portada/assets/...` → `https://tubarriopublicidad.es/assets/...`). El `canonical`
del aviso legal también. Las pruebas (`tests/web_test.py`) esperan el prefijo `/portada/`.

## Cambiar textos

Edita `public/index.html` (está todo escrito en claro, por secciones: `portada`, `#servicios`, `#como`, `#contacto`).
Los tres bloques de venta de cada tarjeta son los `<li>` de `<ul class="ventajas">`. No pongas cifras ni promesas que
no se puedan cumplir. Si cambias el título o la descripción, cámbialos también en `og:` y `twitter:`.

## Cambiar el contacto

- **Correo del botón «Pide presupuesto»**: constante `CORREO` (y `ASUNTO`) al principio de `public/assets/web.js`.
  Pon el mismo correo en el `href="mailto:..."` de `index.html` (es lo que funciona si no hay JavaScript), en el
  JSON-LD (`"email"`) y en `aviso-legal.html`.
- **Teléfono / WhatsApp**: rellena `TELEFONO` en `web.js` (por ejemplo `'+34600123456'`). Mientras esté vacío no se ve
  nada. Al rellenarlo aparece «También por teléfono o WhatsApp: ...» con enlaces `tel:` y `wa.me`. No hace falta tocar
  el HTML. (El teléfono **no** está en el JSON-LD a propósito; si lo quieres allí, añádelo a mano.)

## Acceso clientes y alta de clientes

La web enlaza con el **portal** (`https://portal.tubarriopublicidad.es`), que ya tiene el área de clientes. No hay formularios,
cookies ni datos de nadie en esta web: solo enlaces.

| Dónde | Qué | Enlace |
|---|---|---|
| Franja de arriba de la cabecera (`nav.acceso`), en PC y en móvil | Botón secundario **«Acceso clientes»** | `https://portal.tubarriopublicidad.es/login` (misma pestaña) |
| Idem | Botón principal **«Solicitar acceso como cliente»** | `https://portal.tubarriopublicidad.es/alta` (misma pestaña) |
| Sección `#clientes` («Área de clientes»), entre «Cómo funciona» y el contacto | Tres líneas de lo que puede hacer un cliente, «Si ya eres cliente, entra con tu correo y tu contraseña.» y los mismos dos botones | idem |
| Pie (también en el aviso legal) | «Aviso legal», «Política de privacidad» (`https://portal.tubarriopublicidad.es/privacidad`) y «Acceso clientes» | idem |

**Activar el alta desde la web.** En `public/assets/web.js`, al principio, está `ALTA_WEB_ACTIVA` (`false` por defecto):

- `false` (ahora): «Solicitar acceso como cliente» sigue llevando a `/alta`, que de momento explica que no hay altas y da el contacto; además,
  junto a los botones (franja de arriba y sección `#clientes`) sale la nota discreta «¿Aún no eres cliente? **Escríbenos**» con enlace al correo
  (`CORREO`, asunto `ASUNTO_ALTA`) y, si hay `TELEFONO`, también a WhatsApp. Sin JavaScript también se ve la nota (es el valor por defecto).
- `true` (cuando Daniel active el alta en el portal): la nota desaparece y quedan solo los botones. Cambia `var ALTA_WEB_ACTIVA = false;` por
  `var ALTA_WEB_ACTIVA = true;` y publica de nuevo (`PUBLICAR.md`, paso 9).

Los botones no se tocan: las direcciones están en `index.html` (y las del pie en `aviso-legal.html`).

## Ejemplo en vivo

Lo principal de la portada son los mapas de seguimiento online. En la **cabecera** (franja azul «Sigue tu ruta online»)
hay dos entradas grandes, una por app, que son enlaces completos (`a.entrada`, pestaña nueva, `rel="noopener"`, `aria-label` claro):

| Entrada | Servicio debajo | Enlace |
|---|---|---|
| Mapa de seguimiento online · Wildposting | Fijación a pie de calle con engrudo | `https://wildposting.tubarriopublicidad.es/demo` |
| Mapa de seguimiento online · Cartelería | Fijación de cartelería en comercios y espacios habituales | `https://carteleria.tubarriopublicidad.es/demo` |

Cada una lleva la etiqueta «Ejemplo en vivo» y, bajo las dos, la frase «Mira en directo cómo ve un cliente su campaña:
ejemplo real, sin registrarte.». Ya **no hay** botón «Conoce nuestros servicios».

En las tarjetas de «Nuestros servicios» el nombre («Wildposting», «Cartelería», con flechita ↗) sigue siendo un enlace a su
`/demo` y abajo se mantiene el botón «Ver ejemplo en vivo» con «Sin registro…». Se quitó el botón pequeño que repetía lo mismo
junto al nombre (quedaba el mismo enlace cuatro veces por servicio). Objetivos táctiles de al menos 44 px.

## Cambiar fotos y carruseles

- Las fotos reales salen de `https://wildposting.tubarriopublicidad.es/demo/fotos.json` y
  `https://carteleria.tubarriopublicidad.es/demo/fotos.json` (atributo `data-fotos` de cada `.carrusel`). Formato:
  `{fotos:[{url, miniatura, punto, categoria, ciudad, pueblo, barrio, pie, comentario}]}` (`fecha` ya no se usa). Se usa la `miniatura` (si no hay, la `url`), hasta
  `MAX_FOTOS` (8). El pie de cada foto (sin fecha) es el campo `pie` que componen las apps (texto plano, partes separadas por « · »); si no viene (apps sin actualizar), la web lo compone con `punto`, `categoria` (solo si no está ya en `punto`, sin tildes ni mayúsculas), `ciudad`, `pueblo` y `barrio`, sin vacíos ni duplicados. El `alt` lleva ese pie y el comentario. Todo se
  inserta como texto, nunca como HTML.
- **Si el JSON falla, tarda más de 6 s o viene vacío**, se queda el relleno: tres ilustraciones propias por servicio
  (`public/assets/img/relleno-wildposting-N.svg`: pared llena de carteles; `relleno-carteleria-N.svg`: escaparate).
  Se regeneran con `python3 tools/generar_imagenes.py`. **No uses fotos de stock ni de terceros.**
- Si una foto concreta no carga, se descarta sola. Con una sola foto no se muestran flechas.
- El HTML ya lleva el relleno: **sin JavaScript** el carrusel enseña la primera ilustración y los enlaces funcionan.
- El avance automático (`INTERVALO`, 5 s) se pausa con el ratón encima, con el foco dentro y con el botón de pausa,
  y no existe con «reducir movimiento» (`prefers-reduced-motion`). Se desliza con el dedo, con los botones, con los
  puntos y con las flechas del teclado.
- Para que esas dos direcciones funcionen desde otra web, las apps de campo deben devolver cabeceras CORS
  (`Access-Control-Allow-Origin`) en `/demo/fotos.json` y las fotos deben poder cargarse desde otro dominio.

## Seguridad (CSP)

Política exacta (la misma en `docs/nginx.conf.example` y en las pruebas):

```
default-src 'self'; img-src 'self' data: https://wildposting.tubarriopublicidad.es https://carteleria.tubarriopublicidad.es; connect-src https://wildposting.tubarriopublicidad.es https://carteleria.tubarriopublicidad.es; frame-ancestors 'none'; base-uri 'self'
```

(Se añadieron `frame-ancestors` y `base-uri` a la que pedía Daniel; solo restringen más.) Por eso no hay `style=`,
`onclick=` ni `<script>` con código en el HTML: todo va en `assets/`. La única excepción es el bloque
`<script type="application/ld+json">` de `index.html`, que es un dato (no se ejecuta y la CSP no lo afecta); las
pruebas lo permiten expresamente. El JS tampoco pone `style` en los elementos: usa clases.
La CSP solo se pone en `/` y `/portada/` (en nginx), nunca en WordPress.

## Pruebas

Sin internet. Necesitan `pip install playwright pillow` y un Chromium (por defecto
`/opt/pw-browsers/chromium-1194/chrome-linux/chrome`; otra ruta con la variable `CHROMIUM`).

```
python3 tests/web_test.py [carpeta_de_capturas]
```

Sirve `public/` en `http://127.0.0.1:8765` con la CSP de producción (`/` y `/portada/…`, como hará nginx) y simula
Wildposting y Cartelería con `page.route` (`fotos.json` con CORS y fotos de prueba generadas). Comprueba:
los botones de acceso clientes (URLs exactas, misma pestaña, `aria-label`, táctiles, foco, contraste, la nota con `ALTA_WEB_ACTIVA` en `false` y en `true` a 390, 768 y 1280 px, la sección `#clientes` y los enlaces del pie), la cabecera (las dos entradas con sus textos exactos, URLs, pestaña nueva, tamaño táctil, foco visible, contraste AA, una al lado de la otra en PC y apiladas en móvil, y que «Conoce nuestros servicios» ya no existe), HTML (sin `style=`, `onclick=`, `<script>` inline, ni dominios externos; `alt`, ancho y alto; canonical, Open Graph,
JSON-LD sin dirección ni teléfono; `web.js` < 10 KB), que todos los ficheros enlazados existen desde `/` y desde
`/portada/`, el carrusel (siguiente, anterior, puntos, teclado, deslizar con el dedo, avance automático, pausa con
ratón, foco y botón, `prefers-reduced-motion`), el relleno cuando el JSON falla (red caída, error 500, vacío), una
foto que no carga, sin JavaScript, enlaces (URLs, `_blank` + `noopener`, `mailto` con asunto), el teléfono oculto
(y visible si se rellena), sin desplazamiento horizontal a 360, 390, 768, 1024, 1280 y 1440 px, CLS < 0,01, y que no
haya errores de consola ni violaciones de CSP. Las capturas (390 y 1280 px) quedan en la carpeta indicada
(390, 768 y 1280 px; por defecto `tests/capturas/`, que no se sube a git). Termina con `TODO BIEN` o la lista de fallos.

También se comprobó `docs/nginx.conf.example` con un nginx real (1.24) delante de un sitio de mentira estilo WordPress:
`/` y `/portada/…` salen con las cabeceras, y `/wp-login.php`, `/wp-admin/`, otros ficheros y páginas no las llevan.

## Dudas abiertas

- **¿`www` o sin `www`?** El sitio de CloudPanel se llama `www.tubarriopublicidad.es`. El `canonical`, el sitemap y
  las direcciones de compartir apuntan a `https://tubarriopublicidad.es/` (sin www), como se pidió. Si el sitio responde
  en `www` sin redirigir al otro, conviene que uno redirija al otro; si el bueno es el de `www`, cambia en `index.html`
  y `aviso-legal.html` `https://tubarriopublicidad.es` por `https://www.tubarriopublicidad.es` (y en `sitemap.xml` y `robots.txt`).
- **`robots.txt` y `sitemap.xml`**: con WordPress siguen mandando los suyos (este repo no los sustituye). Hay que mirar
  qué publica WordPress (¿Yoast, Rank Math?) para que la portada nueva aparezca bien en Google.
- **Aviso legal**: lleva `noindex` hasta que se rellene. Revisar el texto con la gestoría (no lleva política de cookies
  porque no usa ninguna).
