import subprocess
from src.roles.node_handler import NodeHandler
import socket
from pathlib import Path
import traceback
from src.network.buffer import Buffer
import time


class Receiver(NodeHandler):
    """
    Class that handles the receiver
    """

    def __init__(self, node_ip: str, node_name: str = "Default", log_level: int = 0):
        """

        :param node_ip: The ip of the host to set up the socket
        :param node_name: The optional name
        :param log_level: The log level chosen to display different infos
        """
        super(Receiver, self).__init__(node_ip, node_name, log_level=log_level)
        self.in_socket = None
        self.buffer = None
        self.info_dict["node_type"] = "RECEIVER"

    def start_node(self, max_connections: int = 5):
        """
        This method starts the Receiver node setting up the socket and binding it
        with the chosen ip and port
        :param max_connections: Maximum number of connections
        :return:
        """

        if self.log_level == 1:

            print(f"Starting node {self.node_ip} --> {self.node_name}")

        try:

            # declaring and starting the socket

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
        This method closes all the sockets
        :return:
        """
        if self.log_level == 1:
            print(f"Stopping node {self.node_ip} --> {self.node_name}")

        try:

            # closing the buffer

            self.buffer = None

            # closing the socket

            #self.in_socket.close()

            while True:

                self.service_out_buffer.put_utf8(f"{self.node_ip}|CLOSE")

                if self.service_in_buffer.get_utf8() == "OK":

                    break


            self.service_out_buffer = None

            self.service_out_socket.close()

            self.service_in_buffer = None

            self.service_in_socket.close()

        except Exception as e:

            print(f"In node {self.node_name} --> {self.node_ip} occurred:\n {e}")

            print(f" Traceback:\n {traceback.format_exc()}")


    def wait_and_receive_file(self, data_path: str, chunk: int):
        """
        This method has the responsibility to handle the stream of data that comes from the network

        :param data_path: path where we can save the images
        :param chunk: max chunk size
        :return:
        """

        Path(data_path).mkdir(parents=True, exist_ok=True)

        if self.log_level == 1:
            print(f"Node is waiting for data {self.node_ip} --> {self.node_name}\n")

        if self.in_socket is None:
            raise Exception("You need to set up an input socket! call obj.start_node()")

        try:

            sender_socket, sender_address = self.in_socket.accept()

            self.buffer = Buffer(sender_socket)

            self.service_out_buffer.put_utf8(f"{self.node_ip}|ACTIVE")

            while True:

                if self.service_in_buffer.get_utf8() == "OK":

                    break

            print(f"{self.node_ip}  ACTIVE OK ack")

            file_dict = {}

            if self.log_level == 1:
                print(f"Node is receiving data {self.node_ip} --> {self.node_name} from {sender_address}")

            first = True

            start_time = 0

            while True:

                file_name = self.buffer.get_utf8()

                if first:

                    start_time = time.time()

                    first = False

                if not file_name:
                    break

                file_size = int(self.buffer.get_utf8())

                if not file_size:
                    break

                with open(data_path+"/"+file_name, "wb") as f:

                    remaining = file_size

                    # updating bytes transmitted
                    self.info_dict["bytes_transmitted"] += file_size

                    while remaining:

                        chunk_size = chunk if remaining >= chunk else remaining

                        chunk = self.buffer.get_bytes(chunk_size)

                        if not chunk:
                            break

                        f.write(chunk)

                        remaining -= len(chunk)

                    file_dict[file_name] = time.time()

                    if self.log_level == 1:

                        if remaining:
                            print(f"{file_name} incomplete, missing {remaining} bytes")
                        else:
                            print(f"{file_name} received successfully.")

                self.info_dict["files_transmitted"] += 1

            end_time = time.time()

            self.info_dict["node_total_traverse_time"] = end_time - start_time

            self.info_dict["transmission_start_time"] = start_time

            self.info_dict["transmission_end_time"] = end_time

            self.info_dict["file_dict"] = file_dict

            self.service_out_buffer.put_utf8(f"{self.node_ip}|IDLE")

            while True:

                if self.service_in_buffer.get_utf8() == "OK":

                    break


        except Exception as e:
            print(f"In node {self.node_name} --> {self.node_ip} {data_path} occurred:\n {e}")
            print(f" Traceback:\n {traceback.format_exc()}")
