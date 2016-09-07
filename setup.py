from setuptools import setup


def _semver(pkg, minver):
    maxver = int(str(minver).split('.')[0]) + 1
    return '{}>={},<{}'.format(pkg, minver, maxver)


setup(
    name='feedreader',
    version='1.0.0',
    py_modules=['feedreader'],
    entry_points={
        'console_scripts': ['feedreader = feedreader:main']
    },
    install_requires=[
        _semver('gevent', 1),
        _semver('requests', 2),
        _semver('feedparser', 5),
        _semver('click', 6),
        'furl',
        'cachecontrol',
        'python-dateutil'
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'flake8']
)
