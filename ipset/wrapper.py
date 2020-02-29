#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import ipaddress
from contextlib import contextmanager
from .libipset.ipset import ffi, lib
from .lib_utils import Output
import xml.etree.ElementTree as ET

FAMILIES = [
    'inet',
    'inet6',
]

TYPES = [
    'bitmap:ip',
    'bitmap:ip,mac',
    'bitmap:port',
    'hash:ip',
    'hash:mac',
    'hash:net',
    'hash:net,net',
    'hash:ip,port',
    'hash:net,port',
    'hash:ip,port,ip',
    'hash:ip,port,net',
    'hash:ip,mark',
    'hash:net,port,net',
    'hash:net,iface',
    'list:set',
]


class IPSet(object):

    def __init__(self, set_name, set_type="hash:ip", set_family="inet",
                 netmask=None, create=True, ignore_existing=True):

        self._name = set_name
        self._netmask = netmask
        self._exist = ignore_existing

        if set_type not in TYPES:
            raise ValueError('Set type should be one of {T}'
                             .format(T=repr(TYPES)))

        if set_family not in FAMILIES:
            raise ValueError('Family should be one of {T}'
                             .format(T=repr(FAMILIES)))

        self._family = set_family
        self._type = set_type

        if create:
            self.__create()

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def family(self):
        return self._family

    @property
    def type(self):
        return self._type

    @property
    def netmask(self):
        return self._netmask

    @staticmethod
    def __init_session():
        lib.ipset_load_types()
        session = lib.ipset_session_init(lib.printf)

        return session

    @staticmethod
    def __close_session(session):
        lib.ipset_session_fini(session)

    @classmethod
    @contextmanager
    def session(cls, s):
        try:
            yield s
        finally:
            cls.__close_session(s)

    def __create(self):
        with self.__class__.session(self.__init_session()) as s:
            rc = lib.ipset_data_set(lib.ipset_session_data(s),
                                  lib.IPSET_SETNAME, self._name.encode())
            assert rc == 0

            lib.ipset_data_set(lib.ipset_session_data(s),
                             lib.IPSET_OPT_TYPENAME, self._type.encode())

            t = lib.ipset_type_get(s, lib.IPSET_CMD_CREATE)
            lib.ipset_data_set(lib.ipset_session_data(s), lib.IPSET_OPT_TYPE, t)

            if self._exist:
                lib.ipset_envopt_parse(s, lib.IPSET_ENV_EXIST, ffi.NULL)

            family_ptr = None
            if self._family == 'inet':
                family_ptr = ffi.new("int *", lib.NFPROTO_IPV4)
            elif self._family == 'inet6':
                family_ptr = ffi.new("int *", lib.NFPROTO_IPV6)

            lib.ipset_data_set(lib.ipset_session_data(s),
                             lib.IPSET_OPT_FAMILY, family_ptr)

            if self._netmask is not None:
                mask = ffi.new("struct in_addr *")
                mask.s_addr = int(self._netmask)
                lib.ipset_data_set(lib.ipset_session_data(s),
                                 lib.IPSET_OPT_NETMASK, mask)

            rc = lib.ipset_cmd(s, lib.IPSET_CMD_CREATE, 0)
            assert rc == 0

    def add(self, item):
        if self._type == 'hash:ip':
            ip = None
            cidr = None
            ip_net = ipaddress.ip_network(item)
            ip = ffi.new("union nf_inet_addr *")
            af = None
            if isinstance(ip_net, ipaddress.IPv4Network):
                af = lib.AF_INET
            elif isinstance(ip_net, ipaddress.IPv6Network):
                af = lib.AF_INET6
            rc = lib.inet_pton(af, str(ip_net.network_address).encode(), ip)
            assert rc == 1
            cidr = int(ip_net.prefixlen)

            with self.__class__.session(self.__init_session()) as s:
                rc = lib.ipset_data_set(lib.ipset_session_data(s),
                                      lib.IPSET_SETNAME, self._name.encode())
                assert rc == 0

                t = lib.ipset_type_get(s, lib.IPSET_CMD_ADD)
                lib.ipset_data_set(lib.ipset_session_data(s),
                                 lib.IPSET_OPT_TYPE, t)

                if self._exist:
                    lib.ipset_envopt_parse(s, lib.IPSET_ENV_EXIST, ffi.NULL)

                lib.ipset_data_set(lib.ipset_session_data(s),
                                 lib.IPSET_OPT_IP, ip)

                lib.ipset_data_set(lib.ipset_session_data(s),
                                 lib.IPSET_OPT_CIDR, ffi.new("uint8_t *", cidr))

                rc = lib.ipset_cmd(s, lib.IPSET_CMD_ADD, 0)
                assert rc == 0

        else:
            raise NotImplementedError('Adding to {t} not implemented yet'
                                      .format(t=self._type))
        return

    def remove(self, item):
        with self.__class__.session(self.__init_session()) as s:
            rc = lib.ipset_data_set(lib.ipset_session_data(s),
                                    lib.IPSET_SETNAME, self._name.encode())
            assert rc == 0

            t = lib.ipset_type_get(s, lib.IPSET_CMD_DEL)
            lib.ipset_data_set(lib.ipset_session_data(s), lib.IPSET_OPT_TYPE, t)

            rc = lib.ipset_parse_elem(s, lib.IPSET_SETNAME, item.encode())
            assert rc == 0

            rc = lib.ipset_cmd(s, lib.IPSET_CMD_DEL, 0)
            assert rc == 0

    def test(self, item):
        with self.__class__.session(self.__init_session()) as s:
            rc = lib.ipset_data_set(lib.ipset_session_data(s),
                                    lib.IPSET_SETNAME, self._name.encode())
            assert rc == 0

            t = lib.ipset_type_get(s, lib.IPSET_CMD_TEST)
            lib.ipset_data_set(lib.ipset_session_data(s), lib.IPSET_OPT_TYPE, t)

            rc = lib.ipset_parse_elem(s, 1, item.encode())
            assert rc == 0

            return lib.ipset_cmd(s, lib.IPSET_CMD_TEST, 0) == 0

    def list_get(self):
        with self.__class__.session(self.__init_session()) as s:
            rc = lib.ipset_data_set(lib.ipset_session_data(s),
                                  lib.IPSET_SETNAME, self._name.encode())
            assert rc == 0

            lib.ipset_session_output(s, lib.IPSET_LIST_XML)
            lib.ipset_session_outfn(s, lib.out_fn)

            rc = lib.ipset_cmd(s, lib.IPSET_CMD_LIST, 0)
            assert rc == 0

            tree = ET.fromstring(Output.buffer())
            return [e.text for e in tree.iter("elem")]

    def list(self):
        with self.__class__.session(self.__init_session()) as s:
            rc = lib.ipset_data_set(lib.ipset_session_data(s),
                                  lib.IPSET_SETNAME, self._name.encode())
            assert rc == 0

            lib.ipset_session_output(s, lib.IPSET_LIST_PLAIN)
            rc = lib.ipset_cmd(s, lib.IPSET_CMD_LIST, 0)
            assert rc == 0

            return

    def destroy(self):
        with self.__class__.session(self.__init_session()) as s:
            rc = lib.ipset_data_set(lib.ipset_session_data(s),
                                  lib.IPSET_SETNAME, self._name.encode())
            assert rc == 0

            t = lib.ipset_type_get(s, lib.IPSET_CMD_DESTROY)
            lib.ipset_data_set(lib.ipset_session_data(s),
                             lib.IPSET_OPT_TYPE, t)

            rc = lib.ipset_cmd(s, lib.IPSET_CMD_DESTROY, 0)
            assert rc == 0
        self.__dict__ = {}

    @classmethod
    def swap(cls, first_set, second_set):

        if not all((isinstance(first_set, cls),
                   isinstance(second_set, cls))):
            raise Exception('Both arguments must be {c} instances'
                            .format(c=cls.__name__))

        with cls.session(cls.__init_session()) as s:
            rc = lib.ipset_data_set(lib.ipset_session_data(s),
                                  lib.IPSET_SETNAME, first_set.name.encode())
            assert rc == 0

            t = lib.ipset_type_get(s, lib.IPSET_CMD_SWAP)
            lib.ipset_data_set(lib.ipset_session_data(s),
                             lib.IPSET_OPT_TYPE, t)

            rc = lib.ipset_data_set(lib.ipset_session_data(s),
                                  lib.IPSET_OPT_SETNAME2, second_set.name.encode())
            assert rc == 0

            rc = lib.ipset_cmd(s, lib.IPSET_CMD_SWAP, 0)
            assert rc == 0
        first_set.name, second_set.name = second_set.name, first_set.name
        first_set.__dict__, second_set.__dict__ =\
            second_set.__dict__, first_set.__dict__
