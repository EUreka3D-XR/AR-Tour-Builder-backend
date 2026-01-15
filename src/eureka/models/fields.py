from django.db import models
from django.core.exceptions import ValidationError
import json


class Coordinates(models.JSONField):
    """
    A JSONField that enforces coordinate structure with lat and long.

    Expected structure:
    {
        "lat": 37.9838,
        "long": 23.7275
    }

    This field provides:
    - Schema validation at the model level
    - Reusable across all models
    - Self-documenting code
    - Type safety through validation
    - Float values for latitude and longitude

    Usage:
        class MyModel(models.Model):
            location = Coordinates()
            destination = Coordinates(blank=True, null=True)
    """

    description = "Geographic coordinates with latitude and longitude"

    def validate(self, value, model_instance):
        """Validate the JSON structure of coordinates."""
        super().validate(value, model_instance)

        # Skip validation if field allows null and value is None
        if value is None and self.null:
            return

        # Skip validation if field allows blank and value is empty
        if not value and self.blank:
            return

        # Validate structure
        if not isinstance(value, dict):
            raise ValidationError(
                "Coordinates must be a dictionary",
                code='invalid_type',
                params={'value': value}
            )

        # Check required keys
        if "lat" not in value:
            raise ValidationError(
                "Coordinates must have a 'lat' key",
                code='missing_lat_key',
                params={'value': value}
            )

        if "long" not in value:
            raise ValidationError(
                "Coordinates must have a 'long' key",
                code='missing_long_key',
                params={'value': value}
            )

        # Validate lat value
        lat = value.get("lat")
        if not isinstance(lat, (int, float)):
            raise ValidationError(
                f"Latitude must be a number, got {type(lat).__name__}",
                code='invalid_lat_type',
                params={'lat': lat}
            )

        # Validate latitude range (-90 to 90)
        if not (-90 <= lat <= 90):
            raise ValidationError(
                f"Latitude must be between -90 and 90, got {lat}",
                code='invalid_lat_range',
                params={'lat': lat}
            )

        # Validate long value
        long = value.get("long")
        if not isinstance(long, (int, float)):
            raise ValidationError(
                f"Longitude must be a number, got {type(long).__name__}",
                code='invalid_long_type',
                params={'long': long}
            )

        # Validate longitude range (-180 to 180)
        if not (-180 <= long <= 180):
            raise ValidationError(
                f"Longitude must be between -180 and 180, got {long}",
                code='invalid_long_range',
                params={'long': long}
            )

    def deconstruct(self):
        """
        Support for migrations.
        Tell Django how to serialize this field.
        """
        name, path, args, kwargs = super().deconstruct()
        return name, path, args, kwargs


class BoundingBox(models.JSONField):
    """
    A JSONField that enforces bounding box structure as an array of two coordinates.
    The first coordinate is southwest, the second is northeast.

    Expected structure:
    [
        {"lat": 37.9700, "long": 23.7100},  # Southwest corner
        {"lat": 37.9900, "long": 23.7400}   # Northeast corner
    ]

    This field provides:
    - Schema validation at the model level
    - Reusable across all models
    - Self-documenting code
    - Type safety through validation
    - Array of two coordinate points defining a bounding box

    Usage:
        class MyModel(models.Model):
            bounds = BoundingBox()
            search_area = BoundingBox(blank=True, null=True)
    """

    description = "Geographic bounding box as array of [southwest, northeast] coordinates"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default', list)
        super().__init__(*args, **kwargs)

    def _validate_coordinate(self, coord_data, coord_name, index):
        """Helper method to validate a single coordinate object."""
        if not isinstance(coord_data, dict):
            raise ValidationError(
                f"Coordinate at index {index} ({coord_name}) must be a dictionary",
                code=f'invalid_coordinate_{index}_type',
                params={'value': coord_data, 'index': index}
            )

        # Check required keys
        if "lat" not in coord_data:
            raise ValidationError(
                f"Coordinate at index {index} ({coord_name}) must have a 'lat' key",
                code=f'missing_coordinate_{index}_lat_key',
                params={'value': coord_data, 'index': index}
            )

        if "long" not in coord_data:
            raise ValidationError(
                f"Coordinate at index {index} ({coord_name}) must have a 'long' key",
                code=f'missing_coordinate_{index}_long_key',
                params={'value': coord_data, 'index': index}
            )

        # Validate lat value
        lat = coord_data.get("lat")
        if not isinstance(lat, (int, float)):
            raise ValidationError(
                f"Coordinate at index {index} ({coord_name}) latitude must be a number, got {type(lat).__name__}",
                code=f'invalid_coordinate_{index}_lat_type',
                params={'lat': lat, 'index': index}
            )

        # Validate latitude range (-90 to 90)
        if not (-90 <= lat <= 90):
            raise ValidationError(
                f"Coordinate at index {index} ({coord_name}) latitude must be between -90 and 90, got {lat}",
                code=f'invalid_coordinate_{index}_lat_range',
                params={'lat': lat, 'index': index}
            )

        # Validate long value
        long = coord_data.get("long")
        if not isinstance(long, (int, float)):
            raise ValidationError(
                f"Coordinate at index {index} ({coord_name}) longitude must be a number, got {type(long).__name__}",
                code=f'invalid_coordinate_{index}_long_type',
                params={'long': long, 'index': index}
            )

        # Validate longitude range (-180 to 180)
        if not (-180 <= long <= 180):
            raise ValidationError(
                f"Coordinate at index {index} ({coord_name}) longitude must be between -180 and 180, got {long}",
                code=f'invalid_coordinate_{index}_long_range',
                params={'long': long, 'index': index}
            )

        return lat, long

    def validate(self, value, model_instance):
        """Validate the JSON structure of bounding box."""
        super().validate(value, model_instance)

        # Skip validation if field allows null and value is None
        if value is None and self.null:
            return

        # Skip validation if field allows blank and value is empty
        if not value and self.blank:
            return

        # Validate structure is a list
        if not isinstance(value, list):
            raise ValidationError(
                "BoundingBox must be an array",
                code='invalid_type',
                params={'value': value}
            )

        # Validate array has exactly 2 elements
        if len(value) != 2:
            raise ValidationError(
                f"BoundingBox must have exactly 2 coordinates, got {len(value)}",
                code='invalid_array_length',
                params={'length': len(value)}
            )

        # Validate both coordinates
        southwest = value[0]
        northeast = value[1]

        sw_lat, sw_long = self._validate_coordinate(southwest, "southwest", 0)
        ne_lat, ne_long = self._validate_coordinate(northeast, "northeast", 1)

        # Validate that southwest is actually southwest of northeast
        if sw_lat >= ne_lat:
            raise ValidationError(
                f"Southwest latitude ({sw_lat}) must be less than northeast latitude ({ne_lat})",
                code='invalid_bounding_box_lat',
                params={'sw_lat': sw_lat, 'ne_lat': ne_lat}
            )

        if sw_long >= ne_long:
            raise ValidationError(
                f"Southwest longitude ({sw_long}) must be less than northeast longitude ({ne_long})",
                code='invalid_bounding_box_long',
                params={'sw_long': sw_long, 'ne_long': ne_long}
            )

    def deconstruct(self):
        """
        Support for migrations.
        Tell Django how to serialize this field.
        """
        name, path, args, kwargs = super().deconstruct()
        # Remove default if it's the standard list
        if 'default' in kwargs and kwargs['default'] == list:
            del kwargs['default']
        return name, path, args, kwargs


class MultilingualTextField(models.JSONField):
    """
    A JSONField that enforces multilingual text content structure.
    Each locale contains a simple string value.

    Expected structure:
    {
        "locales": {
            "en": "English text",
            "fr": "French text",
            "el": "Greek text",
            ...
        }
    }

    This field provides:
    - Schema validation at the model level
    - Reusable across all models
    - Self-documenting code
    - Type safety through validation
    - String-only values for simplicity

    Usage:
        class MyModel(models.Model):
            title = MultilingualTextField()
            description = MultilingualTextField(blank=True, null=True)
    """

    description = "Multilingual text content with locale-based string translations"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default', dict)
        super().__init__(*args, **kwargs)

    def validate(self, value, model_instance):
        """Validate the JSON structure of multilingual text content."""
        super().validate(value, model_instance)

        # Skip validation if field allows null and value is None
        if value is None and self.null:
            return

        # Skip validation if field allows blank and value is empty
        if not value and self.blank:
            return

        # Validate structure
        if not isinstance(value, dict):
            raise ValidationError(
                "MultilingualTextField must be a dictionary",
                code='invalid_type',
                params={'value': value}
            )

        if "locales" not in value:
            raise ValidationError(
                "MultilingualTextField must have a 'locales' key",
                code='missing_locales_key',
                params={'value': value}
            )

        locales = value.get("locales")
        if not isinstance(locales, dict):
            raise ValidationError(
                "'locales' must be a dictionary mapping locale codes to text",
                code='invalid_locales_type',
                params={'locales': locales}
            )

        # Validate each locale entry - must be strings
        for locale_code, text in locales.items():
            if not isinstance(locale_code, str):
                raise ValidationError(
                    f"Locale code must be a string, got {type(locale_code).__name__}",
                    code='invalid_locale_code',
                    params={'locale_code': locale_code}
                )

            if not isinstance(text, str):
                raise ValidationError(
                    f"Text for locale '{locale_code}' must be a string, got {type(text).__name__}",
                    code='invalid_locale_text',
                    params={'locale_code': locale_code, 'text': text}
                )

    def deconstruct(self):
        """
        Support for migrations.
        Tell Django how to serialize this field.
        """
        name, path, args, kwargs = super().deconstruct()
        # Remove default if it's the standard dict
        if 'default' in kwargs and kwargs['default'] == dict:
            del kwargs['default']
        return name, path, args, kwargs


class MultilingualJSONField(models.JSONField):
    """
    A JSONField that enforces multilingual content structure with support for nested JSON.
    Each locale can contain any JSON-serializable value (dict, list, string, number, etc.).

    Expected structure:
    {
        "locales": {
            "en": {
                "title": "Welcome",
                "subtitle": "Hello World",
                "items": ["item1", "item2"]
            },
            "fr": {
                "title": "Bienvenue",
                "subtitle": "Bonjour le monde",
                "items": ["élément1", "élément2"]
            }
        }
    }

    Or simpler structures:
    {
        "locales": {
            "en": ["apple", "banana"],
            "fr": ["pomme", "banane"]
        }
    }

    This field provides:
    - Schema validation at the model level
    - Support for complex nested structures
    - Reusable across all models
    - Self-documenting code
    - Type safety through validation

    Usage:
        class MyModel(models.Model):
            metadata = MultilingualJSONField()
            config = MultilingualJSONField(blank=True, null=True)
    """

    description = "Multilingual JSON content with locale-based structured data"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default', dict)
        super().__init__(*args, **kwargs)

    def validate(self, value, model_instance):
        """Validate the JSON structure of multilingual content."""
        super().validate(value, model_instance)

        # Skip validation if field allows null and value is None
        if value is None and self.null:
            return

        # Skip validation if field allows blank and value is empty
        if not value and self.blank:
            return

        # Validate structure
        if not isinstance(value, dict):
            raise ValidationError(
                "MultilingualJSONField must be a dictionary",
                code='invalid_type',
                params={'value': value}
            )

        if "locales" not in value:
            raise ValidationError(
                "MultilingualJSONField must have a 'locales' key",
                code='missing_locales_key',
                params={'value': value}
            )

        locales = value.get("locales")
        if not isinstance(locales, dict):
            raise ValidationError(
                "'locales' must be a dictionary mapping locale codes to content",
                code='invalid_locales_type',
                params={'locales': locales}
            )

        # Validate each locale entry - locale codes must be strings, values can be any JSON type
        for locale_code, content in locales.items():
            if not isinstance(locale_code, str):
                raise ValidationError(
                    f"Locale code must be a string, got {type(locale_code).__name__}",
                    code='invalid_locale_code',
                    params={'locale_code': locale_code}
                )

            # Validate that content is JSON-serializable
            try:
                json.dumps(content)
            except (TypeError, ValueError) as e:
                raise ValidationError(
                    f"Content for locale '{locale_code}' must be JSON-serializable: {str(e)}",
                    code='invalid_locale_content',
                    params={'locale_code': locale_code, 'content': content}
                )

    def deconstruct(self):
        """
        Support for migrations.
        Tell Django how to serialize this field.
        """
        name, path, args, kwargs = super().deconstruct()
        # Remove default if it's the standard dict
        if 'default' in kwargs and kwargs['default'] == dict:
            del kwargs['default']
        return name, path, args, kwargs


class ExternalLink(models.JSONField):
    """
    A JSONField that enforces a single external link structure with title, url, and type.

    Expected structure:
    {
        "title": "Wikipedia",
        "url": "https://en.wikipedia.org",
        "type": "blog"
    }

    This field provides:
    - Schema validation at the model level
    - Reusable across all models
    - Self-documenting code
    - Type safety through validation
    - Single link object

    Usage:
        class MyModel(models.Model):
            link = ExternalLink()
            resource = ExternalLink(blank=True, null=True)
    """

    description = "External link with title, url, and type"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default', dict)
        super().__init__(*args, **kwargs)

    def validate(self, value, model_instance):
        """Validate the JSON structure of external link."""
        super().validate(value, model_instance)

        # Skip validation if field allows null and value is None
        if value is None and self.null:
            return

        # Skip validation if field allows blank and value is empty
        if not value and self.blank:
            return

        # Validate structure
        if not isinstance(value, dict):
            raise ValidationError(
                "ExternalLink must be a dictionary",
                code='invalid_type',
                params={'value': value}
            )

        # Check required keys
        if "title" not in value:
            raise ValidationError(
                "ExternalLink must have a 'title' key",
                code='missing_link_title',
                params={'value': value}
            )

        if "url" not in value:
            raise ValidationError(
                "ExternalLink must have a 'url' key",
                code='missing_link_url',
                params={'value': value}
            )

        if "type" not in value:
            raise ValidationError(
                "ExternalLink must have a 'type' key",
                code='missing_link_type',
                params={'value': value}
            )

        # Validate title is a string
        title = value.get("title")
        if not isinstance(title, str):
            raise ValidationError(
                f"Title must be a string, got {type(title).__name__}",
                code='invalid_link_title_type',
                params={'title': title}
            )

        # Validate url is a string
        url = value.get("url")
        if not isinstance(url, str):
            raise ValidationError(
                f"URL must be a string, got {type(url).__name__}",
                code='invalid_link_url_type',
                params={'url': url}
            )

        # Validate type is a string and one of the allowed values
        link_type = value.get("type")
        if not isinstance(link_type, str):
            raise ValidationError(
                f"Type must be a string, got {type(link_type).__name__}",
                code='invalid_link_type_type',
                params={'type': link_type}
            )

        if link_type not in ['quiz', 'blog']:
            raise ValidationError(
                f"Type must be 'quiz' or 'blog', got '{link_type}'",
                code='invalid_link_type_value',
                params={'type': link_type}
            )

    def deconstruct(self):
        """
        Support for migrations.
        Tell Django how to serialize this field.
        """
        name, path, args, kwargs = super().deconstruct()
        # Remove default if it's the standard dict
        if 'default' in kwargs and kwargs['default'] == dict:
            del kwargs['default']
        return name, path, args, kwargs


class ExternalLinks(models.JSONField):
    """
    A JSONField that enforces multilingual external links structure.
    Each locale contains an array of link objects with title, url, and type.

    Expected structure:
    {
        "locales": {
            "en": [
                {"title": "Wikipedia", "url": "https://en.wikipedia.org", "type": "blog"},
                {"title": "Quiz", "url": "https://example.com/quiz", "type": "quiz"}
            ],
            "fr": [
                {"title": "Wikipédia", "url": "https://fr.wikipedia.org", "type": "blog"}
            ],
            "el": []
        }
    }

    This field provides:
    - Schema validation at the model level
    - Reusable across all models
    - Self-documenting code
    - Type safety through validation
    - Multilingual arrays of link objects

    Usage:
        class MyModel(models.Model):
            external_links = ExternalLinks()
            resources = ExternalLinks(blank=True, null=True)
    """

    description = "Multilingual external links with locale-based arrays of link objects"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default', dict)
        super().__init__(*args, **kwargs)

    def validate(self, value, model_instance):
        """Validate the JSON structure of multilingual external links."""
        super().validate(value, model_instance)

        # Skip validation if field allows null and value is None
        if value is None and self.null:
            return

        # Skip validation if field allows blank and value is empty
        if not value and self.blank:
            return

        # Validate structure
        if not isinstance(value, dict):
            raise ValidationError(
                "ExternalLinks must be a dictionary",
                code='invalid_type',
                params={'value': value}
            )

        if "locales" not in value:
            raise ValidationError(
                "ExternalLinks must have a 'locales' key",
                code='missing_locales_key',
                params={'value': value}
            )

        locales = value.get("locales")
        if not isinstance(locales, dict):
            raise ValidationError(
                "'locales' must be a dictionary mapping locale codes to link arrays",
                code='invalid_locales_type',
                params={'locales': locales}
            )

        # Validate each locale entry
        for locale_code, links in locales.items():
            if not isinstance(locale_code, str):
                raise ValidationError(
                    f"Locale code must be a string, got {type(locale_code).__name__}",
                    code='invalid_locale_code',
                    params={'locale_code': locale_code}
                )

            # Links must be an array
            if not isinstance(links, list):
                raise ValidationError(
                    f"Links for locale '{locale_code}' must be an array, got {type(links).__name__}",
                    code='invalid_locale_links_type',
                    params={'locale_code': locale_code, 'links': links}
                )

            # Validate each link object in the array
            for idx, link in enumerate(links):
                if not isinstance(link, dict):
                    raise ValidationError(
                        f"Link at index {idx} for locale '{locale_code}' must be an object, got {type(link).__name__}",
                        code='invalid_link_type',
                        params={'locale_code': locale_code, 'index': idx, 'link': link}
                    )

                # Check required keys
                if "title" not in link:
                    raise ValidationError(
                        f"Link at index {idx} for locale '{locale_code}' must have a 'title' key",
                        code='missing_link_title',
                        params={'locale_code': locale_code, 'index': idx, 'link': link}
                    )

                if "url" not in link:
                    raise ValidationError(
                        f"Link at index {idx} for locale '{locale_code}' must have a 'url' key",
                        code='missing_link_url',
                        params={'locale_code': locale_code, 'index': idx, 'link': link}
                    )

                if "type" not in link:
                    raise ValidationError(
                        f"Link at index {idx} for locale '{locale_code}' must have a 'type' key",
                        code='missing_link_type',
                        params={'locale_code': locale_code, 'index': idx, 'link': link}
                    )

                # Validate title is a string
                title = link.get("title")
                if not isinstance(title, str):
                    raise ValidationError(
                        f"Title for link at index {idx} in locale '{locale_code}' must be a string, got {type(title).__name__}",
                        code='invalid_link_title_type',
                        params={'locale_code': locale_code, 'index': idx, 'title': title}
                    )

                # Validate url is a string
                url = link.get("url")
                if not isinstance(url, str):
                    raise ValidationError(
                        f"URL for link at index {idx} in locale '{locale_code}' must be a string, got {type(url).__name__}",
                        code='invalid_link_url_type',
                        params={'locale_code': locale_code, 'index': idx, 'url': url}
                    )

                # Validate type is a string and one of the allowed values
                link_type = link.get("type")
                if not isinstance(link_type, str):
                    raise ValidationError(
                        f"Type for link at index {idx} in locale '{locale_code}' must be a string, got {type(link_type).__name__}",
                        code='invalid_link_type_type',
                        params={'locale_code': locale_code, 'index': idx, 'type': link_type}
                    )

                if link_type not in ['quiz', 'blog']:
                    raise ValidationError(
                        f"Type for link at index {idx} in locale '{locale_code}' must be 'quiz' or 'blog', got '{link_type}'",
                        code='invalid_link_type_value',
                        params={'locale_code': locale_code, 'index': idx, 'type': link_type}
                    )

    def deconstruct(self):
        """
        Support for migrations.
        Tell Django how to serialize this field.
        """
        name, path, args, kwargs = super().deconstruct()
        # Remove default if it's the standard dict
        if 'default' in kwargs and kwargs['default'] == dict:
            del kwargs['default']
        return name, path, args, kwargs


class PoiMediaStats(models.JSONField):
    """
    A JSONField that enforces media statistics structure with counts for different media types.

    Expected structure:
    {
        "image": 0,
        "video": 0,
        "audio": 0,
        "model3d": 0,
        "text": 0
    }

    This field provides:
    - Schema validation at the model level
    - Reusable across all models
    - Self-documenting code
    - Type safety through validation
    - Integer values for media counts

    Usage:
        class MyModel(models.Model):
            media_stats = PoiMediaStats()
            stats = PoiMediaStats(blank=True, null=True)
    """

    description = "Media statistics with counts for different media types"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default', dict)
        super().__init__(*args, **kwargs)

    def validate(self, value, model_instance):
        """Validate the JSON structure of media statistics."""
        super().validate(value, model_instance)

        # Skip validation if field allows null and value is None
        if value is None and self.null:
            return

        # Skip validation if field allows blank and value is empty
        if not value and self.blank:
            return

        # Validate structure
        if not isinstance(value, dict):
            raise ValidationError(
                "PoiMediaStats must be a dictionary",
                code='invalid_type',
                params={'value': value}
            )

        # Required media type keys
        required_keys = ['image', 'video', 'audio', 'model3d', 'text']

        # Check all required keys are present
        for key in required_keys:
            if key not in value:
                raise ValidationError(
                    f"PoiMediaStats must have a '{key}' key",
                    code=f'missing_{key}_key',
                    params={'value': value}
                )

        # Validate each value is a non-negative integer
        for key in required_keys:
            val = value.get(key)
            if not isinstance(val, int):
                raise ValidationError(
                    f"Value for '{key}' must be an integer, got {type(val).__name__}",
                    code=f'invalid_{key}_type',
                    params={key: val}
                )

            if val < 0:
                raise ValidationError(
                    f"Value for '{key}' must be non-negative, got {val}",
                    code=f'invalid_{key}_range',
                    params={key: val}
                )

    def deconstruct(self):
        """
        Support for migrations.
        Tell Django how to serialize this field.
        """
        name, path, args, kwargs = super().deconstruct()
        # Remove default if it's the standard dict
        if 'default' in kwargs and kwargs['default'] == dict:
            del kwargs['default']
        return name, path, args, kwargs


class LinkedAsset(models.JSONField):
    """
    A JSONField that enforces multilingual linked asset structure with title and URL.

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

    This field provides:
    - Schema validation at the model level
    - Multilingual support
    - Title and URL for each locale
    - Reusable across all models
    - Self-documenting code
    - Type safety through validation

    Usage:
        class MyModel(models.Model):
            linked_asset = LinkedAsset()
            reference = LinkedAsset(blank=True, null=True)
    """

    description = "Multilingual linked asset with title and URL for each locale"

    def validate(self, value, model_instance):
        """Validate the JSON structure of linked asset."""
        super().validate(value, model_instance)

        # Skip validation if field allows null and value is None
        if value is None and self.null:
            return

        # Skip validation if field allows blank and value is empty
        if not value and self.blank:
            return

        # Validate structure
        if not isinstance(value, dict):
            raise ValidationError(
                "LinkedAsset must be a dictionary",
                code='invalid_type',
                params={'value': value}
            )

        if "locales" not in value:
            raise ValidationError(
                "LinkedAsset must have a 'locales' key",
                code='missing_locales_key',
                params={'value': value}
            )

        locales = value.get("locales")
        if not isinstance(locales, dict):
            raise ValidationError(
                "'locales' must be a dictionary mapping locale codes to link objects",
                code='invalid_locales_type',
                params={'locales': locales}
            )

        # Validate each locale entry
        for locale_code, link_obj in locales.items():
            if not isinstance(locale_code, str):
                raise ValidationError(
                    f"Locale code must be a string, got {type(locale_code).__name__}",
                    code='invalid_locale_code',
                    params={'locale_code': locale_code}
                )

            # Link object must be a dictionary
            if not isinstance(link_obj, dict):
                raise ValidationError(
                    f"Link object for locale '{locale_code}' must be a dictionary, got {type(link_obj).__name__}",
                    code='invalid_link_object_type',
                    params={'locale_code': locale_code, 'link_obj': link_obj}
                )

            # Check required keys
            if "title" not in link_obj:
                raise ValidationError(
                    f"Link object for locale '{locale_code}' must have a 'title' key",
                    code='missing_link_title',
                    params={'locale_code': locale_code, 'link_obj': link_obj}
                )

            if "url" not in link_obj:
                raise ValidationError(
                    f"Link object for locale '{locale_code}' must have a 'url' key",
                    code='missing_link_url',
                    params={'locale_code': locale_code, 'link_obj': link_obj}
                )

            # Validate title is a string
            title = link_obj.get("title")
            if not isinstance(title, str):
                raise ValidationError(
                    f"Title for locale '{locale_code}' must be a string, got {type(title).__name__}",
                    code='invalid_link_title_type',
                    params={'locale_code': locale_code, 'title': title}
                )

            # Validate url is a string
            url = link_obj.get("url")
            if not isinstance(url, str):
                raise ValidationError(
                    f"URL for locale '{locale_code}' must be a string, got {type(url).__name__}",
                    code='invalid_link_url_type',
                    params={'locale_code': locale_code, 'url': url}
                )

    def deconstruct(self):
        """
        Support for migrations.
        Tell Django how to serialize this field.
        """
        name, path, args, kwargs = super().deconstruct()
        return name, path, args, kwargs
