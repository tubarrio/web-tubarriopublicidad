# Cómo publicar la web principal (tubarriopublicidad.es)

> **Dirección principal: `https://www.tubarriopublicidad.es/`.** El servidor ya redirige `tubarriopublicidad.es` (sin www) a `www.` (así lo tiene CloudPanel); quien escriba la dirección sin www llega igualmente. Las direcciones de la web (canonical, sitemap) usan `www`.

Léelo entero antes de empezar. Cada orden va **en una sola línea**: cópiala entera y pégala. Las que dicen
**PowerShell** van en la ventana de tu PC; las que dicen **Ubuntu** van después de entrar en el servidor.

**Qué hay ahora y qué vamos a hacer.** El sitio actual de `tubarriopublicidad.es` es un **WordPress**
(CloudPanel, usuario `tubarriopublicidad`, carpeta `/home/tubarriopublicidad/htdocs/www.tubarriopublicidad.es`).
Decidiste **cambiar solo la portada y dejar WordPress vivo**. Por eso:

- La web nueva se copia a una carpeta nueva, `portada/`, **dentro** de la del sitio. No se borra ni se cambia nada de WordPress.
- Una regla de nginx hace que `https://tubarriopublicidad.es/` enseñe la portada nueva. `/wp-admin`, `/wp-login.php`, el resto de páginas y `.well-known` siguen siendo de WordPress.
- Antes de nada se hace una **copia completa** (ficheros y base de datos) y se comprueba.
- Volver atrás es quitar la regla (paso 8). WordPress vuelve a enseñar su portada de siempre.

La web también se ve siempre en `https://tubarriopublicidad.es/portada/`, aunque no pongas la regla (paso 5).

---

## 1. Entrar en el servidor

**PowerShell** (tu PC):

```
ssh ubuntu@51.83.97.87
```

A partir de aquí, todo es **Ubuntu** (la ventana donde has entrado), salvo que diga otra cosa.

## 2. Mirar qué hay (solo mirar, no cambia nada)

```
sudo ls -la /home/tubarriopublicidad/htdocs/
```

```
sudo ls -la /home/tubarriopublicidad/htdocs/www.tubarriopublicidad.es/
```

Debes ver `wp-admin`, `wp-content`, `wp-includes`, `wp-config.php`, `index.php`… (eso es WordPress). Mira que **no** exista ya una carpeta llamada `portada`.
Si existe, o si lo que ves no se parece a WordPress, **para y pégame lo que sale**.

Descarga ahora la web nueva (esto tampoco toca el sitio; la deja en tu carpeta de `ubuntu`):

```
git clone https://github.com/tubarrio/web-tubarriopublicidad ~/web-tubarriopublicidad
```

```
ls ~/web-tubarriopublicidad/public
```

Debe salir `aviso-legal.html  assets  favicon.ico  index.html  robots.txt  sitemap.xml`.
(Si el `git clone` te pide usuario y contraseña es que el repositorio es privado: dímelo y lo hacemos de otra forma, p. ej. con `scp` desde tu PC.)

## 3. Copia de seguridad COMPLETA (obligatoria)

Una sola orden hace las dos copias (los ficheros de todo `htdocs` y la base de datos de WordPress) y las comprueba. Lee la contraseña de la base de datos del fichero `wp-config.php` y **no la enseña**:

```
sudo bash ~/web-tubarriopublicidad/tools/copia-antes.sh
```

Tiene que acabar con **`COPIA COMPLETA Y COMPROBADA`** y mostrar dos ficheros en `/home/ubuntu/copias/` con su tamaño:

- `web-antes-FECHA.tar.gz` (los ficheros: no puede pesar unos pocos bytes; en un WordPress suele ser de decenas de MB o más)
- `wordpress-bd-FECHA.sql.gz` (la base de datos: tampoco puede ser casi vacío)

Si dice `FALLO` o `HAY PROBLEMAS`, **no sigas** y pégame todo lo que salió. Vuelve a mirarlas cuando quieras:

```
ls -lh ~/copias/
```

Consejo: baja esos dos ficheros a tu PC por si acaso. **PowerShell** (cambia FECHA por la que ves en la lista; la orden `scp` baja la carpeta entera, así no hay que escribir fechas):

```
scp -r ubuntu@51.83.97.87:/home/ubuntu/copias C:\Users\tubar\copias-web
```

## 4. Subir la web nueva (carpeta `portada/`)

**Ubuntu.** Crea la carpeta (si ya existiera, esta orden da error y no hace nada: bien, para y avísame):

```
sudo mkdir /home/tubarriopublicidad/htdocs/www.tubarriopublicidad.es/portada
```

Copia la web dentro:

```
sudo cp -r ~/web-tubarriopublicidad/public/. /home/tubarriopublicidad/htdocs/www.tubarriopublicidad.es/portada/
```

Que sea del usuario del sitio (solo esa carpeta):

```
sudo chown -R tubarriopublicidad:tubarriopublicidad /home/tubarriopublicidad/htdocs/www.tubarriopublicidad.es/portada
```

Compruébalo:

```
sudo ls -la /home/tubarriopublicidad/htdocs/www.tubarriopublicidad.es/portada
```

Debe salir `index.html`, `aviso-legal.html`, `assets`, `favicon.ico`… No se ha tocado ningún fichero de WordPress.

**Ya puedes verla** (aún sin regla de nginx), en el navegador o aquí:

```
curl -sI https://tubarriopublicidad.es/portada/ | head -5
```

Debe salir `HTTP/2 200`. Si sale 404, o ves la portada de WordPress, pégame lo que sale (probablemente falta la regla del paso 5).

## 5. Que «/» enseñe la portada nueva (regla nginx)

El texto de la regla está en `docs/nginx.conf.example` (con comentarios). **Es opcional:** sin ella la portada sigue en `/portada/`. La regla solo toca `/` y `/portada/`; las cabeceras de seguridad **no** se aplican a WordPress (la política de seguridad (CSP) de la portada rompería `/wp-admin`).

### Opción A: desde CloudPanel (la más cómoda)

1. Entra en CloudPanel (`https://51.83.97.87:8443` o el panel de siempre) → **Sites** → `www.tubarriopublicidad.es` → pestaña **Vhost**.
2. Antes de cambiar nada, copia **todo** el texto que hay ahí a un bloc de notas (es tu copia para volver atrás).
3. Abre `docs/nginx.conf.example` (en GitHub: <https://github.com/tubarrio/web-tubarriopublicidad/blob/main/docs/nginx.conf.example>), copia **lo que hay entre `INICIO DE LAS REGLAS` y `FIN DE LAS REGLAS`** y pégalo **dentro del bloque `server { ... }` que tiene la línea `root`** (el de `listen 443`), justo debajo de la línea `root ...;`. No borres nada de lo que ya estaba.
4. **Save**. Si CloudPanel avisa de un error, no se aplica: borra lo pegado y avísame.

Si tu usuario de CloudPanel (rol User) no ve la pestaña **Vhost**, usa la opción B.

### Opción B: por SSH (Ubuntu)

Averigua el fichero del sitio y mira sus líneas `root` (debe salir **una sola** línea `root /home/tubarriopublicidad/htdocs/www.tubarriopublicidad.es;`):

```
sudo ls /etc/nginx/sites-enabled/
```

```
sudo grep -n "server_name\|root " /etc/nginx/sites-enabled/www.tubarriopublicidad.es.conf
```

Si el fichero se llama distinto o sale más de una línea `root`, **para y pégame lo que sale**. Si no:

Copia del fichero (para volver atrás):

```
sudo cp /etc/nginx/sites-enabled/www.tubarriopublicidad.es.conf ~/copias/vhost-antes.conf
```

Pon las reglas en un fichero propio:

```
sudo cp ~/web-tubarriopublicidad/docs/nginx.conf.example /etc/nginx/portada-tubarrio.conf
```

Añade UNA línea al fichero del sitio, justo debajo de `root`, que lee ese fichero:

```
sudo sed -i '/^[[:space:]]*root /a\    include /etc/nginx/portada-tubarrio.conf;' /etc/nginx/sites-enabled/www.tubarriopublicidad.es.conf
```

Mira que la línea ha quedado bien (debe verse `include` debajo de `root`):

```
sudo grep -n -B1 "portada-tubarrio" /etc/nginx/sites-enabled/www.tubarriopublicidad.es.conf
```

**Comprueba la configuración ANTES de aplicarla** (debe decir `syntax is ok` y `test is successful`):

```
sudo nginx -t
```

Solo si ha salido bien:

```
sudo systemctl reload nginx
```

Si `nginx -t` da error, **no recargues**: vuelve atrás con el paso 8 (opción B) y pégame el error.

### Si el sitio usa Varnish (caché de CloudPanel)

Si tras el paso 5 sigues viendo la portada antigua, en CloudPanel → Sites → el sitio → **Varnish Cache** → **Purge** (vaciar caché). Si no existe esa pestaña, no hace falta.

## 6. Comprobar con `curl` (Ubuntu o PowerShell)

La portada nueva en «/» (200, con `content-security-policy`):

```
curl -sI https://tubarriopublicidad.es/ | head -12
```

El título debe ser el de la web nueva («Tu Barrio Publicidad · Diseño, impresión y distribución»):

```
curl -s https://tubarriopublicidad.es/ | grep -o "<title>[^<]*</title>"
```

La portada también en su dirección propia (200):

```
curl -sI https://tubarriopublicidad.es/portada/ | head -5
```

WordPress sigue igual: el acceso (200, y **sin** `content-security-policy`) y el panel (302 hacia el acceso):

```
curl -sI https://tubarriopublicidad.es/wp-login.php | head -12
```

```
curl -sI https://tubarriopublicidad.es/wp-admin/ | head -5
```

Y el nombre con `www` (si responde distinto al de arriba, dímelo; ver las dudas del `README.md`):

```
curl -sI https://www.tubarriopublicidad.es/ | head -5
```

**En el navegador** (con Ctrl+F5, y también en el móvil): `https://tubarriopublicidad.es/` enseña la portada nueva con las dos tarjetas; los carruseles cargan fotos; **Pide presupuesto** abre tu correo con el asunto «Quiero presupuesto»; **Ver ejemplo en vivo** abre cada demo en pestaña nueva; entra en `https://tubarriopublicidad.es/wp-admin/` y comprueba que **WordPress funciona** como siempre; abre alguna otra página de WordPress.

## 7. Antes de dar la web por buena

- Rellena el **aviso legal**: edita `public/aviso-legal.html` (los textos `[RAZÓN SOCIAL]`, `[NIF]`, `[DOMICILIO]`) y quita la línea `noindex` y el recuadro amarillo (ver `README.md`). Después se sube de nuevo (paso 9).
- Si quieres un teléfono o WhatsApp en la web: `README.md`, «Cambiar el contacto».
- El `robots.txt` y el `sitemap.xml` de este repo **no** se usan con WordPress (los dejamos en `portada/` sin efecto): el de WordPress sigue mandando. Pregúntame si queremos revisarlos.

## 8. Volver atrás

**Quitar la regla** (WordPress vuelve a enseñar su portada de siempre; la copia no hace falta):

- Opción A (CloudPanel): Vhost → borra las líneas que pegaste (o pega el texto que guardaste en el bloc de notas) → Save.
- Opción B (Ubuntu), vuelve a poner el fichero tal como estaba:

```
sudo cp ~/copias/vhost-antes.conf /etc/nginx/sites-enabled/www.tubarriopublicidad.es.conf
```

```
sudo nginx -t
```

```
sudo systemctl reload nginx
```

Comprueba con `curl -sI https://tubarriopublicidad.es/ | head -5` y en el navegador (vacía la caché si hace falta).

**Quitar también los ficheros nuevos** (opcional; solo esa carpeta, mira bien la ruta antes de pulsar Intro):

```
sudo rm -rf /home/tubarriopublicidad/htdocs/www.tubarriopublicidad.es/portada
```

**Restaurar la copia completa** (solo si WordPress se hubiera roto de verdad; no debería, porque no se toca. **Escríbeme antes**). Los ficheros se devuelven así (cambia FECHA por la que ves en `ls ~/copias`):

```
sudo tar xzf ~/copias/web-antes-FECHA.tar.gz -C /home/tubarriopublicidad/htdocs
```

La base de datos, con el script que pide confirmación (escribes `SI`):

```
sudo bash ~/web-tubarriopublicidad/tools/restaurar-bd-wordpress.sh ~/copias/wordpress-bd-FECHA.sql.gz
```

## 9. Actualizar la web más adelante

Cuando haya cambios (textos nuevos, fotos…) y los hayas unido en GitHub. Todo en **Ubuntu**:

```
git -C ~/web-tubarriopublicidad pull
```

```
sudo cp -r ~/web-tubarriopublicidad/public/. /home/tubarriopublicidad/htdocs/www.tubarriopublicidad.es/portada/
```

```
sudo chown -R tubarriopublicidad:tubarriopublicidad /home/tubarriopublicidad/htdocs/www.tubarriopublicidad.es/portada
```

(Los cambios se ven en menos de una hora por la caché; con Ctrl+F5 antes.)

---

## Si prefieres no tocar nginx (alternativa)

- **La portada se queda en `https://tubarriopublicidad.es/portada/`** (paso 4, sin el 5) y tú la enlazas a mano: en WordPress → Apariencia → Menús → «Enlaces personalizados» con esa dirección, o un botón en tu página de inicio actual. Funciona sin cambiar nada del servidor.
- **No se recomienda** copiar la portada dentro de una página de WordPress ni meterla en un `iframe`: WordPress añade scripts y estilos propios y la política de seguridad de la portada no es compatible; el carrusel y el diseño se estropearían.
- Si algún día el sitio dejara de ser WordPress, la web se podría poner en la raíz sin `portada/` (ver «Servirla desde la raíz» en `README.md`).
