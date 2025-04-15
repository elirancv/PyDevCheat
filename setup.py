from setuptools import setup, find_packages

# Read README.md with proper encoding
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="pydevcheat",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "typer>=0.15.2",
        "rich>=14.0.0",
        "httpx>=0.28.1",
        "beautifulsoup4>=4.13.3",
        "pyperclip>=1.8.2",
    ],
    entry_points={
        "console_scripts": [
            "pydevcheat=pydevcheat.main:app",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A lightning-fast CLI tool to instantly access programming cheat sheets",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pydevcheat",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
) 