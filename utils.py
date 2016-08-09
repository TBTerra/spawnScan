#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
import sys
import platform

def get_encryption_lib_path():
    lib_folder_path = os.path.join(
        os.path.dirname(__file__), "lib")
    lib_path = ""
    # win32 doesn't mean necessarily 32 bits
    if sys.platform == "win32":
        if platform.architecture()[0] == '64bit':
            lib_path = os.path.join(lib_folder_path, "encrypt64bit.dll")
        else:
            lib_path = os.path.join(lib_folder_path, "encrypt32bit.dll")

    elif sys.platform == "darwin":
        lib_path = os.path.join(lib_folder_path, "libencrypt-osx-64.so")

    elif os.uname()[4].startswith("arm") and platform.architecture()[0] == '32bit':
        lib_path = os.path.join(lib_folder_path, "libencrypt-linux-arm-32.so")

    elif sys.platform.startswith('linux'):
        if platform.architecture()[0] == '64bit':
            lib_path = os.path.join(lib_folder_path, "libencrypt-linux-x86-64.so")
        else:
            lib_path = os.path.join(lib_folder_path, "libencrypt-linux-x86-32.so")

    elif sys.platform.startswith('freebsd-10'):
        lib_path = os.path.join(lib_folder_path, "libencrypt-freebsd10-64.so")

    else:
        err = "Unexpected/unsupported platform '{}'".format(sys.platform)
        log.error(err)
        raise Exception(err)

    if not os.path.isfile(lib_path):
        err = "Could not find {} encryption library {}".format(sys.platform, lib_path)
        log.error(err)
        raise Exception(err)

    return lib_path
