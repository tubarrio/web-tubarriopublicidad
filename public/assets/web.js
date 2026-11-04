/* Tu Barrio Publicidad · web principal. JavaScript normal, sin librerías ni servicios externos.
   Si este fichero no carga, la web se ve igual: el carrusel enseña su primera imagen y los enlaces funcionan. */
(function () {
  'use strict';

  /* ===== CONFIGURACIÓN: el único sitio donde cambiar contacto y fotos ===== */
  var CORREO = 'tubarriopublicidad@gmail.com';   // correo del botón «Pide presupuesto»
  var ASUNTO = 'Quiero presupuesto';             // asunto que sale precargado
  var TELEFONO = '';                             // p. ej. '+34600123456' (con prefijo, sin espacios). Vacío = oculto
  var MAX_FOTOS = 8;                             // fotos reales por carrusel
  var INTERVALO = 5000;                          // milisegundos entre fotos (avance automático)
  var ESPERA_JSON = 6000;                        // si el JSON tarda más, se queda el relleno
  /* ======================================================================= */

  var quieta = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  function el(tag, cls, txt) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (txt) e.textContent = txt;
    return e;
  }

  /* ---------- Contacto ---------- */
  function contacto() {
    var b = document.getElementById('pide-presupuesto');
    if (b && CORREO) b.href = 'mailto:' + CORREO + '?subject=' + encodeURIComponent(ASUNTO);
    if (!TELEFONO) return;
    var caja = document.getElementById('bloque-telefono');
    var t = document.getElementById('enlace-telefono');
    var w = document.getElementById('enlace-whatsapp');
    if (!caja || !t || !w) return;
    t.href = 'tel:' + TELEFONO.replace(/[^\d+]/g, '');
    t.textContent = TELEFONO;
    w.href = 'https://wa.me/' + TELEFONO.replace(/\D/g, '');
    caja.hidden = false;
  }

  /* ---------- Carrusel ---------- */
  function Carrusel(raiz) {
    var lista = raiz.querySelector('.slides');
    var originales = [].slice.call(lista.children);
    var slides = originales.slice();
    var actual = 0, timer = null, pausaUsuario = false, encima = false, dentro = false;
    var ant, sig, puntos, pp, estado;

    function montarControles() {
      raiz.classList.add('on');
      raiz.tabIndex = 0;
      ant = el('button', 'flecha ant'); ant.type = 'button'; ant.setAttribute('aria-label', 'Foto anterior'); ant.innerHTML = '&#8249;';
      sig = el('button', 'flecha sig'); sig.type = 'button'; sig.setAttribute('aria-label', 'Foto siguiente'); sig.innerHTML = '&#8250;';
      puntos = el('div', 'puntos');
      pp = el('button', 'pp'); pp.type = 'button';
      estado = el('p', 'solo-lector'); estado.setAttribute('aria-live', 'polite');
      raiz.appendChild(ant); raiz.appendChild(sig); raiz.appendChild(puntos); raiz.appendChild(pp); raiz.appendChild(estado);
      ant.addEventListener('click', function () { manual(-1); });
      sig.addEventListener('click', function () { manual(1); });
      pp.addEventListener('click', function () { pausaUsuario = !pausaUsuario; pintaPP(); reloj(); });
      raiz.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowLeft') { manual(-1); e.preventDefault(); }
        else if (e.key === 'ArrowRight') { manual(1); e.preventDefault(); }
      });
      raiz.addEventListener('mouseenter', function () { encima = true; reloj(); });
      raiz.addEventListener('mouseleave', function () { encima = false; reloj(); });
      raiz.addEventListener('focusin', function () { dentro = true; reloj(); });
      raiz.addEventListener('focusout', function () { dentro = false; reloj(); });
      document.addEventListener('visibilitychange', reloj);
      var x0 = null;
      raiz.addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; }, { passive: true });
      raiz.addEventListener('touchend', function (e) {
        if (x0 === null) return;
        var dx = e.changedTouches[0].clientX - x0; x0 = null;
        if (Math.abs(dx) > 40) manual(dx < 0 ? 1 : -1);
      }, { passive: true });
      if (quieta) pp.hidden = true;
      pintaPP();
    }

    function pintaPP() {
      pp.textContent = pausaUsuario ? '▶' : '❚❚';
      pp.setAttribute('aria-label', pausaUsuario ? 'Reanudar el avance automático' : 'Pausar el avance automático');
    }

    function pintar(rehacer) {
      var n = slides.length;
      if (rehacer) {
        lista.textContent = '';
        puntos.textContent = '';
        slides.forEach(function (s, i) {
          lista.appendChild(s);
          var p = el('button', 'punto'); p.type = 'button';
          p.setAttribute('aria-label', 'Ir a la foto ' + (i + 1) + ' de ' + n);
          p.addEventListener('click', function () { manual(slides.indexOf(s) - actual); });
          puntos.appendChild(p);
        });
        var multi = n > 1;
        ant.hidden = sig.hidden = puntos.hidden = !multi;
        pp.hidden = !multi || quieta;
      }
      slides.forEach(function (s, i) {
        s.classList.toggle('activa', i === actual);
        s.setAttribute('aria-hidden', i === actual ? 'false' : 'true');
        var p = puntos.children[i];
        if (i === actual) p.setAttribute('aria-current', 'true'); else p.removeAttribute('aria-current');
        var img = s.querySelector('img');
        if (img && img.loading === 'lazy' && Math.abs(i - actual) <= 1) img.loading = 'eager';
      });
      estado.textContent = 'Foto ' + (actual + 1) + ' de ' + n;
    }

    function ir(d) { actual = (actual + d + slides.length) % slides.length; pintar(false); }
    function manual(d) { ir(d); reloj(); }

    function reloj() {
      clearInterval(timer); timer = null;
      var parar = quieta || pausaUsuario || encima || dentro || document.hidden || slides.length < 2;
      raiz.setAttribute('data-auto', parar ? 'no' : 'si');
      if (!parar) timer = setInterval(function () { ir(1); }, INTERVALO);
    }

    function norm(t) {
      var s = String(t == null ? '' : t);
      try { s = s.normalize('NFD').replace(/[\u0300-\u036f]/g, ''); } catch (e) {}
      return s.toLowerCase().replace(/\s+/g, ' ').trim();
    }

    // Pie de foto (siempre texto, sin fecha): el campo «pie» de la app; si no viene, se compone aquí.
    function pieDe(f) {
      if (typeof f.pie === 'string' && f.pie.trim()) return f.pie.trim();
      var punto = String(f.punto == null ? '' : f.punto).trim();
      var cat = String(f.categoria == null ? '' : f.categoria).trim();
      if (cat && punto && norm(punto).indexOf(norm(cat)) >= 0) cat = '';
      var vistos = [], partes = [];
      [punto, cat, f.ciudad, f.pueblo, f.barrio].forEach(function (v) {
        v = String(v == null ? '' : v).trim();
        var k = norm(v);
        if (!k || vistos.indexOf(k) >= 0) return;
        vistos.push(k); partes.push(v);
      });
      return partes.join(' · ');
    }

    function diapositiva(f, base, tema, n) {
      var src;
      try { src = new URL(f.miniatura || f.url, base); } catch (e) { return null; }
      if (src.protocol !== 'https:') return null;
      var li = el('li', 'slide real');
      var img = el('img');
      var pie = pieDe(f);
      var alt = tema + (pie ? ': ' + pie : '') + (f.comentario ? '. ' + String(f.comentario).slice(0, 120) : '');
      img.alt = alt || tema + ': foto de la campaña de ejemplo';
      img.width = 800; img.height = 600;
      if (n > 0) img.loading = 'lazy';
      img.addEventListener('error', function () {
        var i = slides.indexOf(li);
        if (i < 0) return;
        slides.splice(i, 1);
        if (!slides.length) slides = originales.slice();
        actual = Math.min(actual, slides.length - 1);
        pintar(true); reloj();
      });
      img.src = src.href;
      li.appendChild(img);
      if (pie) li.appendChild(el('p', 'pie-foto', pie));
      return li;
    }

    function cargar() {
      var url = raiz.getAttribute('data-fotos'), tema = raiz.getAttribute('data-tema') || 'Campaña';
      if (!url || !window.fetch) return;
      var ctl = window.AbortController ? new AbortController() : null;
      var corte = setTimeout(function () { if (ctl) ctl.abort(); }, ESPERA_JSON);
      fetch(url, { mode: 'cors', credentials: 'omit', signal: ctl ? ctl.signal : undefined })
        .then(function (r) { if (!r.ok) throw new Error('http'); return r.json(); })
        .then(function (j) {
          clearTimeout(corte);
          var fotos = (j && Array.isArray(j.fotos) ? j.fotos : []).filter(function (f) { return f && (f.miniatura || f.url); }).slice(0, MAX_FOTOS);
          var nuevas = [];
          fotos.forEach(function (f) { var s = diapositiva(f, url, tema, nuevas.length); if (s) nuevas.push(s); });
          if (!nuevas.length) return;          // vacío: se queda el relleno
          slides = nuevas; actual = 0; raiz.classList.add('con-fotos');
          pintar(true); reloj();
        })
        .catch(function () { clearTimeout(corte); /* falla: se queda el relleno */ });
    }

    montarControles();
    pintar(true);
    reloj();
    cargar();
  }

  function iniciar() {
    contacto();
    [].forEach.call(document.querySelectorAll('.carrusel'), Carrusel);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar); else iniciar();
})();
