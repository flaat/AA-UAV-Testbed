import os


# -------------------------------PATHS FROM SRC---------------------------------------------
SRC_BASE_PATH = os.getcwd()   # .../TaskMAS_test_framework/src
PACKAGE_PATH = os.path.split(os.getcwd())[0]  # .../TaskMAS_test_framework
NETWORK_CONFIGS = os.path.join(SRC_BASE_PATH, "network_configs")
OUTDOOR_CONFIG_PATH = os.path.join(NETWORK_CONFIGS, "outdoor_network_config")
DATA_PATH = os.path.join(PACKAGE_PATH, "data")
LOGS_FOLDER_PATH = os.path.join(DATA_PATH, "logs")
RESULTS_FOLDER_PATH = os.path.join(DATA_PATH, "results")

# -------------------------------THIS SHOULD BE PERSONALIZED---------------------------------
# Set the parameters to match you network configuration

# 1) NETWORK CONFIG
CONTROLLER_IP = "169.254.1.1"
STATS_SERVER_IP = "169.254.1.1"
NODES_MAPPING = {
    "0": "169.254.1.2",
    "1": "169.254.1.5",
    "2": "169.254.1.3",
    "3": "169.254.1.7",
    "4": "169.254.1.1"
}
# 2) FILE CONFIG
FILES_TO_SEND_PATH = ""
RECEIVED_DIRECTORY = ""
# 3) TEST CONFIG
TEST_REP = 10
# 4) DEVICE PACKAGES PATH
DEVICE_PACKAGE_PATH = ""  # package path used in the remote devices

if __name__ == "__main__":

    print(OUTDOOR_CONFIG_PATH)
