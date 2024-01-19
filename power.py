from subprocess import run
import usb.core
import usb.backend.libusb1 as libusb1
import usb.backend.libusb0 as libusb0
from usb.legacy import TYPE_CLASS, RECIP_OTHER, REQ_SET_FEATURE, REQ_CLEAR_FEATURE
import time
from argparse import ArgumentParser, ArgumentTypeError
import re

PORT_FEAT_POWER = 8
RT_PORT = TYPE_CLASS | RECIP_OTHER


class RegexArgValidator(object):

    def __init__(self, pattern):
        self._pattern = re.compile(pattern)

    def __call__(self, value):
        if not self._pattern.fullmatch(value):
            raise ArgumentTypeError(
                "Argument has to match '{}'".format(self._pattern.pattern))
        return value


def main():
    def usb0_dev(dev):
        return usb.core.find(bus=dev.bus, address=dev.address, backend=libusb0.get_backend())

    id_regex = "[0-9a-f]{4}:[0-9a-f]{4}"

    parser = ArgumentParser(
        description="Powers off/on usb devices by id",
    )
    parser.add_argument('action', choices=['cycle', 'off', 'on'],
                        help='action to perform: power-cycle, off or on')
    parser.add_argument("id", type=RegexArgValidator(id_regex),
                        help="usb device id in the form 'idVendor:idProduct' where both ids are 4-digit hex numbers")
    parser.add_argument("-m", "--mod", type=str, nargs="*",
                        help="kernel module(s) to unload before the action, and to load back after the action")

    args = parser.parse_args()

    args.mod = args.mod or []

    id_vendor, id_product = (int(_id, base=16) for _id in args.id.split(":"))

    # find our device(s)
    devs = usb.core.find(find_all=True, idVendor=id_vendor, idProduct=id_product, backend=libusb1.get_backend())
    devs = [dev for dev in devs if dev.parent]  # leave only devices with parents

    if devs:
        devs.sort(key=lambda dev: (dev.parent.bus, dev.parent.address, dev.port_number))

        for module in args.mod:
            run(f"modprobe -r {module}".split(), check=True)

        if args.action in ["off", "cycle"]:
            for dev in devs:
                # power off
                usb0_dev(dev.parent).ctrl_transfer(RT_PORT, REQ_CLEAR_FEATURE, PORT_FEAT_POWER, dev.port_number)

        if args.action == "cycle":
            time.sleep(0.1)

        if args.action in ["on", "cycle"]:
            for dev in devs:
                # power on
                usb0_dev(dev.parent).ctrl_transfer(RT_PORT, REQ_SET_FEATURE, PORT_FEAT_POWER, dev.port_number)

        for module in args.mod:
            run(f"modprobe {module}".split(), check=True)


if __name__ == "__main__":
    main()
