"""
Setup script for OpenMesh
"""
from setuptools import setup, find_packages

setup(
    name="openmesh",
    version="0.1.0",
    description="Decentralized GPU Mesh Compute Sharing Protocol",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "redis==5.0.1",
        "celery==5.3.4",
        "pydantic==2.5.0",
        "pydantic-settings==2.1.0",
        "docker==6.1.3",
        "requests==2.31.0",
        "python-dotenv==1.0.0",
        "aiofiles==23.2.1",
        "httpx==0.25.2",
        "python-multipart==0.0.6",
        "sqlalchemy==2.0.23",
        "aiosqlite==0.19.0",
        "numpy==1.26.2",
        "click==8.1.7",
        "rich==13.7.0",
    ],
    entry_points={
        "console_scripts": [
            "openmesh=app.cli:cli",
        ],
    },
)

