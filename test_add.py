import ipaddress

from ipset.wrapper import IpSet


SET_PREFIX = 24


def add_to_set(ip_set, item):
    net = ipaddress.ip_network(item)

    if not isinstance(net, ipaddress.IPv4Network):
        raise Exception('Only IPv4 nets are supported')

    if net.prefixlen < SET_PREFIX:
        for subnet in net.subnets(new_prefix=24):
            ip_set.add(subnet.network_address)
    else:
        ip_set.add(net.network_address)

print "Creating 1st set..."

myset = IpSet(set_name="test", set_type="hash:ip", set_family="inet",
              netmask=SET_PREFIX)

add_to_set(myset, '127.0.0.1')
add_to_set(myset, '192.168.100.4/32')
add_to_set(myset, '192.168.0.0/27')
add_to_set(myset, '10.8.0.0/19')

print "Creating 2nd set..."

myset2 = IpSet(set_name="test2", set_type="hash:ip", set_family="inet")

myset2.add(ipaddress.IPv4Address('10.0.0.1'))

print "Swapping..."

IpSet.swap(myset, myset2)

print "Destroying..."

myset.destroy()
myset2.destroy()
