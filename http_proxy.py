import socket
import json
import sys
 
def receive_full_message(connection_socket, buff_size):
  # recibimos la primera parte para buscar los headers
  recv_message = connection_socket.recv(buff_size)
  full_message = recv_message
  sep = b"\r\n\r\n"

  # verificamos que lleguen todos los headers
  while sep not in full_message:
    recv_message = connection_socket.recv(buff_size)
    full_message += recv_message

  headers_raw, body_raw = full_message.split(sep)
  header_parsed = parse_HTTP_message(headers_raw + sep)

  # chequeamos si viene un content-length para saber cuánto body falta leer
  if "Content-Length" in header_parsed["headers"]:
    content_length = int(header_parsed["headers"]["Content-Length"])
    # loopeamos hasta que el largo del body raw alcance el indicado en el header
    while len(body_raw) < content_length:
      recv_message = connection_socket.recv(buff_size)
      body_raw += recv_message
  # o revisamos si el mensaje viene particionado (chuncked)
  elif header_parsed["headers"].get("Transfer-Encoding", "") == "chunked":
    # el fin de un mensaje chunked es un 0 seguido del sep
    while b"0\r\n\r\n" not in body_raw:
      recv_message = connection_socket.recv(buff_size)
      body_raw += recv_message

  # finalmente retornamos el mensaje en bytes
  return headers_raw + sep + body_raw

 
def parse_HTTP_message(http_message: bytes):
  # separaramos header del body
  headers_cod, body = http_message.split(b"\r\n\r\n", 1)
  # pasamos los headers a texto para procesar más fácil
  headers_text = headers_cod.decode()
  lines = headers_text.split("\r\n")
  # guardarmos el header en un diccionario
  headers = {}
  for line in lines[1:]: # ignoramos lines[0] pke es solo get y http
    if not line: continue
    key, val = line.split(": ", 1)
    headers[key] = val
  # lo juntamos con el body y retornamos 
  return {
    "f_line": lines[0],
    "headers": headers,
    "body": body
  }
 

# NOTE: funciona pke en ningún momento decodificamos body en parse,
# entonces body debería seguir en bytes
def create_HTTP_message(parsed_msg: dict):
  # reconstruir el msje http
  msg_text = parsed_msg["f_line"] + "\r\n"
  for key, val in parsed_msg["headers"].items():
    msg_text += f"{key}: {val}\r\n"
  # fin headers "\r\n\r\n"
  msg_text += "\r\n"
  # pasamos el string a bytes y pegamos en body tal cual
  header_bytes = msg_text.encode()
  return header_bytes + parsed_msg["body"]

if __name__ == "__main__":
  # cargamos la config desde el json que pasamos desde la terminal 
  config_path = sys.argv[1]
  with open(config_path) as file:
    data = json.load(file)
  
  username = data.get("user", "usuario_desconocido")
  blocked_url = data.get("blocked", [])
  forbidden_words = data.get("forbidden_words", [])
  image_root = "/cat.jpg"

  print(f"server iniciado para el usuario: {username} :3")

  # setup inicial del proxy
  buff_size = 4
  IP_VM = "192.168.64.2" # amandis 192.168.64.2
                         # dani 10.0.2.15
  listen_socket_address = (IP_VM, 8000)
  
  print("Creando socket de escucha - Proxy")
  # creamos un socket orientado a conexión
  listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  # le indicamos al socket de escucha que debe atender peticiones en 
  # la dirección address (maquina virtual)
  listen_socket.bind(listen_socket_address)
  # definimos que puede tener hasta 3 peticiones de conexión encoladas
  listen_socket.listen(3)
  
  # nos quedamos esperando a que llegue una petición de conexión
  print(f"... Esperando clientes en http://{IP_VM}:8000")
  while True:
    # aceptamos al cliente y guardamos su socket 
    client_socket, client_socket_address = listen_socket.accept()
 
    # recibimos y parseamos la request del cliente
    recv_message = receive_full_message(client_socket, buff_size)
    parsed_req = parse_HTTP_message(recv_message)
    print(f"-> Se ha recibido la siguiente petición: {parsed_req['f_line']}")
      
    # revisamos si la página está bloqueada
    url_req = parsed_req["f_line"].split(" ")[1]
    url_req = url_req.removeprefix("http://").removeprefix("https://")
    is_blocked = False
    
    for url in blocked_url:
      if url_req.startswith(url):
        is_blocked = True

    # revisamos si la request es por la imagen local
    is_image_request = url_req.endswith(image_root)

    # si la request es por la imagen
    if is_image_request: 
      print(f"Mostrando imagen local {image_root}")

      # abrimos la imagen en modo lectura de bytes
      with open("cat.jpg", "rb") as f:
        img_body = f.read()

      response = {
        "f_line": "HTTP/1.1 200 OK",
        "headers": {
          "Content-Type": "image/jpeg",
          "Content-Length": str(len(img_body)),
          "Connection": "keep-alive",
          "Access-Control-Allow-Origin": "*",
        },
        "body": img_body
      }

      server_ans = create_HTTP_message(response)

    # si está bloqueada 
    elif is_blocked:
      print(f"La página {url_req} está bloqueada")

      # armamos el html de error
      # este pide /cat.jpg que lo envia a is_image_resquest 
      html_body = """<!DOCTYPE html> 
        <html lang="es">
          <head><meta charset="UTF-8">
            <title>CC4303</title>
          </head>
          <body>
            <h1>Página bloqueada</h1>
            <img src="/cat.jpg" alt="gato">
          </body>
        </html>""".encode()

      # respondemos un msje http
      response = {
        "f_line": "HTTP/1.1 403 Forbidden",
        "headers": {
          "Content-Type": "text/html; charset=utf-8",
          "Content-Length": str(len(html_body)),
          "Connection": "keep-alive",
          "Access-Control-Allow-Origin": "*",
          "X-ElQuePregunta": username
        },
        "body": html_body
      }
 
      # el mensaje debe pasarse a bytes antes de ser enviado
      server_ans = create_HTTP_message(response)

    # sino: enviar el request al servidor
    else:

      # extraemos el dominio la request del cliente 
      server_domain = parsed_req["headers"]["Host"]
      server_host = server_domain.split(":", 1)[0]
      server_port = int(server_domain.split(":", 1)[1]) if ":" in server_domain else 80

      # creamos un socket para hablar con el servidor 
      server_socket_address = (server_host, server_port)
      server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      print(f"-> Conectando a {server_host}:{server_port}")
      server_socket.connect(server_socket_address)
      print("Conexión con el servidor establecida")
      
      # añadimos al header quién pregunta 
      parsed_req["headers"]["X-ElQuePregunta"] = username

      # pasamos la request a bytes para poder enviarla al servidor
      modified_request = create_HTTP_message(parsed_req)

      # enviamos la request al servidor
      server_socket.send(modified_request)

      # capturamos la respuesta del servidor 
      server_ans = receive_full_message(server_socket, buff_size)
      server_parsed_req = parse_HTTP_message(server_ans)
      print(f"-> Respuesta recibida del servidor: {len(server_ans)} bytes")

      # reemplazando contenido
      # pasamos a texto para poder buscar las palabras
      body_text = server_parsed_req["body"].decode()
      for words in forbidden_words:
          for bad_word, replacement in words.items():
              # buscamos en el body todas las palabras baneadas y
              # las reemplazamos por lo pedido
              body_text = body_text.replace(bad_word,replacement)
      new_body = body_text.encode()
      # actualizamos el body
      server_parsed_req["body"] = new_body
      # actualizamos el largo del contenido
      server_parsed_req["headers"]["Content-Length"] = str(len(new_body))
      # pasamos la respuesta a bytes para mandarla al server
      ans_final = create_HTTP_message(server_parsed_req)


      # cerramos la conexión con el servidor
      server_socket.close()
      print(f"Conexión con {server_host}:{server_port} ha sido cerrada")

    # reenviamos la respuesta al cliente 
    client_socket.send(ans_final)

    # cerramos la conexión con el cliente
    client_socket.close()
    print(f"Conexión con {client_socket_address} ha sido cerrada")
