from pathlib import Path

from setuptools import find_packages, setup


README = Path(__file__).resolve().parent / "README.md"


setup(
    name="tipranks_api",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["pandas", "requests"],
    author="Eleanor Koh",
    description="TipRanks ETF data ingestion, storage, and portfolio analysis tools",
    long_description=README.read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    url="https://github.com/elkhz09/tipranks-etf-analytics",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
)
