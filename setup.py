from setuptools import setup

setup(
        name='polygon-cli',
        version='1.0',
        packages=['polygon_cli'],
        url='https://github.com/kunyavskiy/polygon-cli',
        license='MIT',
        author='Pavel Kunyavskiy',
        author_email='kunyavskiy@gmail.com',
        description='Commandline tool for polygon',
        requires=['colorama', 'requests', 'prettytable'],
        entry_points={
            'console_scripts': [
                'polygon-cli=polygon_cli:main'
            ],
        }
)
