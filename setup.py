from setuptools import setup, find_packages
setup(
    name = "comettail",
    version = "0.1",
    license = 'BSD',
    description = "Comet Tail Server",
    author = 'Valeriy Zamarayev',
    author_email = 'valeriy.zamarayev@gmail.com',
    install_requires = ['Twisted'],
    packages=find_packages('src'),
    package_dir={'' : 'src'},
    package_data={'comettail' : ['media']},
    entry_points={'console_scripts' : ['comettail=comettail:comettail']},
)
