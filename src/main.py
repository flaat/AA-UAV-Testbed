import sys

from src.roles.sender import Sender
from src.roles.receiver import Receiver
from src.roles.relay import Relay
from src.utilities.config import CONTROLLER_IP

if __name__ == "__main__":

    mode = sys.argv[1]

    if mode == "SENDER":
        """
        Sender syntax python3 main.py <mode> <host_ip> <next_hop_ip> <file_to_send>
        """
        host_ip = sys.argv[2]
        data_to_send_path = sys.argv[3]

        sender_drone = Sender(node_ip=host_ip, log_level=1)
        print("Sender init...")
        sender_drone.node_bootstrap(controller_ip=CONTROLLER_IP)

        sender_drone.start_node()

        sender_drone.send_data(data_path=data_to_send_path)

        sender_drone.stop_node()

        sender_drone.send_stats()

    elif mode == "RECEIVER":
        """
        Receiver syntax python3 main.py <mode> <host_ip> <folder_to_save>
        """
        host_ip = sys.argv[2]
        data_path = sys.argv[3]

        receiver_drone = Receiver(node_ip=host_ip, node_name="Access_Point", log_level=1)
        print("Receiver init...")

        receiver_drone.node_bootstrap(controller_ip=CONTROLLER_IP)

        receiver_drone.start_node()

        receiver_drone.wait_and_receive_file(data_path=data_path)

        receiver_drone.stop_node()

        receiver_drone.send_stats()


    elif mode == "RELAY":
        """
        Relay syntax python3 main.py <mode> <host_ip> <next_hop_ip> 
        """
        host_ip = sys.argv[2]

        relay_drone = Relay(node_ip=host_ip, log_level=1)
        print("Relay init...")

        relay_drone.node_bootstrap(controller_ip=CONTROLLER_IP)

        relay_drone.start_node()

        relay_drone.relay_data()

        relay_drone.stop_node()

        relay_drone.send_stats()



    else:
        raise Exception("You should choose between: RELAY, RECEIVER or SENDER")
