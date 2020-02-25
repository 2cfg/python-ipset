import ipaddress

from contextlib import contextmanager

from ipset.lib import ffi, C


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
            raise ValueError('Family should be one of {F}'
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
        C.ipset_load_types()
        session = C.ipset_session_init(C.printf)

        return session

    @staticmethod
    def __close_session(session):
        C.ipset_session_fini(session)

    @classmethod
    @contextmanager
    def session(cls, s):
        try:
            yield s
        finally:
            cls.__close_session(s)

    def __create(self):
        with self.__class__.session(self.__init_session()) as s:
            rc = C.ipset_data_set(C.ipset_session_data(s),
                                  C.IPSET_SETNAME, self._name.encode())
            assert rc == 0

            C.ipset_data_set(C.ipset_session_data(s),
                             C.IPSET_OPT_TYPENAME, self._type.encode())

            t = C.ipset_type_get(s, C.IPSET_CMD_CREATE)
            C.ipset_data_set(C.ipset_session_data(s), C.IPSET_OPT_TYPE, t)

            if self._exist:
                C.ipset_envopt_parse(s, C.IPSET_ENV_EXIST, ffi.NULL)

            family_ptr = None
            if self._family == 'inet':
                family_ptr = ffi.new("int *", C.NFPROTO_IPV4)
            elif self._family == 'inet6':
                family_ptr = ffi.new("int *", C.NFPROTO_IPV6)

            C.ipset_data_set(C.ipset_session_data(s),
                             C.IPSET_OPT_FAMILY, family_ptr)

            if self._netmask is not None:
                mask = ffi.new("struct in_addr *")
                mask.s_addr = int(self._netmask)
                C.ipset_data_set(C.ipset_session_data(s),
                                 C.IPSET_OPT_NETMASK, mask)

            rc = C.ipset_cmd(s, C.IPSET_CMD_CREATE, 0)
            assert rc == 0

    def add(self, item):
        if self._type == 'hash:ip':
            ip = None
            cidr = None
            ip_net = ipaddress.ip_network(item)
            ip = ffi.new("union nf_inet_addr *")
            af = None
            if isinstance(ip_net, ipaddress.IPv4Network):
                af = C.AF_INET
            elif isinstance(ip_net, ipaddress.IPv6Network):
                af = C.AF_INET6
            rc = C.inet_pton(af, str(ip_net.network_address).encode(), ip)
            assert rc == 1
            cidr = int(ip_net.prefixlen)

            with self.__class__.session(self.__init_session()) as s:
                rc = C.ipset_data_set(C.ipset_session_data(s),
                                      C.IPSET_SETNAME, self._name.encode())
                assert rc == 0

                t = C.ipset_type_get(s, C.IPSET_CMD_ADD)
                C.ipset_data_set(C.ipset_session_data(s),
                                 C.IPSET_OPT_TYPE, t)

                if self._exist:
                    C.ipset_envopt_parse(s, C.IPSET_ENV_EXIST, ffi.NULL)

                C.ipset_data_set(C.ipset_session_data(s),
                                 C.IPSET_OPT_IP, ip)

                C.ipset_data_set(C.ipset_session_data(s),
                                 C.IPSET_OPT_CIDR, ffi.new("uint8_t *", cidr))

                rc = C.ipset_cmd(s, C.IPSET_CMD_ADD, 0)
                assert rc == 0

        else:
            raise NotImplementedError('Adding to {t} not implemented yet'
                                      .format(t=self._type))
        return

    def remove(self, item):
        raise NotImplementedError('Remove not implemented yet')

    def destroy(self):
        with self.__class__.session(self.__init_session()) as s:
            rc = C.ipset_data_set(C.ipset_session_data(s),
                                  C.IPSET_SETNAME, self._name.encode())
            assert rc == 0

            t = C.ipset_type_get(s, C.IPSET_CMD_DESTROY)
            C.ipset_data_set(C.ipset_session_data(s),
                             C.IPSET_OPT_TYPE, t)

            rc = C.ipset_cmd(s, C.IPSET_CMD_DESTROY, 0)
            assert rc == 0
        self.__dict__ = {}

    @classmethod
    def swap(cls, first_set, second_set):

        if not all((isinstance(first_set, cls),
                   isinstance(second_set, cls))):
            raise Exception('Both arguments must be {c} instances'
                            .format(c=cls.__name__))

        with cls.session(cls.__init_session()) as s:
            rc = C.ipset_data_set(C.ipset_session_data(s),
                                  C.IPSET_SETNAME, first_set.name.encode())
            assert rc == 0

            t = C.ipset_type_get(s, C.IPSET_CMD_SWAP)
            C.ipset_data_set(C.ipset_session_data(s),
                             C.IPSET_OPT_TYPE, t)

            rc = C.ipset_data_set(C.ipset_session_data(s),
                                  C.IPSET_OPT_SETNAME2, second_set.name.encode())
            assert rc == 0

            rc = C.ipset_cmd(s, C.IPSET_CMD_SWAP, 0)
            assert rc == 0
        first_set.name, second_set.name = second_set.name, first_set.name
        first_set.__dict__, second_set.__dict__ =\
            second_set.__dict__, first_set.__dict__
