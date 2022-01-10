import json
from abc import ABC, abstractmethod
import socket
import traceback
from src.network.buffer import Buffer
from src.utilities import config
from src.utilities.general_utils import random_port


class NodeHandler(ABC):
    """
    Super class for receiver, relay and sender
    """

    def __init__(self, node_ip: str, node_name: str = "Default",
                 buffer_size: int = 4096, log_level: int = 0):
        """

        :param node_ip: current node ip
        :param node_name: current node name
        :param buffer_size: buffer size
        :param log_level: 0 is off, 1 is info only
        """

        # Service variables and parameters
        self.service_out_socket = socket.socket()
        self.service_in_socket = socket.socket()
        self.stats_socket = None
        self.stats_buffer = None
        self.service_out_buffer = None
        self.service_in_buffer = None
        self.service_in_port = None
        self.service_out_port = 4000

        # Connection variables and parameters
        self.next_hop = None
        self.connection_port = None
        self.node_ip = node_ip
        self.buffer_size = buffer_size
        self.node_name = node_name
        self.connection_id = None

        # infos and debug
        self.log_level = log_level

        # stats about the node
        self.info_dict = {"node_type": "",
                           "bytes_transmitted": 0,
                           "files_transmitted": 0,
                           "node_total_traverse_time": 0,
                           "transmission_start_time": 0,
                           "transmission_end_time": 0,
                           "total_transmission_time": 0,
                           "file_dict": {},
                           "node_name": node_name,
                           "node_ip": node_ip}

    def node_bootstrap(self, controller_ip: str):
        """
        Permette di creare la connessione di servizio dove vengono scambiate le informazioni

        :param controller_ip:
        :return:
        """

        try:

            while True:
                self.service_in_port = random_port()
                try:
                    # service socket
                    self.service_in_socket.bind((self.node_ip, self.service_in_port))
                    break
                except Exception as e:
                    print(f"In node {self.node_name} --> {self.node_ip} occurred:\n {e}")
                    print(f" Traceback:\n {traceback.format_exc()}")
                    print(" Reconnection...")
                    self.service_in_port = random_port()


            print(f"{self.node_ip} is connecting to the controller ")

            self.service_out_socket.connect((controller_ip, self.service_out_port))

            self.service_out_buffer = Buffer(self.service_out_socket)

            self.service_in_socket.listen(100)

            self.service_out_buffer.put_utf8(f"{self.service_in_port}|{self.node_ip}|SETUP")

            controller_socket, _ = self.service_in_socket.accept()

            self.service_in_buffer = Buffer(controller_socket)

            while True:

                if self.service_in_buffer.get_utf8() == "OK":

                    break


            print(f"{self.node_ip} sent the SETUP states ")

            print(f"{self.node_ip} is receiving the controller socket ")

            self.connection_port = int(self.service_in_buffer.get_utf8())

            self.next_hop = self.service_in_buffer.get_utf8()

            self.connection_id = self.service_in_buffer.get_utf8()

            print(f"{self.node_ip} has received the next hop and next port: {self.next_hop}:{self.connection_port}")

        except Exception as e:

            print(f"In node {self.node_name} --> {self.node_ip} occurred:\n {e}")

            print(f" Traceback:\n {traceback.format_exc()}")

            with open(config.LOGS_FOLDER_PATH, 'w') as f:

                f.write(traceback.format_exc())


    def send_stats(self):

        self.stats_socket = socket.socket()

        self.stats_socket.connect((config.STATS_SERVER_IP, 65000))

        print(f"Connected to controller for stats {self.node_ip}")

        self.stats_buffer = Buffer(self.stats_socket)

        dict_str = json.dumps(self.info_dict)

        self.stats_buffer.put_utf8(dict_str)

        self.stats_buffer.put_utf8(self.connection_id + "|" + self.node_ip)


    @abstractmethod
    def start_node(self):
        pass


    @abstractmethod
    def stop_node(self):
        pass
