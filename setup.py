from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name="hyperspace_explorer",
      version="0.3.1",
      author="Tomasz Pietruszka",
      author_email="tomek.pietruszka@gmail.com",
      url="https://github.com/tpietruszka/hyperspace_explorer",
      description="Tracking, queueing and distributed execution of ML/DL experiments. Helping define and "
                  "semi-automatically explore hyper-parameter spaces.",
      long_description=long_description,
      long_description_content_type="text/markdown",
      packages=find_packages(),
      scripts=['hyperspace_explorer/hyperspace_worker.py'],
      python_requires='>=3.7',
      install_requires=[
          'sacred>=0.8.1',
          'pymongo>=3.9.0'
      ],
      tests_require=[
          'pytest',
      ],
      extras_require={
          'dev': [
              'commitizen>=1.16.4',
              'pytest',
          ],
          'analysis': [
              'pandas>=1.0.1',
          ],
      },
      )
