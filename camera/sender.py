
# sender.py (run this on upstairs computer after starting receiver.py)
import socket
import zlib
from dotenv import load_dotenv
import os

load_dotenv()

host_ip = os.environ.get('HOST_IP')
host_port = os.environ.get("PORT")
receive_buffer = os.environ.get("RECEIVE_BUFFER_SIZE")


def send_file(filename, host):
    # Create a client socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Connect to the server (downstairs computer)
    client_socket.connect((host_ip, host_port))

    # Send filename
    client_socket.send(os.path.basename(filename).encode())

    # Open and send file
    with open(filename, 'rb') as f:
        while True:
            # Read file in chunks
            data = f.read(4096)
            if not data:
                break

            # Compress and send data
            compressed_data = zlib.compress(data)
            client_socket.send(compressed_data)

    print("File transfer complete!")
    client_socket.close()


if __name__ == "__main__":
    # Replace with your file path and downstairs computer's IP address
    send_file("some_file.avi", "192.168.1.100")  # Example IP address
