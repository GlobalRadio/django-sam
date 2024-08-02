import os
import re

from setuptools import find_packages, setup


def read(file):
    with open(file, 'r', encoding='utf-8') as f:
        return f.read()


def get_version():
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join('django_sam', '__init__.py')).read()
    return re.search('__version__ = [\'"]([^\'"]+)[\'"]', init_py).group(1)


version = get_version()


setup(
    name='django-sam',
    version=version,
    author='Chris Graham',
    license='MIT',
    author_email='chris.graham@global.com',
    description='Basic Static Asset Middleware for Django',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    url='https://github.com/GlobalRadio/django-sam',
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    python_requires='>=3.8',
    install_requires=[
        'django>=3.2.0',
    ],
)
