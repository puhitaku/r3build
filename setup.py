from setuptools import setup, find_packages

version = "0.0.1"

setup(
    name="r3build",
    version=version,
    author="Takumi Sueda",
    author_email="puhitaku@gmail.com",
    description="File change detection + automatic build",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    packages=find_packages(exclude=["test*"]),
    test_suite="tests",
)
