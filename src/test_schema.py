#!/usr/bin/env python3
"""
Test script to verify that the MultilingualText schema is properly appearing
in the API documentation for all models (Project, Tour, POI, Asset).
"""

import os
import sys
import django
import json

# Add the project root to the Python path
sys.path.insert(0, '/app')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eureka.settings')
django.setup()

from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.settings import spectacular_settings
from eureka.urls import urlpatterns

def test_multilingual_text_schema():
    """Test that MultilingualText schema appears in the API documentation."""
    
    # Generate the schema
    generator = SchemaGenerator()
    schema = generator.get_schema(request=None, public=True)
    
    # Check if MultilingualText schema is defined
    if 'components' in schema and 'schemas' in schema['components']:
        schemas = schema['components']['schemas']
        
        if 'MultilingualText' in schemas:
            print("✅ MultilingualText schema is properly defined!")
            print(f"Schema definition: {json.dumps(schemas['MultilingualText'], indent=2)}")
        else:
            print("❌ MultilingualText schema is NOT found in the API schema!")
            return False
    
    # Check if the schema is referenced in model serializers
    model_schemas = ['Project', 'Tour', 'POI', 'Asset']
    missing_refs = []
    
    for model_name in model_schemas:
        if model_name in schemas:
            model_schema = schemas[model_name]
            properties = model_schema.get('properties', {})
            
            # Check for multilingual fields
            multilingual_fields = []
            if model_name == 'Project':
                multilingual_fields = ['title', 'description']
            elif model_name == 'Tour':
                multilingual_fields = ['title', 'description']
            elif model_name == 'POI':
                multilingual_fields = ['name', 'description']
            elif model_name == 'Asset':
                multilingual_fields = ['title', 'description']
            
            for field in multilingual_fields:
                if field in properties:
                    field_schema = properties[field]
                    if '$ref' in field_schema and field_schema['$ref'] == '#/components/schemas/MultilingualText':
                        print(f"✅ {model_name}.{field} properly references MultilingualText schema")
                    else:
                        print(f"❌ {model_name}.{field} does NOT reference MultilingualText schema")
                        print(f"   Current schema: {json.dumps(field_schema, indent=2)}")
                        missing_refs.append(f"{model_name}.{field}")
                else:
                    print(f"❌ {model_name}.{field} field not found in schema")
                    missing_refs.append(f"{model_name}.{field}")
        else:
            print(f"❌ {model_name} schema not found in API documentation")
            missing_refs.append(model_name)
    
    if missing_refs:
        print(f"\n❌ Missing or incorrect references: {missing_refs}")
        return False
    else:
        print("\n✅ All MultilingualText references are properly configured!")
        return True

if __name__ == '__main__':
    print("Testing MultilingualText schema in API documentation...")
    success = test_multilingual_text_schema()
    
    if success:
        print("\n🎉 All tests passed! MultilingualText schema is properly configured.")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Please check the configuration.")
        sys.exit(1) 