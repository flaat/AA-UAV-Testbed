import json
import traceback
from concurrent.futures import ThreadPoolExecutor
import time
from threading import Thread
import paramiko
from src.network.buffer import Buffer
from src.network.connection import Connection
from src.utilities.config import LOGS_FOLDER_PATH, DEVICE_PACKAGE_PATH
from src.utilities.general_utils import random_alphanumerical_string, random_port
import socket
from src.utilities.print_utils import print_dict


class Controller:


    def __init__(self, controller_ip: str, total_nodes: int):

        self.service_in_socket = socket.socket()
        self.service_out_socket = socket.socket()

        self.service_in_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.service_in_socket.bind((controller_ip, 4000))
        self.service_in_socket.listen(200)

        self.stats_socket = socket.socket()
        self.stats_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.stats_socket.bind((controller_ip, 65000))

        # d id -> connection obj
        self.connections = {}

        # d id -> thread that handles a given connection
        self.thread_dict = {}

        # d connection_id -> port (used for the images exchange)
        self.ports_dict = {}

        self.service_communication_port = 4000

        # ip and port of the controller
        self.port = None
        self.ip = controller_ip

        self.connections_stats = {}
        self.total_nodes = total_nodes

    def get_connections_status(self):
        """
        Retrieve information about the connections
        :return: the string containing the connections status
        """

        message = "#################CONNECTIONS STATUS#################\n"

        for id, conn in self.connections.items():

            message += f"Status: {conn.connection_status}\n"

            message += conn.get_nodes_status() + "\n"

        return message


    def init_connection(self, nodes_roles: dict, file_to_send_path: str, save_path: str, test: str = ""):
        """
        Starts a new connection

        :param test:
        :param save_path: Folder to save the images
        :param file_to_send_path:
        :param nodes_roles: A dictionary with ip -> role entries
        :return:
        """

        print("Init connection...")

        try:

            # Assign a new connection id
            new_connection_id = random_alphanumerical_string(char_num=8)

            # check if there is another connection with the same id

            while new_connection_id in self.connections:

                new_connection_id = random_alphanumerical_string(char_num=8)


            # Assign a new connection port
            new_connection_port = random_port(lb=5000, ub=64999)

            while new_connection_port in self.ports_dict.values():

                new_connection_port = random_port(lb=5000, ub=64999)

            # adding the connection port to the dictionary
            self.ports_dict[new_connection_id] = new_connection_port

            new_connection = Connection(nodes_roles=nodes_roles, connection_id=new_connection_id, port=new_connection_port)

            self.connections[new_connection_id] = new_connection

            ip_chain = list(nodes_roles.keys())

            roles_chain = list(nodes_roles.values())

            # d ip -> next hop
            new_connection.nodes_path = {k: v for k, v in zip(ip_chain, ip_chain[1:] + ["NULL"])}

            # Starting the nodes through ssh
            self.ssh_start_node(file_to_send_path, ip_chain, new_connection_port, roles_chain, save_path, True, test, new_connection_id)

            self.handshake_procedure(ip_chain, new_connection, new_connection_id, new_connection_port, nodes_roles)

            print("Connection READY")

        except Exception as e:

            print(f" Traceback:\n {traceback.format_exc()}")
            for c in self.connections.values():
                c.close_connection()
            self.service_in_socket.close()
            self.service_out_socket.close()

    def handshake_procedure(self, ip_chain, new_connection, new_connection_id, new_connection_port, nodes_roles):
        """
        When the node has been activated using ssh it starts the handshake procedure (node_handler in node_bootstrap).
        The procedure is as follow:
        ---------------------------------------------------------------------------------------------------------------

        NODE                                                   CONTROLLER

        1) start_up and choose a random port for service
           communication
        2) send the port, the status and
           the ip to the controller
                                                                3) accept the connection from the node and receive the
                                                                   port for the service channel, the status and the ip.
                                                                   The controller save the information in the new_connection
                                                                4) For each node, create a new socket and connect to the
                                                                   node using the port just received from that specific
                                                                   node and send to the node its next hop and the port
                                                                   used for the transmission (all the nodes in a path use
                                                                   the same port)
                                                                5) launch a thread for each node to update the status for
                                                                   each node
        6) receive the next hop and the port



        :param ip_chain:
        :param new_connection:
        :param new_connection_id:
        :param new_connection_port:
        :param nodes_roles:
        :return:
        """

        while len(ip_chain) != len(new_connection.nodes_buffers):

            # accepts and receives the socket from the node that has to be set up
            sock, addr = self.service_in_socket.accept()
            node_buffer = Buffer(sock)

            node_service_port, node_ip, status = node_buffer.get_utf8().split("|")

            new_connection.set_node_status(node=node_ip, status=status)

            new_socket = socket.socket()

            new_connection.nodes_service_ports[node_ip] = int(node_service_port)

            service_port = new_connection.nodes_service_ports[node_ip]

            new_socket.connect((node_ip, service_port))

            new_buffer = Buffer(new_socket)

            new_buffer.put_utf8("OK")

            new_connection.controller_buffers[node_ip] = new_buffer

            new_connection.nodes_buffers[node_ip] = node_buffer

        new_connection.status_updater = ThreadPoolExecutor(max_workers=len(nodes_roles.keys()))

        for ip in new_connection.nodes_path.keys():

            next_hop = new_connection.nodes_path[ip]

            new_connection.controller_buffers[ip].put_utf8(str(new_connection_port))

            new_connection.controller_buffers[ip].put_utf8(next_hop)

            new_connection.controller_buffers[ip].put_utf8(new_connection_id)

            new_connection.status_updater.submit(new_connection.update_node_status, ip=ip)

        start_time = time.time()

        while not all([True if status != "SETUP" else False for status in new_connection.nodes_status.values()]):

            if time.time() - start_time > 30:

                print(new_connection.connection_id)
                print_dict(new_connection.nodes_status)
                time.sleep(5)

            pass

        new_connection.connection_status = "SETUP"

        connection_thread_handler = Thread(target=new_connection.connection_kernel, args=())

        connection_thread_handler.start()

        self.thread_dict[new_connection_id] = connection_thread_handler

    @staticmethod
    def ssh_start_node(file_path, ip_chain, new_connection_port, roles_chain, save_path, sync, test, conn_id):
        # ssh connection
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        for ip, role, index in zip(ip_chain, roles_chain, list(range(0, len(ip_chain)))):

            while True:

                try:

                    ssh.connect(ip, username="pi", password="raspberry")

                    break

                except Exception as e:

                    time.sleep(4)

                    print(f"{ip} is not reachable")

            print(f"Starting node through ssh {ip}, {role}")

            command = f"fuser {new_connection_port}/tcp -k ; cd {DEVICE_PACKAGE_PATH} ;"

            if role == "RELAY":

                command += f"python3 -u main.py \"{role}\" {ip} > {LOGS_FOLDER_PATH}/log_{test}_{conn_id}.txt"

            elif role == "SENDER":

                command += f"python3 -u main.py \"{role}\" {ip} \"{file_path}\" > {LOGS_FOLDER_PATH}/log_{test}_{conn_id}.txt"

            elif role == "RECEIVER":

                command += f"python3 -u main.py \"{role}\" {ip} \"{save_path}\" > {LOGS_FOLDER_PATH}/log_{test}_{conn_id}.txt"

            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(command=command)

            ssh.close()


    def get_stats(self):
        """

        :return:
        """

        self.stats_socket.listen(200)

        while True:

            sender_socket, addr = self.stats_socket.accept()

            buffer = Buffer(sender_socket)

            stat_dict = buffer.get_utf8()

            conn_id, ip = buffer.get_utf8().split("|")

            if conn_id not in self.connections_stats:

                self.connections_stats[conn_id] = {}

            print(f"{conn_id} stats received from {ip}")

            self.connections_stats[conn_id][ip] = json.loads(stat_dict)

            if sum([len(v) for k, v in self.connections_stats.items()]) == self.total_nodes:

                break

        self.stats_socket.close()

        return self.connections_stats

    def close(self):

        for c in self.connections.values():
            c.close_connection()

        self.service_in_socket.close()
        self.service_out_socket.close()
        self.stats_socket.close()
