# receiver.py (run this on downstairs computer first)
import socket
import zlib
from dotenv import load_dotenv
import os

load_dotenv()

host_ip = os.environ.get('HOST_IP')
host_port = os.environ.get("PORT")
receive_buffer = os.environ.get("RECEIVE_BUFFER_SIZE")


def receive_file():
    # Create a server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Listen on all network interfaces on port 12345
    server_socket.bind((host_ip, host_port))
    server_socket.listen(1)

    print("Waiting for connection...")

    # Accept incoming connection
    client_socket, address = server_socket.accept()
    print(f"Connected to {address}")

    # Receive file name
    buffer_size = 1024
    filename = client_socket.recv(buffer_size).decode()
    print(f"Receiving {filename}")

    # Open file for writing
    with open(f"received_{filename}", 'wb') as f:
        while True:
            # Receive compressed data in chunks
            compressed_data = client_socket.recv(receive_buffer)
            if not compressed_data:
                break

            # Decompress and write to file
            data = zlib.decompress(compressed_data)
            f.write(data)

    print("File transfer complete!")
    client_socket.close()
    server_socket.close()


if __name__ == "__main__":
    receive_file()
