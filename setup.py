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
        "httpx>=0.24.0",
        "pyyaml>=6.0.1",
        "rich>=13.0.0",
        "typer>=0.9.0",
        "beautifulsoup4>=4.12.0",
        "pyperclip>=1.8.2",
        "PyQt6>=6.4.0",
        "PyQt6-Qt6>=6.6.1",
        "PyQt6-sip>=13.6.0",
        "qt-material>=2.14",
        "markdown2>=2.4.0",
        "pygments>=2.15.0"
    ],
    entry_points={
        "console_scripts": [
            "pydevcheat=pydevcheat.main:app",
        ],
    },
    author="Eliran Cohen",
    author_email="eliran.cohen.work@gmail.com",
    description="A powerful programming companion for instant command lookups and code snippets",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/elirancv/PyDevCheat",
    project_urls={
        "Bug Tracker": "https://github.com/elirancv/PyDevCheat/issues",
        "Documentation": "https://github.com/elirancv/PyDevCheat#readme",
        "Source Code": "https://github.com/elirancv/PyDevCheat",
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Environment :: X11 Applications :: Qt",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Documentation",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
    keywords="cheatsheet, cli, development, documentation, programming, reference, snippets",
    python_requires=">=3.8",
    package_data={
        "pydevcheat": ["assets/*", "assets/icons/*", "assets/docs/*"],
    },
) 