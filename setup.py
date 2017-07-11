import os
import shutil
import sys
import setuptools
import subprocess


from rere.build.extension import build_c_extension


VM_MAIN_FILE = os.path.join(
    os.path.curdir, 'rere', 'vm', 'vm_main.py'
)


def rbuild_research():
    rpython_path = os.environ.get("RPYTHON_PATH")
    if not rpython_path or not os.path.isfile(rpython_path):
        print(
            "FATAL: RPYTHON_PATH env var is not set, could not proceed.",
            file=sys.stderr
        )
        sys.exit(1)

    builder = subprocess.Popen(
        args=[rpython_path, '--shared', '--lldebug', VM_MAIN_FILE]
    )
    return builder.communicate()


def cleanup():
    os.unlink('vm_main-c')
    shutil.move(
        'libvm_main-c.so',
        os.path.join(os.path.curdir, 'rere', 'build', 'librere.so')
    )
    return 0


rbuild_research()
cleanup()
#build_c_extension()


classifiers = [
    (
        'Programming Language :: Python :: %s' % x
    )
    for x in '3.3 3.4 3.5'.split()
]


setuptools.setup(
    name='research',
    description='JITted version of SRE engine.',
    version='0.1.0',
    license='MIT license',
    platforms=['unix', 'linux'],
    keywords=['regular expression', 'jit', 'rpython'],
    author='magniff',
    url='https://github.com/magniff/research',
    install_requires=[
        'pytest', 'CFFI'
    ],
    classifiers=classifiers,
    packages=setuptools.find_packages(),
    zip_safe=False,
)
