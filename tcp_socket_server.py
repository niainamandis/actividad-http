import socket
import json
import sys
 
def receive_full_message(connection_socket, buff_size):

     # recibimos la primera parte del mensaje
    recv_message = connection_socket.recv(buff_size)
    full_message = recv_message
    sep = b"\r\n\r\n"

    # verificamos que lleguen los headers
    while sep not in full_message:
        recv_message = connection_socket.recv(buff_size)
        full_message += recv_message

    headers_raw, body_raw = full_message.split(sep)
    header_parsed = parse_HTTP_message(headers_raw + sep)

    #verificamos si llegó todo el contenido de body (o si no tiene == 0)
    content_length = int(header_parsed["headers"].get("Content-Length",0))
     # entramos a un while para recibir el resto y seguimos esperando información
     # mientras el buffer no contenga todo el body
    while len(body_raw)<content_length:
         # recibimos un nuevo trozo del mensaje
         recv_message = connection_socket.recv(buff_size)
         # lo añadimos al mensaje "completo"
         body_raw += recv_message

     # finalmente retornamos el mensaje
    return headers_raw + sep + body_raw

 
def parse_HTTP_message(http_message: bytes):
    # separar header del body
    # nota: agregar b"" => busca en bytes :D
    headers_cod, body = http_message.split(b"\r\n\r\n")
    # decodificar las lineas del header
    headers_text = headers_cod.decode()
    lines = headers_text.split("\r\n")
    # guardar el header en un diccionario
    headers = {}
    for line in lines[1:]: #ignoramos lines[0] pke es solo get y http
        if not line: continue
        key, val = line.split(": ", 1)
        headers[key] = val
    # juntarlo con el body y retornar 
    return {
            "f_line": lines[0],
            "headers": headers,
            "body": body
            }
 

# NOTE: debería funcionar pke en ningún momento decodificamos
# body en parse,,, entonces body debería seguir en bytes
def create_HTTP_message(parsed_msg: dict):
    #reconstruir el msje http
    msg_text = parsed_msg["f_line"] + "\r\n"
    for key, val in parsed_msg["headers"].items():
        msg_text += f"{key}" + ": " + f"{val}" + "\r\n"
    #fin headers "\r\n\r\n"
    msg_text += "\r\n"
    #codificarlo
    header_bytes = msg_text.encode()
    return header_bytes + parsed_msg["body"]


if __name__ == "__main__":

    # para leer el nombre o ruta del archivo json
     config_path = sys.argv[1]
     with open(config_path) as file:
        data = json.load(file)
     username = data.get("user", "usuario_desconocido")
     print(f"server iniciado para el usuario: {username} :3")

     # definimos el tamaño del buffer de recepción y la secuencia de fin de mensaje
     buff_size = 4
     IP_VM = 'localhost'
     listen_socket_address = (IP_VM, 8000)
     
     print('Creando socket - Servidor')
     # creamos un socket orientado a conexión
     listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
     # le indicamos al server socket que debe atender peticiones en la dirección address
     listen_socket.bind(listen_socket_address)
     # definimos que puede tener hasta 3 peticiones de conexión encoladas
     listen_socket.listen(3)
     
     # nos quedamos esperando a que llegue una petición de conexión
     print(f'... Esperando clientes en http://{IP_VM}:8000')
     while True:
        # cuando llega una petición de conexión la aceptamos
        # y se crea un nuevo socket que se comunicará con el cliente
        client_socket, client_socket_address = listen_socket.accept()
 
        # recibimos y parseamos la request del cliente
        recv_message = receive_full_message(client_socket, buff_size)
        parsed_req = parse_HTTP_message(recv_message)
        print(f' -> Se ha recibido la siguiente petición: {parsed_req["f_line"]}')
 
        # TODO

        # extraer el host de la request del cliente 

        # crear un socket para el servidor con host y conectarse 
        
        # enviar la request al servidor

        # recibir respuesta del servidor 

        # reenviar respuesta al cliente 

        # cerrar la conexión al servidor
        
        # cerramos la conexión con el cliente
        client_socket.close()
        print(f"conexión con {client_socket_address} ha sido cerrada")
 
