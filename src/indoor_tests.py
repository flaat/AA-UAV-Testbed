import json
import time
from threading import Thread
from src.roles.controller import Controller

if __name__ == "__main__":
    """
    The indoor tests do not have heterogeneous quality, all the connections in a test have the same quality.
    
    
    """

    tests_stats = {}

    UPPER_BOUND_QUALITY = 100
    LOWER_BOUND_QUALITY = 0

    CONTROLLER_IP = "169.254.1.1"

    QUALITY_LIST = [i for i in range(LOWER_BOUND_QUALITY, UPPER_BOUND_QUALITY)]

    with open("/home/pi/Desktop/Thesis/indoor_network_config/long_chain.json", "r") as f:

        CONFIG = json.load(f)

    for test_name, connections in CONFIG.items():

        for quality in QUALITY_LIST:

            print(f"Executing {test_name} with quality {quality}...")

            conn_number = sum([len(v) for k, v in connections.items()])

            controller = Controller(controller_ip=CONTROLLER_IP)

            stats_thread = Thread(target=controller.get_stats, args=())

            stats_thread.start()

            for conn_name, conn_dict in connections.items():

                controller.init_connection(nodes_roles=conn_dict["nodes"], file_to_send_path=f"/home/pi/Desktop/dataset/{quality}/",
                                           save_folder=f"/home/pi/Desktop/received/{test_name}_{quality}_rec/")

            while True:

                if all(True if conn.connection_status == "CLOSE" else False for id, conn in
                       controller.connections.items()):
                    break

                time.sleep(1)

                print(controller.get_connections_status(), end='\r')

            stats_thread.join()

            tests_stats[str(f"{test_name}_{quality}")] = controller.connections_stats

            with open("/home/pi/Desktop/Thesis/tests/results/results.json", "w") as f:

                json.dump(tests_stats, f)

            controller.close()

