from setuptools import setup, find_packages

setup(
    name="avalytics",
    version="0.1.0",
    description="Crypto Palantir for Avalanche - Blockchain intelligence platform",
    author="Naman Bajpai",
    author_email="bajpainaman@gmail.com",
    url="https://github.com/bajpainaman/Avalytics",
    packages=find_packages(),
    install_requires=[
        "web3==6.11.3",
        "pandas==2.1.4",
        "sqlalchemy==2.0.23",
        "python-dotenv==1.0.0",
        "rich==13.7.0",
        "requests==2.31.0",
        "scikit-learn==1.3.2",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "avalytics=cli.terminal:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
