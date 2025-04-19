import pathlib
from setuptools import setup, find_packages

here = pathlib.Path(__file__).parent

long_description = (here / "README.md").read_text(encoding="utf-8")
version = (here / "VERSION").read_text(encoding="utf-8").strip()
requirements = (here / "requirements.txt").read_text(encoding="utf-8").splitlines()

setup(
    # Unique distribution name to avoid PyPI conflicts
    name="blackcortex-gpt-cli",
    version=version,
    description="BLACKCORTEX GPT CLI — A conversational assistant with memory, config, and logging features.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/BlackCortexAgent/blackcortex-gpt-cli",
    author="Konijima",
    author_email="konijima@blackcortex.net",
    license="MIT",
    packages=find_packages(),
    py_modules=["gpt"],
    install_requires=requirements,
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