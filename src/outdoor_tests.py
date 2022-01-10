from src.utilities import config
import json
import time
import os
from threading import Thread
from src.roles.controller import Controller
from utilities.general_utils import get_config, plot_config

if __name__ == "__main__":

    tests_stats = {}

    print("REMEMBER TO SYNC THE NODES!!!")

    TESTS_PATH = config.OUTDOOR_CONFIG_PATH

    config_list = []

    tests_names = os.listdir(TESTS_PATH)

    for TEST_CONFIG in tests_names:

        with open(TESTS_PATH + TEST_CONFIG, "r") as f:

            CONFIG = json.load(f)

            config_list.append(get_config(CONFIG))

            plot_config(CONFIG)

    for i in range(0, config.TEST_REP):

        for connection_dict, TEST_CONFIG in zip(config_list, tests_names):

            total_nodes = sum([len(v["nodes"]) for k, v in connection_dict.items()])

            controller = Controller(controller_ip=config.CONTROLLER_IP, total_nodes=total_nodes)

            stats_thread = Thread(target=controller.get_stats, args=())

            stats_thread.start()

            for test_name, connections in connection_dict.items():

                print(f"Executing {test_name}...")

                nodes = connections["nodes"]

                quality = connections["quality"]

                file_to_send_path = f"{config.FILES_TO_SEND_PATH}/{quality}/"

                save_path = f"{config.RECEIVED_DIRECTORY}/{test_name}_{quality}_rec/"

                controller.init_connection(nodes_roles=nodes, file_to_send_path=file_to_send_path, save_path=save_path)

            while True:

                if all(True if conn.connection_status == "CLOSE" else False for id, conn in
                       controller.connections.items()):
                    break

                time.sleep(1)

                print(controller.get_connections_status(), end='\r')

            stats_thread.join()

            with open(f"{config.RESULTS_FOLDER_PATH}/res_NUMBER_{i}_{TEST_CONFIG}", "w") as f:

                json.dump(controller.connections_stats, f)

            controller.close()
