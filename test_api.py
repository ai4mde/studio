import os
import sys
import json

# Add the app directory to sys.path
sys.path.append(os.path.abspath('api/model/gemini-make-agent'))

# Mock or set environment variables if needed
os.environ['METADATA_API_BASE'] = 'http://localhost:8000/api/v1/metadata'
os.environ['PROTOTYPE_API_BASE'] = 'http://localhost:8010'
os.environ['DESIGN_SPECS_DIR'] = os.path.abspath('design_specs')

from app.tools import get_interface_full_context

interface_id = '7cb15d30-277c-4cf2-b735-826bea27b2d5'
try:
    context = get_interface_full_context(interface_id)
    print(context)
except Exception as e:
    print(f"Error: {e}")
