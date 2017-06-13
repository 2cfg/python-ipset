python-ipset
============

This library is a Python wrapper around libipset.

It is absolutely a work in progress. Use at your own risk. If you're
interested in helping, send the author an email.

Goals
-----

- Provide an in-process interface to allow Python programs to manipulate
  ipsets.
- Provide a much friendlier Python interface to libipset so that programmers
  don't need to concern themselves with the details of libipset's interface.
- Be fast and small.

TODO
----

- Implement del, test, list, flush, rename
- Implement operations on all kinds of sets (not just hash:ip)
- Implement mass operations (aka restore)
- Handle errors from libipset properly


License
-------

This project is made available under the GNU General Public License, version 2.

