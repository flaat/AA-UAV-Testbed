class Buffer:
    """
    The buffer class is responsible for the separation of the data that come from the network
    """

    def __init__(self, socket):
        """
        Buffer constructor, it needs a socket!
        :param socket: The input or output socket
        """
        self.socket = socket
        self.buffer = b''

    def get_bytes(self, n_bytes: int = 1024):
        """
        Read exactly n bytes from the buffered socket.
        Return remaining buffer if <n bytes remain and socket closes.
        :param n_bytes: bytes to read each iteration
        :return: n_bytes bytes
        """
        while len(self.buffer) < n_bytes:

            data = self.socket.recv(n_bytes)

            if not data:

                data = self.buffer

                self.buffer = b''

                return data

            self.buffer += data

        data, self.buffer = self.buffer[:n_bytes], self.buffer[n_bytes:]
        return data

    def put_bytes(self, data: bytes):
        """
        It sends the bytes toward the destination host
        :param data: bytes to send
        :return:
        """
        self.socket.sendall(data)

    def get_utf8(self):
        """
        Read a null-terminated UTF8 data string and decode it.
        Return an empty string if the socket closes before receiving a null.
        :return: utf8 data decoded (as a string)
        """

        while b'\x00' not in self.buffer:

            data = self.socket.recv(1024)

            if not data:
                return ''

            self.buffer += data

        data, _, self.buffer = self.buffer.partition(b'\x00')

        return data.decode()

    def put_utf8(self, string: str):
        """
        It sends strings
        :param string: The string to send toward the destination
        :return:
        """

        if '\x00' in string:
            raise ValueError('string contains delimiter(null)')

        self.socket.sendall(string.encode() + b'\x00')
