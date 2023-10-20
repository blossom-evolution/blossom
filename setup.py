import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as f:
    install_requires = f.readlines()

version_dict = {}
with open("blossom/_version.py") as fp:
    exec(fp.read(), version_dict)
setuptools.setup(
    name='blossom',
    version=version_dict["__version__"],
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
    install_requires=install_requires,
    classifiers=(
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ),
)
