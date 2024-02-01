Usage
=====

```
usage: power.py [-h] [-m [MOD ...]] {cycle,off,on} id

Powers off/on usb devices by id

positional arguments:
  {cycle,off,on}        action to perform: power-cycle, off or on
  id                    usb device id in the form 'idVendor:idProduct', each id is a hex number from 0 to ffff, e.g., '123:abcd'

options:
  -h, --help            show this help message and exit
  -m [MOD ...], --mod [MOD ...]
                        kernel module(s) to unload before the action, and to load back after the action
```

Note the script needs to be run as root.

Motivation
===========

I wrote this python script after I accidentally discovered a workaround, using
[hub-ctrl fork](https://github.com/yy502/hub-ctrl) by Yi Yu, to make ethernet port on my
[Razer Core X Chroma](https://egpu.io/razer-core-x-review-thick-juicy/)
usable on a laptop running Arch Linux. The fix was to power off the ports, to which the ethernet controller
is (internally) connected to, then power them on again. I wanted to do this without hardcoding the hub bus/device,
which isn't possible with `hub-ctrl`, so I turned to using [pyusb](https://pypi.org/project/pyusb) to find devices
by vendor and product id, and ported the `usb_control_msg()` from `hub-ctrl` to power off/on the discovered devices.
I also noticed that power-cycling the ethernet adapter creates a new network interface called `eth0`, leaving the old
[predictably](https://www.freedesktop.org/wiki/Software/systemd/PredictableNetworkInterfaceNames/) named one hanging
dead. A workaround that helps is to unload the `ax88179_178a` kernel module before the power-cycling and then load it
back again. Hence, I added an option to do this with the same script too. Now I just run
```
python power.py cycle 0b95:1790 -m ax88179_178a
```
on system boot, and ethernet finally works.


Dependencies
============

The script has the following dependencies:

* `libusb-1.0-0`
* `libusb-0.1-4`
* `pyusb` >= `1.1.0`

It uses both `libusb1` and `libusb0` backends for two reasons:

1. `libusb0` doesn't implement the `get_parent` method that is used to find the hub, to which a device is connected to
2. In my tests, only using `libusb-0.1-4` to execute power off/on control messages yielded the desired results.
Neither `libusb1`, nor [libusb-compat](https://archlinux.org/packages/extra/x86_64/libusb-compat/) did the trick.

### Arch Linux

`libusb-1.0-0` and `pyusb`:
```
sudo pacman -Sy libusb python-pyusb
```
`libusb-0.1-4` has to be installed via AUR, https://aur.archlinux.org/packages/libusb0, e.g., with `yay`:
```
yay -Sy libusb0
```

### Ubuntu
Newer Ubuntu distros (at least, starting from 22.04) have `pyusb==1.2.1` in the official `[universe]` repositories,
and so all the dependencies can be installed with `apt`:

```
sudo apt update
sudo apt install libusb-1.0-0 libusb-0.1-4 python3-usb
```
If you're running an older Ubuntu distro, e.g., 20.04 has `pyusb==1.0.2`, you can install `pyusb` from PyPI:

```
sudo apt update
sudo apt install libusb-1.0-0 libusb-0.1-4 python3-pip
sudo python3 -m pip install pyusb
```
