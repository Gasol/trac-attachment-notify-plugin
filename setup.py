from setuptools import find_packages, setup

PACKAGE = 'TracAttachmentNotifyPlugin'
VERSION = 'UNRELEASE'

try:
    import trac
    if trac.__version__ < '0.11.6':
        print "%s %s requires Trac >= 0.11.6" % (PACKAGE, VERSION)
        sys.exit(1)
except ImportError:
    pass

setup(
    name = PACKAGE,
    version = VERSION,
    author = 'Gasol Wu',
    author_email = 'gasolwu@kkbox.com',
    license = 'BSD',
    packages = find_packages(),
    entry_points = {
        'trac.plugins': [
            'attachment.notify = attachment.notify',
        ],
    },
)

