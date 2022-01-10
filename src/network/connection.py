import threading
import time

class Connection:
    """
    The Connection object contains the information about a give connection
    A connection is composed by many nodes, and it must have 1 sender, 1 receiver and
    from 0 to many relay.
    """

    def __init__(self, nodes_roles: dict, port: int, connection_id):

        self.connection_id = connection_id  # d  ip -> role
        self.nodes_roles = nodes_roles  # d ip -> name
        self.nodes_name = {ip: "default" for ip, _ in nodes_roles.items()}
        self.nodes_status = {ip: "DOWN" for ip, _ in nodes_roles.items()} # d ip -> one among ( DOWN, SETUP, ACTIVE, IDLE, CLOSE)

        self.nodes_buffers = {}
        self.controller_buffers = {}
        self.nodes_path = {}
        self.nodes_service_ports = {}

        self.connection_status = "DOWN"  # it can be DOWN, SETUP, ACTIVE or CLOSE
        self.port_used = port

        self.status_updater = None  # thread pool that update the node status
        self.lock = threading.Lock()

    def __len__(self):
        """
        It returns the number of the nodes in the connection
        :return:
        """
        return len(self.nodes_roles)

    def get_nodes_status(self, names: bool = False):
        """
        it returns a the nodes status in a given connection as a string

        :param names: if true uses the names assigned to the nodes
        :return: nodes status as a formatted string
        """


        status = f"***********CONNECTION-{self.connection_id}-NODE STATUS***********\n"

        if names:

            for ip, st in self.nodes_status.items():
                node_name = self.nodes_name[ip]
                node_role = self.nodes_roles[ip]
                status += f"| {node_name} | {ip} | {st} | {node_role} |\n"

        else:

            for ip, st in self.nodes_status.items():
                node_role = self.nodes_roles[ip]
                status += f"| {ip} | {st} | {node_role} |\n"

        status += "*****************************************************"


        return status


    def set_node_status(self, node: str, status: str):
        """
        Sets the node status for a given node
        :param node: The node ip as a string
        :param status: The status as a string ( DOWN, SETUP, ACTIVE, IDLE, CLOSE)
        :return:
        """

        self.nodes_status[node] = status

    def close_connection(self):
        """
        Close the connection socket
        :return:
        """

        if self.nodes_buffers:
            for ip, buf in self.nodes_buffers.items():
                buf.socket.close()

        if self.controller_buffers:
            for ip, buf in self.controller_buffers.items():
                buf.socket.close()


    def connection_kernel(self):
        """
        The connection_kernel update the connection state launching one thread from each node
        in the connection. Each time the node change its status, it send an update to this
        listen_thread_pool

        :return:
        """

        while True:

            time.sleep(0.2)

            if all([True if status == "ACTIVE" else False for status in self.nodes_status.values()]):
                self.connection_status = "ACTIVE"

            elif all([True if status == "IDLE" else False for status in self.nodes_status.values()]):
                self.connection_status = "IDLE"

            elif all([True if status == "CLOSE" or status == "IDLE" else False for status in self.nodes_status.values()]):
                self.connection_status = "CLOSE"
                break

            else:
                continue

    def update_node_status(self, ip: int):
        """
        update continuously the current node state until the connection is closed
        :param ip: ip of the node to check
        :return:
        """
        while True:

            _, status = self.nodes_buffers[ip].get_utf8().split("|")

            with self.lock:

                self.nodes_status[ip] = status

            if status != '':

                print(f"{ip} {self.connection_id} status {status}")

                self.controller_buffers[ip].put_utf8("OK")

            if status == "CLOSE":

                break
