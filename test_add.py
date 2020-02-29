#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import ipaddress
from ipset.wrapper import IPSet


# SET_PREFIX = 24
#
# myset24 = IPSet(set_name="test24", set_type="hash:ip", set_family="inet",
#                 netmask=SET_PREFIX, ignore_existing=True)
#
# myset24.add('127.0.0.1')
# myset.add('192.168.100.4/32')
# myset.add('192.168.0.0/27')
# myset.add('10.8.0.0/19')
# myset.add('1.1.1.1')
#
# myset24.list()
# myset24.destroy()

#Example 1: create list with /32 prefix
myset32 = IPSet(set_name="test32", set_type="hash:ip", set_family="inet", ignore_existing=True)

myset32.add('127.0.0.1')
myset32.add('47.92.4.69')
myset32.add('47.92.4.12/30')
myset32.list()
print("Test exist 47.92.4.69 is {}".format(myset32.test('47.92.4.69')))

myset32.remove('47.92.4.69')
print("--"*20)
myset32.list()
print("Test exist 47.92.4.69 is {}".format(myset32.test('47.92.4.69')))

# Example 2: output to variable as xml
try:
    list = myset32.list_get()
    print(list)
except Exception as e:
    print(str(e))

# myset32.destroy()

# print("Creating 2nd set...")
#
# myset2 = IPSet(set_name="test2", set_type="hash:ip", set_family="inet",
#                ignore_existing=True)
#
# myset2.add(ipaddress.IPv4Address('10.0.0.1'))
#
# myset2.list()
#
# print("Swapping...")
#
# IPSet.swap(myset, myset2)
#
# print("Creating IPv6 set...")
#
# ipv6set = IPSet(set_name="testv6", set_type="hash:ip", set_family="inet6",
#                 ignore_existing=True)
#
# ipv6set.add('::1')
# ipv6set.add('fe80::a21d:48ff:fec7:2310')
#
# ipv6set.list()
#
# print("Destroying...")
#
#
# myset2.destroy()
# ipv6set.destroy()
