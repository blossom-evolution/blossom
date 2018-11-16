import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='blossom',
    version='1.1.0',
    author='Bryan Brzycki',
    author_email='bbrzycki@berkeley.edu',
    description='A simple evolution simulator',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/blossom-evolution/blossom',
    project_urls={
        'Documentation': 'https://blossom.readthedocs.io/en/latest/',
        'Source': 'https://github.com/blossom-evolution/blossom'
    },
    packages=setuptools.find_packages(),
    install_requires=[
       'uuid',
       'numpy',
       'configparser'
    ],
    classifiers=(
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ),
)
