from setuptools import setup, find_namespace_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="starlink-client",
    version="0.1.14.post2",
    # Buscamos paquetes namespace en "starlink_client*" y "spacex*"
    packages=find_namespace_packages(
        include=["starlink_client*", "spacex*"]
    ),
    include_package_data=True,  # necesario si usamos MANIFEST.in
    install_requires=[
        "grpcio>=1.83.0,<2",
        "grpcio-status>=1.83.0,<2",
        "proto-plus>=1.26.1,<2",
        "protobuf>=7.35.1,<8",
        "requests>=2.32,<3",
        "httpx[http2]>=0.28,<1",
        "pydantic>=2.11,<3",
    ],
    description="A Python client for Starlink.",
    author="Hector Oliveros",
    author_email="hector.oliveros.leon@gmail.com",
    url="https://github.com/Eitol/starlink-client",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Typing :: Typed",
    ],
    python_requires='>=3.10',
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="starlink client grpc satellite internet antenna",
)

