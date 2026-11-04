#!/usr/bin/env python3
"""Genera las imágenes propias de la web (sin fotos de terceros):
 - 3 ilustraciones de relleno por servicio (SVG): pared llena de carteles y escaparate.
 - og.png (1200x630) para compartir en redes.
 - favicon.ico y apple-touch-icon a partir del logo.
Uso: python3 tools/generar_imagenes.py   (necesita Pillow solo para og.png y los iconos)
"""
import os, random
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(RAIZ, 'public', 'assets', 'img')
COLORES = ['#b3182a', '#f2a900', '#1f9fbf', '#101a2b', '#fdf6e3', '#e4572e', '#6f121d']

def cartel(r, x, y, w, h, rot):
    c = r.choice(COLORES)
    claro = c in ('#fdf6e3', '#f2a900')
    tinta = '#101a2b' if claro else '#fdf6e3'
    s = f'<g transform="rotate({rot} {x+w/2:.0f} {y+h/2:.0f})">'
    s += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{c}" stroke="#101a2b" stroke-opacity=".25" stroke-width="1.5"/>'
    s += f'<rect x="{x+w*.1:.0f}" y="{y+h*.1:.0f}" width="{w*.8:.0f}" height="{max(h*.14,5):.0f}" fill="{tinta}" opacity=".9"/>'
    if r.random() < .6:
        s += f'<circle cx="{x+w/2:.0f}" cy="{y+h*.5:.0f}" r="{min(w,h)*.2:.0f}" fill="{tinta}" opacity=".85"/>'
    else:
        s += f'<rect x="{x+w*.15:.0f}" y="{y+h*.4:.0f}" width="{w*.7:.0f}" height="{h*.25:.0f}" fill="{tinta}" opacity=".85"/>'
    for i in range(2):
        s += f'<rect x="{x+w*.1:.0f}" y="{y+h*(.74+i*.1):.0f}" width="{w*(.8-i*.3):.0f}" height="{max(h*.04,3):.0f}" fill="{tinta}" opacity=".7"/>'
    return s + '</g>'

def pared(sem):
    r = random.Random(sem)
    s = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="800" height="600">'
    s += '<rect width="800" height="600" fill="#8c8a84"/>'
    for j in range(0, 600, 40):  # ladrillos
        off = 0 if (j // 40) % 2 == 0 else 40
        for i in range(-80, 800, 80):
            s += f'<rect x="{i+off}" y="{j}" width="78" height="38" fill="{r.choice(["#9a8f84","#8f8a80","#a39a8c"])}"/>'
    for fila in range(4):
        for col in range(5):
            w = r.randint(120, 170); h = int(w * r.choice([1.3, 1.4, 1.5]))
            x = col * 160 - 20 + r.randint(-18, 18); y = fila * 150 - 60 + r.randint(-14, 14)
            s += cartel(r, x, y, w, h, r.randint(-4, 4))
    # chincheta de mapa: seguimiento online
    px, py = r.randint(560, 680), r.randint(380, 440)
    s += f'<g transform="translate({px} {py})"><ellipse cx="0" cy="62" rx="22" ry="7" fill="#000" opacity=".3"/><path d="M0 60C-40 10 -46 -6 -46 -22a46 46 0 1 1 92 0c0 16 -6 32 -46 82z" fill="#b3182a" stroke="#fdf6e3" stroke-width="5"/><circle cx="0" cy="-22" r="16" fill="#fdf6e3"/></g>'
    return s + '</svg>'

def escaparate(sem):
    r = random.Random(sem)
    s = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="800" height="600">'
    s += '<rect width="800" height="600" fill="#d9d3c4"/><rect y="520" width="800" height="80" fill="#6b6a66"/>'
    # toldo a rayas
    for i in range(10):
        s += f'<rect x="{i*80}" y="40" width="80" height="90" fill="{"#b3182a" if i%2==0 else "#fdf6e3"}"/>'
    s += '<path d="M0 130h800v22q-20 24 -40 0q-20 24 -40 0q-20 24 -40 0q-20 24 -40 0q-20 24 -40 0q-20 24 -40 0q-20 24 -40 0q-20 24 -40 0q-20 24 -40 0q-20 24 -40 0q-20 24 -40 0q-20 24 -40 0q-20 24 -40 0q-20 24 -40 0q-20 24 -40 0q-20 24 -40 0q-20 24 -40 0q-20 24 -40 0q-20 24 -40 0q-20 24 -40 0z" fill="#8c1220"/>'
    s += '<rect x="60" y="190" width="470" height="330" fill="#bfe3ee" stroke="#101a2b" stroke-width="10"/>'
    s += '<path d="M60 520L260 190h90L150 520z" fill="#fff" opacity=".25"/>'
    s += '<rect x="580" y="190" width="170" height="330" fill="#a9d6e4" stroke="#101a2b" stroke-width="10"/><circle cx="600" cy="360" r="8" fill="#101a2b"/>'
    # carteles dentro del escaparate
    pos = [(90, 220, 90, 125), (200, 215, 100, 140), (320, 225, 80, 112), (420, 220, 90, 125),
           (110, 380, 80, 110), (215, 385, 70, 98), (310, 380, 100, 130)]
    for (x, y, w, h) in pos[:r.randint(5, 7)]:
        s += cartel(r, x, y, w, h, r.randint(-3, 3))
    # cartel en la puerta
    s += cartel(r, 610, 250, 110, 150, 0)
    # mostrador y farola
    s += '<rect x="390" y="470" width="130" height="50" fill="#6f4a30"/><rect x="60" y="500" width="470" height="20" fill="#101a2b" opacity=".25"/>'
    px, py = r.randint(120, 480), 80
    s += f'<g transform="translate(765 205)"><path d="M0 40C-26 6 -30 -4 -30 -14a30 30 0 1 1 60 0c0 10 -4 20 -30 54z" fill="#f2a900" stroke="#101a2b" stroke-width="4"/><circle cx="0" cy="-14" r="10" fill="#101a2b"/></g>'
    return s + '</svg>'

def main():
    for n in range(1, 4):
        open(os.path.join(IMG, f'relleno-wildposting-{n}.svg'), 'w').write(pared(n * 7))
        open(os.path.join(IMG, f'relleno-carteleria-{n}.svg'), 'w').write(escaparate(n * 11))
    from PIL import Image, ImageDraw, ImageFont
    logo = Image.open(os.path.join(IMG, 'logo.png')).convert('RGBA')
    og = Image.new('RGB', (1200, 630), '#ffffff')
    d = ImageDraw.Draw(og)
    d.rectangle([0, 0, 1200, 14], fill='#b3182a'); d.rectangle([0, 616, 1200, 630], fill='#b3182a')
    l = logo.resize((470, 470), Image.LANCZOS)
    og.paste(l, (70, 80), l)
    f = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    g = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    d.text((590, 170), 'Tu Barrio', font=ImageFont.truetype(f, 92), fill='#101a2b')
    d.text((590, 270), 'Publicidad', font=ImageFont.truetype(f, 92), fill='#b3182a')
    for i, t in enumerate(['Diseño, impresión y distribución', 'de publicidad local. Sigue tu', 'campaña online en el mapa.']):
        d.text((590, 400 + i * 44), t, font=ImageFont.truetype(g, 34), fill='#101a2b')
    og.save(os.path.join(IMG, 'og.png'), optimize=True)
    base = Image.open(os.path.join(IMG, 'logo.png'))
    base.resize((180, 180), Image.LANCZOS).save(os.path.join(IMG, 'apple-touch-icon.png'))
    base.resize((48, 48), Image.LANCZOS).save(os.path.join(RAIZ, 'public', 'favicon.ico'), sizes=[(16, 16), (32, 32), (48, 48)])
    base.resize((32, 32), Image.LANCZOS).save(os.path.join(IMG, 'favicon-32.png'))

if __name__ == '__main__':
    main()
