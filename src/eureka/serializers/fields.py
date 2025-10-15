from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

@extend_schema_field({'ref': '#/components/schemas/MultilingualText'})
class MultilingualTextField(serializers.JSONField):
    """
    A custom serializer field for multilingual text content, which is
    represented as a JSON object with language codes as keys.

    In the OpenAPI schema, this field is represented by a reference to the
    reusable 'MultilingualText' component defined in SPECTACULAR_SETTINGS.
    """
    pass