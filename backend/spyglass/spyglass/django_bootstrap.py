from dotenv import load_dotenv
import os
import sys
import django

load_dotenv()  # loads from .env file in current dir

project_path = os.environ.get('PYTHONPATH_SPYGLASS')
if not project_path:
    raise EnvironmentError("PYTHONPATH_SPYGLASS is not set.")

sys.path.append(project_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spyglass.settings')

django.setup()
