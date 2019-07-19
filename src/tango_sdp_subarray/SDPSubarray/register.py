# coding: utf-8
"""Register the SDPSubarray device(s) with the Tango Db."""
import argparse
from tango import Database, DbDevInfo


def is_subarray_device_registered(server_name: str):
    """Check if the SDPSubarray device is already registered with the db.

    :param server_name: Name of the Tango device server.
    """
    return server_name in list(Database().get_server_list(server_name))


def registered_subarray_devices(server_name: str, class_name: str) -> list:
    """Get list of registered subarray devices.

    :param server_name: Name of the Tango device server.
    :param class_name: Name of the Tango device class.
    :return: List of device names
    """
    return list(Database().get_device_name(server_name, class_name))


def list_subarray_devices(server_name: str, class_name: str):
    """List the subarray devices registered.

    :param server_name: Name of the Tango device server.
    :param class_name: Name of the Tango device class.
    """
    devices = registered_subarray_devices(server_name, class_name)
    print('- No. registered devices: {}'.format(len(devices)))


def delete_server(server_name: str):
    """Delete the specified device server.

    :param server_name: Name of the Tango device server to delete.
    """
    tango_db = Database()
    if is_subarray_device_registered(server_name):
        print('- Removing device server: {}'.format(server_name))
        tango_db.delete_server(server_name)


def register_subarray_devices(server_name: str, class_name: str,
                              num_devices: int):
    """Register subarray devices.

    :param server_name: Name of a Tango device server.
    :param class_name: Class name of the Tango device server.
    :param num_devices: Number of Subarray devices to create.
    """
    tango_db = Database()
    device_info = DbDevInfo()

    # pylint: disable=protected-access
    device_info._class = class_name
    device_info.server = server_name

    for index in range(num_devices):
        device_info.name = 'mid_sdp/elt/subarray_{:02d}'.format(index)
        print("- Registering device: {}, class: {}, server: {}"
              .format(device_info.name, class_name, server_name))
        tango_db.add_device(device_info)


if __name__ == '__main__':
    PARSER = argparse.ArgumentParser(
        description='SDPSubarray device registration')
    PARSER.add_argument('--delete', action='store_true',
                        help='Delete the device server and exit')
    PARSER.add_argument('num_devices', metavar='N', type=int,
                        default=16, nargs='?',
                        help='Number of devices to start.')
    ARGS = PARSER.parse_args()
    SERVER = 'SDPSubarray/1'
    CLASS = 'SDPSubarray'

    if ARGS.delete:
        delete_server(SERVER)
    else:
        delete_server(SERVER)
        register_subarray_devices(SERVER, CLASS, ARGS.num_devices)
