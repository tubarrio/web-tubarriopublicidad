#!/bin/bash
# Restaura la base de datos de WordPress desde una copia hecha con copia-antes.sh.
# SOLO si WordPress se ha roto de verdad (no debería: esta web no toca su base de datos).
# Uso: sudo bash ~/web-tubarriopublicidad/tools/restaurar-bd-wordpress.sh /home/ubuntu/copias/wordpress-bd-FECHA.sql.gz
set -u
SITIO="${2:-/home/tubarriopublicidad/htdocs/www.tubarriopublicidad.es}"
FICHERO="${1:-}"
CONFIG="$SITIO/wp-config.php"
[ "$(id -u)" = "0" ] || { echo "Ejecútalo con sudo."; exit 1; }
[ -f "$FICHERO" ] && gzip -t "$FICHERO" || { echo "Indica una copia .sql.gz que exista y esté bien."; exit 1; }
valor() { sed -n "s/^[[:space:]]*define([[:space:]]*['\"]$1['\"][[:space:]]*,[[:space:]]*['\"]\(.*\)['\"][[:space:]]*)[[:space:]]*;.*/\1/p" "$CONFIG" | head -1; }
N="$(valor DB_NAME)"; U="$(valor DB_USER)"; P="$(valor DB_PASSWORD)"; H="$(valor DB_HOST)"; H="${H:-localhost}"; PT=""; case "$H" in /*) ;; *:*) PT="${H##*:}"; H="${H%:*}" ;; esac
[ -n "$N" ] && [ -n "$U" ] || { echo "No puedo leer wp-config.php."; exit 1; }
echo "Esto SUSTITUYE el contenido actual de la base de datos «$N» por el de la copia $FICHERO."
read -r -p "Escribe SI en mayúsculas para continuar: " R
[ "$R" = "SI" ] || { echo "Cancelado, no se ha tocado nada."; exit 1; }
zcat "$FICHERO" | MYSQL_PWD="$P" mysql -h "$H" ${PT:+-P "$PT"} -u "$U" "$N" && echo "Base de datos restaurada." || echo "FALLO al restaurar."
