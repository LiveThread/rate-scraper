from setuptools import setup

setup(name='rate-scraper',
      version='0.0.1',
      description='Scraping reddit for comment rates',
      url='https://github.com/LiveThread/rate-scraper',
      author='William Reed, Nick Thompson',
      author_email='wreed58@gmail.com',
      license='MIT',
      packages=['funniest'],
      install_requires=[
          'SQLAlchemy',
          'mysqlclient',
          'Flask',
          'praw',
          'prawcore'
      ],
      zip_safe=False)