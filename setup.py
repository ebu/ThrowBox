from setuptools import setup

setup(
    name = 'throwbox',
    version = '0.0.10',
    description = 'A tiny travis-ci clone with rabbit-mq push support and local run',
    long_description = open('README.md').read(),
    keywords = 'travis ci shell',
    license = '',
    author = 'Malik Bougacha',
    author_email = '',
    maintainer = 'Malik Bougacha',
    maintainer_email = '',
    url = 'https://github.com/ebu/ThrowBox',
    dependency_links = ['http://github.com/todddeluca/python-vagrant/tarball/master#egg=python-vagrant'],
    install_requires = ['python-vagrant', 'fabric', 'celery'],
    py_modules = ['throw_box.test_box', 'throw_box.tasks'],

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Plugins',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    include_package_data = True,
)
