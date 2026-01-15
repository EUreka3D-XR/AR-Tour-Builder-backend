from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

@extend_schema_field({
    'type': 'object',
    'properties': {
        'lat': {'type': 'number', 'format': 'float', 'minimum': -90, 'maximum': 90},
        'long': {'type': 'number', 'format': 'float', 'minimum': -180, 'maximum': 180}
    },
    'required': ['lat', 'long']
})
class Coordinates(serializers.JSONField):
    """
    A custom serializer field for geographic coordinates with latitude and longitude.

    Expected structure:
    {
        "lat": 37.9838,
        "long": 23.7275
    }
    """
    pass

@extend_schema_field({
    'type': 'array',
    'items': {
        'type': 'object',
        'properties': {
            'lat': {'type': 'number', 'format': 'float', 'minimum': -90, 'maximum': 90},
            'long': {'type': 'number', 'format': 'float', 'minimum': -180, 'maximum': 180}
        },
        'required': ['lat', 'long']
    },
    'minItems': 2,
    'maxItems': 2,
    'description': 'Array of two coordinates: [southwest, northeast]'
})
class BoundingBox(serializers.JSONField):
    """
    A custom serializer field for geographic bounding box.

    Expected structure:
    [
        {"lat": 37.9700, "long": 23.7100},  # Southwest corner
        {"lat": 37.9900, "long": 23.7400}   # Northeast corner
    ]
    """
    pass

@extend_schema_field({
    'type': 'object',
    'properties': {
        'title': {'type': 'string'},
        'url': {'type': 'string', 'format': 'uri'},
        'type': {'type': 'string', 'enum': ['quiz', 'blog']}
    },
    'required': ['title', 'url', 'type'],
    'description': 'External link with title, url, and type'
})
class ExternalLink(serializers.JSONField):
    """
    A custom serializer field for a single external link.

    Expected structure:
    {
        "title": "Wikipedia",
        "url": "https://en.wikipedia.org",
        "type": "blog"
    }
    """
    pass

@extend_schema_field({
    'type': 'object',
    'properties': {
        'locales': {
            'type': 'object',
            'additionalProperties': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'title': {'type': 'string'},
                        'url': {'type': 'string', 'format': 'uri'},
                        'type': {'type': 'string', 'enum': ['quiz', 'blog']}
                    },
                    'required': ['title', 'url', 'type']
                }
            }
        }
    },
    'required': ['locales'],
    'description': 'Multilingual external links with locale-based arrays of link objects'
})
class ExternalLinks(serializers.JSONField):
    """
    A custom serializer field for multilingual external links.

    Expected structure:
    {
        "locales": {
            "en": [
                {"title": "Wikipedia", "url": "https://en.wikipedia.org", "type": "blog"},
                {"title": "Quiz", "url": "https://example.com/quiz", "type": "quiz"}
            ],
            "fr": [
                {"title": "Wikipédia", "url": "https://fr.wikipedia.org", "type": "blog"}
            ]
        }
    }

    Supports locale filtering: if a 'locale' parameter is passed in the serializer context,
    the field will return just the array for that locale instead of the full multilingual object.
    """
    def to_representation(self, value):
        """
        Convert the multilingual external links to the appropriate representation.
        If locale is specified in context, return just that locale's array.
        Otherwise, return the full multilingual object.
        """
        # Get the standard representation first
        data = super().to_representation(value)

        # Check if locale filter is requested
        locale = self.context.get('locale')
        if locale and isinstance(data, dict) and 'locales' in data:
            # Return just the array for the requested locale
            return data['locales'].get(locale, [])

        # Return full multilingual object
        return data

@extend_schema_field({'ref': '#/components/schemas/MultilingualText'})
class MultilingualTextField(serializers.JSONField):
    """
    A custom serializer field for multilingual text content, which is
    represented as a JSON object with language codes as keys.

    In the OpenAPI schema, this field is represented by a reference to the
    reusable 'MultilingualText' component defined in SPECTACULAR_SETTINGS.

    Supports locale filtering: if a 'locale' parameter is passed in the serializer context,
    the field will return just the string for that locale instead of the full multilingual object.
    """
    def to_representation(self, value):
        """
        Convert the multilingual field to the appropriate representation.
        If locale is specified in context, return just that locale's string.
        Falls back to 'en' if the requested locale doesn't exist.
        Otherwise, return the full multilingual object.
        """
        # Get the standard representation first
        data = super().to_representation(value)

        # Check if locale filter is requested
        locale = self.context.get('locale')
        if locale and isinstance(data, dict) and 'locales' in data:
            locales = data['locales']
            # Return the requested locale, fallback to 'en', or empty string
            return locales.get(locale, locales.get('en', ''))

        # Return full multilingual object
        return data

@extend_schema_field({
    'type': 'object',
    'properties': {
        'image': {'type': 'integer', 'minimum': 0, 'description': 'Number of image assets'},
        'video': {'type': 'integer', 'minimum': 0, 'description': 'Number of video assets'},
        'audio': {'type': 'integer', 'minimum': 0, 'description': 'Number of audio assets'},
        'model3d': {'type': 'integer', 'minimum': 0, 'description': 'Number of 3D model assets'},
        'text': {'type': 'integer', 'minimum': 0, 'description': 'Number of text assets'}
    },
    'required': ['image', 'video', 'audio', 'model3d', 'text'],
    'description': 'Media statistics with counts for different media types'
})
class PoiMediaStats(serializers.JSONField):
    """
    A custom serializer field for POI media statistics.

    Expected structure:
    {
        "image": 0,
        "video": 0,
        "audio": 0,
        "model3d": 0,
        "text": 0
    }
    """
    pass

@extend_schema_field({
    'type': 'object',
    'properties': {
        'locales': {
            'type': 'object',
            'additionalProperties': {
                'type': 'object',
                'properties': {
                    'title': {'type': 'string'},
                    'url': {'type': 'string', 'format': 'uri'}
                },
                'required': ['title', 'url']
            }
        }
    },
    'required': ['locales'],
    'description': 'Multilingual linked asset with title and URL for each locale'
})
class LinkedAsset(serializers.JSONField):
    """
    A custom serializer field for multilingual linked assets.

    Expected structure:
    {
        "locales": {
            "en": {
                "title": "English Wikipedia",
                "url": "https://en.wikipedia.org/wiki/Example"
            },
            "fr": {
                "title": "Wikipédia français",
                "url": "https://fr.wikipedia.org/wiki/Exemple"
            }
        }
    }

    Supports locale filtering: if a 'locale' parameter is passed in the serializer context,
    the field will return just the object for that locale instead of the full multilingual object.
    """
    def to_representation(self, value):
        """
        Convert the multilingual linked asset to the appropriate representation.
        If locale is specified in context, return just that locale's object.
        Falls back to 'en' if the requested locale doesn't exist.
        Otherwise, return the full multilingual object.
        """
        # Get the standard representation first
        data = super().to_representation(value)

        # Check if locale filter is requested
        locale = self.context.get('locale')
        if locale and isinstance(data, dict) and 'locales' in data:
            locales = data['locales']
            # Return the requested locale, fallback to 'en', or empty object
            return locales.get(locale, locales.get('en', {}))

        # Return full multilingual object
        return data