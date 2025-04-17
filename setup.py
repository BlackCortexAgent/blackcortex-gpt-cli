import pathlib
from setuptools import setup, find_packages

here = pathlib.Path(__file__).parent

long_description = (here / "README.md").read_text(encoding="utf-8")
version = (here / "VERSION").read_text(encoding="utf-8").strip()

setup(
    # Unique distribution name to avoid PyPI conflicts
    name="konijima-gpt-cli",
    version=version,
    description="GPT CLI — A conversational assistant with memory, config, and logging features.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Konijima/gpt-cli",
    author="Konijima",
    author_email="",
    license="MIT",
    packages=find_packages(),
    py_modules=["gpt"],
    install_requires=[
        "openai",
        "rich",
        "prompt_toolkit",
        "python-dotenv",
    ],
    entry_points={
        "console_scripts": [
            "gpt = gpt:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
)