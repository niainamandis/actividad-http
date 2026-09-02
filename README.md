# Actividad HTTP: Construir un Proxy - CC4303

Proxy HTTP en Python que reenvía peticiones entre cliente y servidor, bloquea páginas prohibidas, reemplaza palabras inadecuadas en el contenido y maneja mensajes con buffers de distinto tamaño.

## Requisitos

Python 3. Solo se usan las librerías estándar `socket`, `json` y `sys`.

## Ejecución

Antes de correr el proxy, ajusta la variable `IP_VM` dentro de `http_proxy.py` según tu propia IP o máquina virtual.

```bash
python3 http_proxy.py config.json
```

El proxy queda escuchando en `http://IP_VM:8000`. Para probarlo:

```bash
curl -x IP_VM:8000 http://dominio.cl
```

O configurando `IP_VM:8000` como proxy HTTP en el navegador.

