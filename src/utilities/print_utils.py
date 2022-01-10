def print_dict(d: dict):
    """

    :param d:
    :return:
    """

    string = ""

    for key, value in d.items():
        string += f"{key}    |    {value}\n"

    print(string)


def bytes_converter(b: int, unit: str = "MB"):
    """

    :param b:
    :param unit:
    :return:
    """
    kb = float(1024)
    mb = float(kb ** 2)

    if unit == "KB":
        return float("{0:.3f}".format(b / kb))
    elif unit == "MB":
        return float("{0:.3f}".format(b / mb))



