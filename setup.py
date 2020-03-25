import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


def test_suite():
    import unittest
    test_loader = unittest.TestLoader()
    tests = test_loader.discover('tests', pattern='test_*.py')
    return tests


setuptools.setup(
    name="pipmap",
    version="0.0.5",
    author="Kostiantyn Tarnashynskyi",
    author_email="kostia.tarnashynskyi@gmail.com",
    description="Mapping the installed packages with its top level modules",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/audiua/pipmap",
    packages=['pipmap'],
    license='MIT',
    keywords='package module',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[],
    include_package_data=True,
    python_requires='>=3.6',
    test_suite="setup.test_suite"
)
