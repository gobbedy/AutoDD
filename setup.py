from setuptools import setup, find_packages

INSTALL_REQUIRES = [
    "praw",
    "psaw",
    "pandas",
    "tabulate",
    "requests",
    "proxy_checker"
]

TEST_REQUIRES = [
]

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="autodd",
    version="0.0.2",
    author="Guillaume Perrault-Archambault",
    author_email="gperr050@uottawa.ca",
    description="Finds reddit score and sentiment for trending reddit tickers and reports financials",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="See LICENSE.txt",
    packages=find_packages(),
    url="https://github.com/gobbedy/autodd",
    install_requires=INSTALL_REQUIRES,
    extras_require={
        "test": TEST_REQUIRES,
    },
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Intended Audience :: Developers, Financial and Insurance Industry",
        "Operating System :: OS Independent",
    ],
    keywords="pandas, yahoo finance, finance, stocks, reddit, investing, due diligence",
    python_requires='>=3.6',
)