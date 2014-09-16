from distutils.core import Command
import os
import setuptools
import textwrap
import doctest
import unittest
import pkgutil
import inspect
import importlib

class doctest_command(Command):
    user_options = []
    def initialize_options(self): pass
    def finalize_options(self): pass

    def run(self):
        suite = unittest.TestSuite()
        for pkg in setuptools.find_packages('src'):
            pkg_dir = os.path.dirname(inspect.getfile(importlib.import_module(pkg)))
            mods = [pkg] + list(el[1] for el in pkgutil.iter_modules([pkg_dir], prefix = pkg + '.'))
            for mod in mods:
                suite.addTest(
                    doctest.DocTestSuite(
                        mod,
                        test_finder = doctest.DocTestFinder(exclude_empty = False)
                    )
                )
        unittest.TextTestRunner(verbosity = 2).run(suite)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.join(SCRIPT_DIR, 'src')

setuptools.setup(
    name = 'mail',
    license = 'BSD',
    version = "0.1",
    description = "Terminal mail client, with benefits.",
    package_dir = { '': 'src' },
    packages = setuptools.find_packages('src'),
    test_suite = 'mail',
    cmdclass = {
        'doctest': doctest_command,
    },
    entry_points = {
        'console_scripts': [
            'mail = mail.main:main',
        ],
    },
    install_requires = [
        'html2text',
        'mistune',
        'colorama',
        'blessings',
        'requests',
    ],
    dependency_links = [
        # SETUPTOOLS MAKES ME CRAZY, INSTALL THIS BY HAND
        #'git+https://github.com/hotgloupi/fabulous.git',
    ]
)
