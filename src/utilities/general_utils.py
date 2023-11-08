import json
import random
import string
import matplotlib.pyplot as plt
from src.utilities.config import NODES_MAPPING, OUTDOOR_CONFIG_PATH


def random_alphanumerical_string(char_num: int = 16):
    """
    Random alphanumerical string
    :param char_num:
    :return:
    """

    return ''.join(random.choices(string.ascii_letters + string.digits, k=char_num))


def random_port(lb: int = 5000, ub: int = 6000):
    """

    :param lb:
    :param ub:
    :return:
    """

    return random.randint(lb, ub)


def plot_config(d: dict):

    ax = plt.gca()

    ax.axis('scaled')

    ax.set_xlim(1, 50)
    ax.set_ylim(1, 50)

    coords = d["depot"][0]["coords"]

    x, y = coords[0], coords[1]

    circle = plt.Circle(xy=(x, y), radius=4, fc="blue")

    plt.text(x - 3, y + 4, "DEPOT")

    ax.add_patch(circle)

    for drone, drone_dict in d["drones"].items():

        coords = drone_dict["coords"]

        x, y = coords[0], coords[1]

        circle = plt.Circle(xy=(x, y), radius=1, fc="red")

        plt.text(x + 0.7, y + 0.7, f'{drone}')

        ax.add_patch(circle)


    plt.show()


def get_config(d: dict):

    senders = [(str(v["drone"]), str(v["dataset"])) for k, v in d["targets"].items() if v["drone"] is not None]

    link_list = []

    receiver = str(d["depot"][0]["id"])

    for k, v in d["drones"].items():

        next_hop = v["next_hop"]

        link_list.append((k, str(next_hop)))

    configs = {}

    print(senders)
    print(receiver)
    print(link_list)

    for sender, quality in senders:

        current_node = sender

        restart = True

        while restart:

            for link in link_list:

                if link[0] == current_node:

                    if f"conn_{sender}" not in configs:

                        configs[f"conn_{sender}"] = {
                            "nodes": {},
                            "quality": None
                        }

                    configs[f"conn_{sender}"]["nodes"][current_node] = ""

                    current_node = link[1]

                    if current_node == receiver:

                        print(current_node)

                        configs[f"conn_{sender}"]["nodes"][current_node] = ""

                        configs[f"conn_{sender}"]["quality"] = quality

                        restart = False

                        break

    res = {}

    print(configs)

    for k, v in configs.items():

        res[k] = {
            "nodes": {},
            "quality": None
        }

        res[k]["quality"] = v["quality"]

        for i, (ip, role) in enumerate(v["nodes"].items()):

            if i == 0:

                res[k]["nodes"][NODES_MAPPING[ip]] = "SENDER"

            elif i == len(v["nodes"]) - 1:

                res[k]["nodes"][NODES_MAPPING[ip]] = "RECEIVER"

            else:

                res[k]["nodes"][NODES_MAPPING[ip]] = "RELAY"


    return res

