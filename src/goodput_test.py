import time
from threading import Thread

from src.roles.controller import Controller

if __name__ == "__main__":

    QUALITY = 80
    CONNECTIONS = 1
    SYNC = True

    FILE_TO_SEND_PATH = f"/home/pi/Desktop/dataset/{QUALITY}/"

    SAVE_FOLDER = f"/home/pi/Desktop/received/GOODPUT_{QUALITY}_rec/"

    IP_CONTROLLER = "169.254.1.1"
    IP_SENDER = "169.254.1.2"
    IP_RECEIVER = "169.254.1.1"

    NODES_ROLES = {IP_SENDER: "SENDER",
                   IP_RECEIVER: "RECEIVER"
                   }

    controller = Controller(controller_ip=IP_CONTROLLER)

    stats_thread = Thread(target=controller.get_stats, args=())

    stats_thread.start()


    controller.init_connection(nodes_roles=NODES_ROLES, file_to_send_path=FILE_TO_SEND_PATH, save_folder=SAVE_FOLDER)

    while True:

        if all(True if conn.connection_status == "CLOSE" else False for _, conn in controller.connections.items()):
            break

        time.sleep(1)

        print(controller.get_connections_status(), end='\r')

    stats_thread.join()

    bytes_transmitted, start_time, end_time = 0, 0, 0

    for idf, d in controller.connections_stats.items():

        ip, conn_id = idf.split("|")

        if ip == IP_SENDER:

            start_time = d["transmission_start_time"]

        else:

            bytes_transmitted = d["bytes_transmitted"]
            end_time = d["transmission_end_time"]

    print(f"GOODPUT BETWEEN {IP_SENDER} - {IP_RECEIVER}: {bytes_transmitted/(end_time-start_time)}")
