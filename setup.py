"""Setup script for CPM Enterprise Blueprint."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="cpm-enterprise-blueprint",
    version="1.0.0",
    author="Catherine Kiriakos",
    author_email="cathy.a.kiriakos@gmail.com",
    description="Enterprise data platform blueprint for Chicago Public Media",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ckiriakos/cpm-enterprise-blueprint",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Database :: Database Engines/Servers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "pandas>=1.5.0",
        "numpy>=1.21.0",
        "pyyaml>=6.0",
        "scikit-learn>=1.0.0",
    ],
    extras_require={
        "dev": ["pytest", "black", "flake8"],
        "notebooks": ["jupyter", "ipykernel"],
    },
)
