#!/bin/bash
# Copia de seguridad COMPLETA antes de tocar el sitio de tubarriopublicidad.es (WordPress en CloudPanel).
# Solo LEE el sitio: no cambia nada de él. Guarda dos ficheros en /home/ubuntu/copias/:
#   web-antes-FECHA.tar.gz        toda la carpeta htdocs del sitio (ficheros de WordPress incluidos)
#   wordpress-bd-FECHA.sql.gz     la base de datos de WordPress
# La contraseña de la base de datos se lee de wp-config.php y NO se muestra en pantalla.
# Uso (en Ubuntu, tras ssh ubuntu@51.83.97.87):  sudo bash ~/web-tubarriopublicidad/tools/copia-antes.sh
# Opcional: los dos parámetros cambian la carpeta del sitio y la de las copias.
set -u
SITIO="${1:-/home/tubarriopublicidad/htdocs/www.tubarriopublicidad.es}"
DESTINO="${2:-/home/ubuntu/copias}"
FECHA="$(date +%Y%m%d-%H%M)"
CONFIG="$SITIO/wp-config.php"
MALO=0

if [ "$(id -u)" != "0" ]; then echo "Ejecútalo con sudo (mira PUBLICAR.md)."; exit 1; fi
if [ ! -d "$SITIO" ]; then echo "No existe la carpeta $SITIO. Avisa antes de seguir."; exit 1; fi
mkdir -p "$DESTINO" || exit 1

echo "== 1. Ficheros del sitio =="
HTDOCS="$(dirname "$SITIO")"
TAR="$DESTINO/web-antes-$FECHA.tar.gz"
if tar czf "$TAR" -C "$HTDOCS" . && gzip -t "$TAR" && [ "$(tar tzf "$TAR" | wc -l)" -gt 1 ]; then
  echo "OK  $(ls -lh "$TAR" | awk '{print $5}')  $TAR  ($(tar tzf "$TAR" | wc -l) elementos)"
else
  echo "FALLO al copiar los ficheros. No sigas."; MALO=1
fi

echo "== 2. Base de datos de WordPress =="
valor() {
  sed -n "s/^[[:space:]]*define([[:space:]]*['\"]$1['\"][[:space:]]*,[[:space:]]*['\"]\(.*\)['\"][[:space:]]*)[[:space:]]*;.*/\1/p" "$CONFIG" | head -1
}
if [ ! -f "$CONFIG" ]; then
  echo "No veo wp-config.php en $SITIO: puede que no sea WordPress o que esté en otra carpeta. Avisa antes de seguir."; MALO=1
else
  BD_NOMBRE="$(valor DB_NAME)"; BD_USUARIO="$(valor DB_USER)"; BD_CLAVE="$(valor DB_PASSWORD)"; BD_SERVIDOR="$(valor DB_HOST)"
  BD_SERVIDOR="${BD_SERVIDOR:-localhost}"
  if [ -z "$BD_NOMBRE" ] || [ -z "$BD_USUARIO" ]; then
    echo "No he podido leer DB_NAME / DB_USER de wp-config.php. Avisa antes de seguir."; MALO=1
  else
    echo "Base de datos: $BD_NOMBRE   usuario: $BD_USUARIO   servidor: $BD_SERVIDOR   (contraseña: leída, no se muestra)"
    SQL="$DESTINO/wordpress-bd-$FECHA.sql.gz"
    MYSQL_PWD="$BD_CLAVE" mysqldump --no-tablespaces --single-transaction -h "$BD_SERVIDOR" -u "$BD_USUARIO" "$BD_NOMBRE" 2>"$DESTINO/.error-mysqldump.txt" | gzip > "$SQL"
    if [ "${PIPESTATUS[0]}" = "0" ] && gzip -t "$SQL" && zcat "$SQL" | tail -3 | grep -q "Dump completed"; then
      echo "OK  $(ls -lh "$SQL" | awk '{print $5}')  $SQL  (termina en «Dump completed»)"
    else
      echo "FALLO al copiar la base de datos. Mensaje:"; cat "$DESTINO/.error-mysqldump.txt"; MALO=1
    fi
    rm -f "$DESTINO/.error-mysqldump.txt"
  fi
fi
unset BD_CLAVE
chown -R ubuntu:ubuntu "$DESTINO" 2>/dev/null
chmod 600 "$DESTINO"/*"$FECHA"* 2>/dev/null

echo
ls -lh "$DESTINO"
if [ "$MALO" = "0" ]; then echo; echo "COPIA COMPLETA Y COMPROBADA. Ya puedes seguir con el siguiente paso."; else echo; echo "HAY PROBLEMAS: NO sigas con el siguiente paso y pégame todo lo que ha salido."; exit 1; fi
