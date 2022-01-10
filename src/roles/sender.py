from abc import ABC
import traceback
from src.roles.node_handler import NodeHandler
from src.network.buffer import Buffer
import socket
import os
import time


class Sender(NodeHandler, ABC):

    def __init__(self, node_ip: str, node_name: str = "Default", log_level: int = 0):
        """
        Sender constructor
        :param node_ip: Current node ip
        :param node_name: optional node name
        """

        super(Sender, self).__init__(node_ip, node_name, log_level=log_level)
        self.out_socket = None
        self.buffer = None
        self.info_dict["node_type"] = "SENDER"

    def start_node(self, max_connections: int = 5):
        """
        This method starts the Sender node setting up the socket and binding it
        with the chosen ip and port
        :param max_connections: Maximum number of connections
        :return:
        """

        if self.log_level == 1:
            print(f"Starting node {self.node_ip} --> {self.node_name}")

        try:

            # declaring and starting the socket

            self.out_socket = socket.socket()

            self.buffer = Buffer(socket=self.out_socket)

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

        if self.log_level == 1:
            print(f"Stopping node {self.node_ip} --> {self.node_name}")

        try:

            # Removing the buffer

            self.buffer = None

            # closing the socket

            #self.out_socket.close()

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

    def send_data(self, data_path: str):
        """
        This method sends a single file or multiple files in a directory specified
        by data_path.
        :param data_path: folder from where we read the files to send.
        :return:
        """

        if self.log_level == 1:
            print(f"Node is sending data {self.node_ip} --> {self.node_name}\n")

        if self.out_socket is None or self.buffer is None:
            raise Exception("You need to set up an input socket and a buffer! call obj.start_node()")

        try:

            while True:

                status = self.buffer.socket.connect_ex((self.next_hop, self.connection_port))

                if status == 0:
                    print(f"{self.node_ip} is connected to the next hop")
                    break

                time.sleep(0.1)

            # if multiple file in a folder
            if os.path.isdir(data_path):

                file_list = os.listdir(data_path)

                path = data_path

            # if single file
            else:

                file_name = os.path.basename(data_path)

                file_list = [file_name]

                path = data_path.replace(file_name, "")

            self.info_dict["files_transmitted"] = len(file_list)

            self.service_out_buffer.put_utf8(f"{self.node_ip}|ACTIVE")

            print(f"{self.node_ip} the node is active")

            while True:

                if self.service_in_buffer.get_utf8() == "OK":

                    break

            print(f"{self.node_ip}  ACTIVE OK ack")

            file_dict = {}

            start_time = time.time()

            for filename in file_list:

                filesize = os.path.getsize(path + filename)

                file_dict[filename] = time.time()

                self.info_dict["bytes_transmitted"] += filesize

                self.buffer.put_utf8(filename)

                self.buffer.put_utf8(str(filesize))

                with open(path + filename, "rb") as f:

                    bytes_read = f.read()

                    self.buffer.put_bytes(bytes_read)

            end_time = time.time()

            self.info_dict["node_total_traverse_time"] = end_time - start_time

            self.info_dict["transmission_start_time"] = start_time

            self.info_dict["transmission_end_time"] = end_time

            self.info_dict["file_dict"] = file_dict

            self.service_out_buffer.put_utf8(f"{self.node_ip}|IDLE")

            while True:

                if self.service_in_buffer.get_utf8() == "OK":

                    break

            print(f"{self.node_ip} transmission completed")

        except Exception as e:

            print(f"In node {self.node_name} --> {self.node_ip} occurred:\n {e}")
            print(f" Traceback:\n {traceback.format_exc()}")

