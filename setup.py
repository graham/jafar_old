import setuptools
from setuptools import setup, find_packages, Extension, Feature

setup(
        name="jafar",
        version=0.2,
        description="Jafar API framework.",
        long_description="Jafar API Framework.",
        author="Graham Abbott",
        author_email="graham.abbott@gmail.com",
        packages=find_packages(),
        platforms=['any'],
        zip_safe=True,
    )

