from distutils.core import setup

DISTNAME='nbx'
FULLVERSION='0.1'

setup(
    name=DISTNAME,
    version=FULLVERSION,
    packages=['nbx'],
    entry_points={
        'console_scripts':
            [
                'nbx = nbx.cli.command:main',
                'nbx-gist = nbx.cli.gist_upload:main',
            ]
    }
)
