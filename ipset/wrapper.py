import ipaddress

from contextlib import contextmanager

from lib import ffi, C


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


class IpSet(object):

    def __init__(self, set_name, set_type="hash:ip", set_family="inet",
                 netmask=None, create=True, ignore_existing=True):

        self._name = set_name
        self._netmask = netmask
        self._exist = ignore_existing

        if set_type not in TYPES:
            raise Exception('Set type should be one of {T}'
                            .format(T=repr(TYPES)))

        if set_family not in FAMILIES:
            raise Exception('Family should be one of {F}'
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
                                  C.IPSET_SETNAME, self._name)
            assert rc == 0

            C.ipset_data_set(C.ipset_session_data(s),
                             C.IPSET_OPT_TYPENAME, self._type)

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
        ip = None
        try:
            ip = ipaddress.ip_address('.'.join(str(item).split('.')[::-1]))
        except Exception:
            print "Only valid IPv4 addresses are supported!"
            raise

        if self._type == 'hash:ip':

            with self.__class__.session(self.__init_session()) as s:
                rc = C.ipset_data_set(C.ipset_session_data(s),
                                      C.IPSET_SETNAME, self._name)
                assert rc == 0

                t = C.ipset_type_get(s, C.IPSET_CMD_ADD)
                C.ipset_data_set(C.ipset_session_data(s),
                                 C.IPSET_OPT_TYPE, t)
                
                if self._exist:
                    C.ipset_envopt_parse(s, C.IPSET_ENV_EXIST, ffi.NULL)


                ip_addr = ffi.new("struct in_addr *")
                ip_addr.s_addr = int(ip)

                C.ipset_data_set(C.ipset_session_data(s),
                                 C.IPSET_OPT_IP, ip_addr)

                rc = C.ipset_cmd(s, C.IPSET_CMD_ADD, 0)
                assert rc == 0

        else:
            raise Exception('Not implemented')
        return

    def remove(self, item):
        raise Exception('Not implemented')

    def destroy(self):
        with self.__class__.session(self.__init_session()) as s:
            rc = C.ipset_data_set(C.ipset_session_data(s),
                                  C.IPSET_SETNAME, self._name)
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
                                  C.IPSET_SETNAME, first_set.name)
            assert rc == 0

            t = C.ipset_type_get(s, C.IPSET_CMD_SWAP)
            C.ipset_data_set(C.ipset_session_data(s),
                             C.IPSET_OPT_TYPE, t)

            rc = C.ipset_data_set(C.ipset_session_data(s),
                                  C.IPSET_OPT_SETNAME2, second_set.name)
            assert rc == 0

            rc = C.ipset_cmd(s, C.IPSET_CMD_SWAP, 0)
            assert rc == 0
        first_set.name, second_set.name = second_set.name, first_set.name
        first_set.__dict__, second_set.__dict__ =\
            second_set.__dict__, first_set.__dict__
