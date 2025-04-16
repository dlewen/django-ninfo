import os
from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-ninfo',
    version='0.6.1',
    packages=['django_ninfo'],
    include_package_data=True,
    license='BSD License',  # example license
    description='a django frontend for ninfo',
    long_description=README,
    author='Justin Azoff`',
    author_email='jazoff@illinois.edu',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License', # example license
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.9',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires = [
        "djangorestframework",
        "ninfo>=0.3.1",
    ],
)
