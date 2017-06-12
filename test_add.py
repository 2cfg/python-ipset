import ipaddress

from ipset.wrapper import IPSet


SET_PREFIX = 24

print "Creating 1st set..."

myset = IPSet(set_name="test", set_type="hash:ip", set_family="inet",
              netmask=SET_PREFIX, ignore_existing=True)

myset.add('127.0.0.1')
myset.add('192.168.100.4/32')
myset.add('192.168.0.0/27')
myset.add('10.8.0.0/19')

print "Creating 2nd set..."

myset2 = IPSet(set_name="test2", set_type="hash:ip", set_family="inet",
               ignore_existing=True)

myset2.add(ipaddress.IPv4Address('10.0.0.1'))

print "Swapping..."

IPSet.swap(myset, myset2)

print "Creating IPv6 set..."

ipv6set = IPSet(set_name="testv6", set_type="hash:ip", set_family="inet6",
                ignore_existing=True)

ipv6set.add('::1')
ipv6set.add('fe80::a21d:48ff:fec7:2310')

print "Destroying..."

myset.destroy()
myset2.destroy()
ipv6set.destroy()
