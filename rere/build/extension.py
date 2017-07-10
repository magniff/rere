import os
from cffi import FFI


RERE_BUILDER = FFI()
LIB_HEADERS_DIR = os.path.join(os.path.curdir, 'rere', 'build')


RERE_BUILDER.set_source(
    "_rere",
    '#include <vm_headers.h>',
    libraries=['rere'],
    library_dirs=[LIB_HEADERS_DIR],
    include_dirs=[LIB_HEADERS_DIR],
    extra_link_args=['-Wl,-rpath=%s' % LIB_HEADERS_DIR],
)


with open(os.path.join(LIB_HEADERS_DIR, 'vm_headers.h')) as vm_header:
    RERE_BUILDER.cdef(vm_header.read())


build_c_extension = lambda: RERE_BUILDER.compile(verbose=True)

