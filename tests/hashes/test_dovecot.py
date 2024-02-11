# SPDX-License-Identifier:  CC0-1.0
"""
Test dovecot-specific device passwords.
"""

from passlib.context import CryptContext

from devicepasswords import hashes as _


def test_scram_sha1():
    assert CryptContext(schemes=["dovecot_scram_sha1"]).verify(
        'IeDahgai',
        ('{SCRAM-SHA-1}4096,YLq6hzinvC13hpOtiYrY6w==,'
         'U2vQpW46v6506Zsab9NTlPv/jbk=,cJxnNAQ5EeLhLAk6IB8ymube7TU=')
    )


def test_scram_sha256():
    assert CryptContext(schemes=["dovecot_scram_sha256"]).verify(
        'maiPeeja',
        ('{SCRAM-SHA-256}4096,2LdpQgqFUFMdV63SS9XgnQ==,'
         '1lqxQc6gqLHXXuycpPlLyvb8AUSuxBfmZlqaJGzFDOI=,'
         'j+dSYp5a1uwOD6HLuzKvnJSmGeKJuJCLQmN80MCEeS0=')
    )