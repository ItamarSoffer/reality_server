import setuptools

requirements = [
    "connexion",
    "connexion",
    "swagger-ui-bundle",
    "flask",
    "uuid",
    "flask_cors"
]

setuptools.setup(
    name="reality_server",
    license="MIT",
    author="Soffer",
    packages=setuptools.find_packages(),
    install_requires=requirements,
    python_requires=">=3.6",
)
