from src.roles.node_handler import NodeHandler
from src.network.buffer import Buffer
import socket
import traceback
import time
import subprocess


class Relay(NodeHandler):
    """
    The relay class menages the relay nodes.
    A relay node is used as a bridge to retransmit data. Doing so it is possible to extend the transmission
    range.
    ******************NETWORK******************
    The relay has:
        1) buffer:
            1.1) in_buffer, for hop_before -> relay IMPORTANT: the in buffer is initialized with the socket
                                                                received from the hop_before!
            1.2) out_buffer, for relay -> next_hop
            1.3) service_in_buffer, for controller -> relay
            1.4) service_out_buffer, for relay -> controller
        2) socket:
            2.1) in_socket, to listen for connection from hop_before
            2.2) out_socket, for relay -> next_hop
            2.1) service_out_socket, for relay -> controller
            2.2) service_in_socket, for controller -> relay
    """

    def __init__(self, node_ip: str, node_name: str = "Default", log_level: int = 0):
        """
        Relay constructor
        :param node_ip: current node ip
        :param node_name: optional node name
        """

        super(Relay, self).__init__(node_ip=node_ip, node_name=node_name, log_level=log_level)

        self.out_socket = None
        self.in_socket = None
        self.in_buffer = None
        self.out_buffer = None
        self.info_dict["node_type"] = "RELAY"

    def start_node(self, max_connections: int = 5):
        """
        This method starts the Sender node setting up the socket and binding it
        with the chosen ip and port
        :param max_connections: Maximum number of connections
        :return:
        """

        try:

            # declaring and starting the input and output socket
            # In the relay class we need to set up the output socket with the
            # output buffer here. The input buffer instead need the sender socket
            # to be initialized. That socket is received when a node starts to send
            # information towards this relay as a return value from the socket.accept() method

            self.out_socket = socket.socket()

            while True:

                status = self.out_socket.connect_ex((self.next_hop, self.connection_port))

                if status == 0:
                    break
                time.sleep(0.5)

            self.out_buffer = Buffer(socket=self.out_socket)

            self.in_socket = socket.socket()

            self.in_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            while True:

                try:

                    self.in_socket.bind((self.node_ip, self.connection_port))

                    break

                except Exception as e:

                    print(f"{self.node_ip} it can't bind the ip:port to the host waiting 2 secs...")
                    command = f"fuser {self.connection_port}/tcp -k"
                    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
                    process.communicate()
                    time.sleep(2)

            print(f" {self.node_ip}:{self.connection_port}")

            self.in_socket.listen(max_connections)

            self.service_out_buffer.put_utf8(f"{self.node_ip}|IDLE")

            while True:

                if self.service_in_buffer.get_utf8() == "OK":

                    break

        except Exception as e:
            print(f"In node {self.node_name} --> {self.node_ip} occurred:\n {e}")
            print(f" Traceback:\n {traceback.format_exc()}")

    def stop_node(self):
        """
        This method closes the socket
        :return:
        """
        try:

            # Removing the buffer

            self.in_buffer = None

            # closing the socket

            #self.in_socket.close()

            # Removing the buffer

            self.out_buffer = None

            # closing the socket

            #self.out_socket.close()

            while True:

                self.service_out_buffer.put_utf8(f"{self.node_ip}|CLOSE")

                if self.service_in_buffer.get_utf8() == "OK":

                    break

                time.sleep(0.5)

            self.service_out_buffer = None

            self.service_out_socket.close()

            self.service_in_buffer = None

            self.service_in_socket.close()

        except Exception as e:
            print(f"In node {self.node_name} --> {self.node_ip} occurred:\n {e}")
            print(f" Traceback:\n {traceback.format_exc()}")

    def relay_data(self, chunk: int):
        """
        :param chunk: max chunk size
        :return:
        """

        if self.log_level == 1:
            print(f"Relay is waiting for data {self.node_ip} --> {self.node_name}")

        if self.in_socket is None:
            raise Exception("You need to set up an input socket! call obj.start_node()")

        try:

            sender_socket, sender_address = self.in_socket.accept()

            self.service_out_buffer.put_utf8(f"{self.node_ip}|ACTIVE")

            while True:

                if self.service_in_buffer.get_utf8() == "OK":

                    break

            print(f"{self.node_ip}  ACTIVE OK ack")

            self.in_buffer = Buffer(sender_socket)

            file_dict = {}

            if self.log_level == 1:

                print(f"Node is receiving data {self.node_ip} --> {self.node_name} from {sender_address}")

            first = True

            start_time = 0

            while True:

                # receiving file name
                file_name = self.in_buffer.get_utf8()

                if first:

                    start_time = time.time()

                    first = False


                if not file_name:
                    break

                # retransmitting file name
                self.out_buffer.put_utf8(file_name)

                # receiving file size
                file_size = int(self.in_buffer.get_utf8())

                if not file_size:
                    break

                # retransmitting file size
                self.out_buffer.put_utf8(str(file_size))

                # updating the total number of files to be transmitted
                self.info_dict["files_transmitted"] += 1

                # updating bytes transmitted
                self.info_dict["bytes_transmitted"] += file_size

                remaining = file_size

                while remaining:

                    chunk_size = chunk if remaining >= chunk else remaining

                    # reads the byte from the input buffer
                    chunk = self.in_buffer.get_bytes(chunk_size)

                    if not chunk:
                        break

                    # retransmits the bytes on the output buffer
                    self.out_buffer.put_bytes(chunk)

                    remaining -= len(chunk)

                file_dict[file_name] = time.time()


                if self.log_level == 1:

                    if remaining:
                        print(f"{file_name} incomplete, missing {remaining} bytes")
                    else:
                        print(f"{file_name} retransmitted successfully.")

            end_time = time.time()

            self.info_dict["node_total_traverse_time"] = end_time - start_time

            self.info_dict["transmission_end_time"] = end_time

            self.info_dict["transmission_start_time"] = start_time

            self.info_dict["file_dict"] = file_dict

            self.service_out_buffer.put_utf8(f"{self.node_ip}|IDLE")

            while True:

                if self.service_in_buffer.get_utf8() == "OK":
                    break


        except Exception as e:
            print(f"In node {self.node_name} --> {self.node_ip} occurred:\n {e}")
            print(f" Traceback:\n {traceback.format_exc()}")
