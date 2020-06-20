import setuptools

requirements = [
    "connexion",
    "connexion",
    "swagger-ui-bundle",
    "flask",
    "uuid",
    "flask_cors",
    'pandas',
    'xlsxwriter',

]

setuptools.setup(
    name="story_server",
    license="MIT",
    author="Soffer",
    packages=setuptools.find_packages(),
    install_requires=requirements,
)
