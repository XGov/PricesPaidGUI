import codecs
import os

from setuptools import setup, find_packages


def read(*parts):
    """
    Build an absolute path from *parts* and and return the contents of the
    resulting file.  Assume UTF-8 encoding.
    """
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, *parts), 'rb', 'utf-8') as f:
        return f.read()


setup(
    name='PricesPaidGUI',
    version='0.0.1',
    description='PricesPaidGUI',
    long_description=(read('README.md') + '\n\n' +
                      read('journal.txt')),
    url='https://github.com/18f/PricesPaidGUI',
    license="MIT",
    author="Robert Read",
    author_email='robert.read@gsa.com',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: JavaScript',
    ],
)