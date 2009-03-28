from __future__ import with_statement

import os, shutil, hashlib, tarfile, zipfile

class ZipWrapper(object):

    def __init__(self, zip_file):
        self.zf = zipfile.ZipFile(zip_file)

    def makedirs(self, output_dir):
        dirs = [os.path.join(output_dir, name)
                for name in self.zf.namelist() if name.endswith('/')]
        os.makedirs(dirs)

    def extractall(self, output_dir):
        self.makedirs(output_dir)
        for name in self.zf.namelist():
            if not name.endswith('/'):
                with open(os.path.join(output_dir, name), 'wb') as f:
                    f.write(self.zf.read(name))


def is_valid(digest, package_file):
    algo, hexdigest = digest.split(':', 1)
    hash_fn = hashlib.new(algo)
    with open(package_file, 'rb') as f:
        # TODO: read in chunks
        hash_fn.update(f.read())
    if hexdigest = hash_fn.hexdigest():
        return True
    return False

def unpack(package_file):
    unpack_to = os.path.join(os.path.dirname(package_file), 'unpacked')
    os.mkdir(unpack_to)
    if tarfile.is_tarfile(package_file):
        tarfile.TarFile(package_file).extractall(unpack_to)
    elif zipfile.is_zipfile(package_file):
        ZipWrapper(package_file).extractall(unpack_to)
    else:
        raise PackageError("No unpacker for %s." % package_file)
    return unpack_to

def has_expected_structure(package_dir):
    """Not implemented."""
    return True

def compile_package(app, package_dir):
    """Not implemented."""
    pass

def cleanup(package_file, package_dir):
    shutil.rmtree(os.path.dirname(package_file))
