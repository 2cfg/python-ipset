#!/usr/bin/python3
# -*- coding: UTF-8 -*-
from .libipset.ipset import ffi, lib

class Output:
    _buffer = ""

    @staticmethod
    def buffer():
        _buffer = Output._buffer
        Output._buffer = ""
        return _buffer

@ffi.def_extern()
def out_buffer(str):
    Output._buffer += ffi.string(str).decode()
    return 0