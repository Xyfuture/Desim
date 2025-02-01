from setuptools import setup, find_packages


setup(
    name='Desim',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'greenlet',
        'sortedcontainers'
    ],
    author='xyfuture',
    author_email='xyfuture01@gmail.com',
    description='Discrete event simulation for circuit in Python, similar to SystemC',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
)