import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()


def load_requirements(path):
    """Load requirement lines, skipping blanks and comments.

    Args:
        path: Relative path to a requirements file.

    Returns:
        List of normalized requirement specifiers.
    """
    requirements = []
    with open(path, "r") as f:
        for line in f:
            req = line.strip()
            if not req or req.startswith("#"):
                continue
            requirements.append(req)
    return requirements


install_requires = load_requirements("requirements.txt")
test_requires = [
    "pytest>=8.0.0",
]
dev_requires = [
    *test_requires,
]

entry_points = {
    'console_scripts': [
        'blossom = blossom.blossom_exe:cli'
    ]
}

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
    entry_points=entry_points,
    packages=setuptools.find_packages(),
    install_requires=install_requires,
    extras_require={
        'test': test_requires,
        'dev': dev_requires
    },
    classifiers=(
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ),
)
