import socket
import struct


class SockServer:
    def __init__(self, host='127.0.0.1', port=1909 ):
        """
        Initialize the TCP server.
        """
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Allow the port to be reused immediately after termination
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        print("Starting server on port ", self.port )
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        self.client_socket = None
        self.client_address = None
        
        # Structure format:
        # '!'  = Network byte order (Big-endian)
        # 'i'  = 32-bit integer (4 bytes)
        # '6f' = 6 floats (32-bit each, 24 bytes total)
        # Total size = 28 bytes
        self.recv_fmt = '!i6f' 
        self.recv_size = struct.calcsize(self.recv_fmt)
        
        # Send format: 1 integer
        self.send_fmt = '!i'


    def wait_for_connection(self):
        """
        Blocks until a client connects.
        """
        print(f"Server listening on {self.host}:{self.port}...")
        self.client_socket, self.client_address = self.server_socket.accept()
        print(f"Connected to client: {self.client_address}")
        self.client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    def is_client_connected(self):
        return not self.client_socket is None


    def recv_status(self):
        """
        Waits to receive 1 int32 and 6 float32s.
        Returns a tuple: (int_value, float_1, float_2, ..., float_6)
        """
        if not self.client_socket:
            return None

        # Receive exactly the number of bytes expected
        data = self.client_socket.recv(self.recv_size)
        
        if not data:
            # Empty data usually means the client closed the connection
            self.client_socket.close()
            self.client_socket = None
            return None
            
        if len(data) < self.recv_size:
            # Handle partial reads if necessary (rare in simple local blocking scenarios)
            # For strictness, you might loop recv here until you have enough bytes.
            raise ValueError("Incomplete data received")

        # Unpack binary data into a Python tuple
        return struct.unpack(self.recv_fmt, data)


    def send_action(self, action):
        """
        Sends a single integer action back to the client.
        """
        if not self.client_socket:
            return False
            
        # Pack the integer into bytes
        data = struct.pack(self.send_fmt, int(action))

        try:
            self.client_socket.sendall(data)
            return True

        except:
            self.client_socket.close()
            self.client_socket = None
        return False


    def close(self):
        """
        Closes client and server sockets.
        """
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
            print("Client connection closed.")
        self.server_socket.close()
        print("Server socket closed.")
