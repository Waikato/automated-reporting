from setuptools import setup, find_packages

setup(
    name="waikato-reporting",
    version="17.5.4",
    license="GNU General Public License version 3.0 (GPLv3)",
    description="Django-based framework for automating some reporting at the University of Waikato.",
    author="Peter Reutemann",
    author_email="fracpete@waikato.ac.nz",
    url="https://github.com/Waikato/automated-reporting",
    packages=find_packages(),
    install_requires=[
        "django-python3-ldap>=0.9.14",
        "psycopg2",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python :: 3",
        "Environment :: Web Environment",
        "Operating System :: OS Independent",
        "Framework :: Django",
    ],
)
