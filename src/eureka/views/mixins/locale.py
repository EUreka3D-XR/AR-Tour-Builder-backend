"""
Mixin to add locale parameter to serializer context if provided in query params.
This enables locale-based filtering of multilingual fields in serializers.
"""

class LocaleContextMixin:
    def get_serializer_context(self):
        context = super().get_serializer_context()
        locale = self.request.query_params.get('locale')
        if locale:
            context['locale'] = locale
        return context
