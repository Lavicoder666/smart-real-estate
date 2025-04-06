from setuptools import setup, find_packages

setup(
    name='smart-real-estate',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'Django==3.2.8',
        'psycopg2-binary==2.9.6',
        'torch==2.5.0',
        'torchvision==0.21.0',
        'openai==0.27.8',
        'pandas==1.5.3',
        'Pillow==9.5.0',
        'numpy==1.24.3',
        'joblib==1.2.0',
        'python-dotenv==0.21.1',
        'django-rosetta==0.9.8',
        'django-widget-tweaks==1.4.12',
        'requests==2.28.2',
        'beautifulsoup4==4.12.2',
        'gunicorn==20.1.0',
        'dj-database-url==0.5.0',
        'whitenoise==5.3.0'
    ],
)