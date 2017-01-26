from setuptools import setup

f = open("README.rst")
try:
    try:
        readme_content = f.read()
    except:
        readme_content = ""
finally:
    f.close()

version = '0.3.2'

setup(
    name='restea',
    packages=['restea', 'restea.adapters'],
    version=version,
    description='Simple RESTful server toolkit',
    long_description=readme_content,
    author='Walery Jadlowski',
    author_email='bodb.digr@gmail.com',
    url='https://github.com/bodbdigr/restea',
    download_url='https://github.com/bodbdigr/restea/archive/{}.tar.gz'.format(version),
    keywords=['rest', 'restful', 'restea'],
    install_requires=[
        'future==0.16.0',
    ],
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest==3.0.6',
        'pytest-cov==2.4.0',
        'pytest-mock==1.5.0',
    ],
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
