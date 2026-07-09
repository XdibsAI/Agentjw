from setuptools import setup, find_packages

setup(
    name="sicuan",
    version="2.0.0",
    packages=find_packages(),
    install_requires=[
        "openai",
        "anthropic",
        "requests",
        "python-dotenv",
        "rich",
        "sqlite3",
        "pytest",
    ],
    entry_points={
        "console_scripts": [
            "sicuan=sicuan.chat:main",
        ],
    },
)
