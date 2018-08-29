#!/usr/bin/env python3
"""
Requires Python 3.6
"""
# from drive_api import Drive
from gg.oauth2 import create_creds_folder
from gg.drive import Drive
import os

from tempfile import SpooledTemporaryFile


def dummy_content():
    """
    ssl.RAND_bytes needs to be seeded before it can be used. So you cannot just rely on ssl.RAND_bytes alone.
    Both os.urandom and ssl.RAND_bytes are pseudo random number generators. PRNG's are deterministic; when
    seeded with the same data, they will return the same stream of pseudo random number bytes. These bytes
    should be indistinguishable from true random if an observer does not know the seed value. os.urandom
    however is normally (re-)seeded using a source of entropy within the operating system.

    Using os.urandom should therefore be preferred over ssl.RAND_bytes. First of all, it is already seeded
    (and will be reseeded by the operating system). Furthermore, it does not require an additional dependency
    on an SSL library. A drawback could be performance. It is probably faster to use ssl.RAND_bytes seeded
    with a big enough value from os.urandom as os.urandom requires a system call any time you retrieve data.

    For ssl.RAND_bytes
    RAND_status() can be used to check the status of the PRNG and RAND_add() can be used to seed the PRNG.
    :return:
    """
    return os.urandom(1 * 1024 * 1024)  # 1MB


RANDOM_DATA = dummy_content()


class Dummy(os.PathLike):

    def __init__(self, content):
        self.content = content

    def __fspath__(self):
        return 'a.txt'


def run(size_in_gb):
    create_creds_folder()

    dummy = SpooledTemporaryFile()
    for i in range(0, size_in_gb, 1):
        dummy.write(RANDOM_DATA * 1024)
    dummy.seek(0)

    file = Dummy(dummy)

    Drive().upload(file)


if __name__ == '__main__':
    try:
        run(1)
    except Exception as e:
        print(e)
    except KeyboardInterrupt:
        os.sys.exit(0)
