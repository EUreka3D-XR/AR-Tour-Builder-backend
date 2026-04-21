import base64
import mimetypes
from rest_framework import serializers
from eureka.models import Image


class ImageUploadSerializer(serializers.ModelSerializer):
    """Serializer for uploading images via base64 JSON or multipart file upload."""
    # Accept base64-encoded image data (for JSON) OR file upload (for multipart/form-data)
    data = serializers.CharField(
        write_only=True,
        required=False,
        help_text="Base64-encoded image data (for JSON uploads)"
    )
    file = serializers.FileField(
        write_only=True,
        required=False,
        help_text="Image file (for multipart/form-data uploads)"
    )
    url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Image
        fields = ['id', 'data', 'file', 'content_type', 'filename', 'url', 'size', 'created_at']
        read_only_fields = ['id', 'url', 'size', 'created_at']
        extra_kwargs = {
            'content_type': {'required': False},  # Optional - auto-detected from file
            'filename': {'required': False},  # Optional - auto-detected from file
        }

    def get_url(self, obj):
        """Generate the public URL for the image."""
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/api/images/{obj.id}')
        return f'/api/images/{obj.id}'

    def validate(self, attrs):
        """Ensure either 'data' or 'file' is provided, but not both."""
        data = attrs.get('data')
        file = attrs.get('file')

        if not data and not file:
            raise serializers.ValidationError("Either 'data' (base64) or 'file' must be provided")

        if data and file:
            raise serializers.ValidationError("Provide either 'data' or 'file', not both")

        # Handle file upload
        if file:
            # Read file data
            file_data = file.read()

            # Size check (max 10MB)
            if len(file_data) > 10 * 1024 * 1024:
                raise serializers.ValidationError("Image size must be less than 10MB")

            # Store binary data
            attrs['binary_data'] = file_data

            # Auto-detect content type if not provided
            if not attrs.get('content_type'):
                content_type = file.content_type
                if not content_type or content_type == 'application/octet-stream':
                    # Fallback to guessing from filename
                    content_type, _ = mimetypes.guess_type(file.name)
                attrs['content_type'] = content_type or 'application/octet-stream'

            # Set filename if not provided
            if not attrs.get('filename'):
                attrs['filename'] = file.name

        # Handle base64 upload
        elif data:
            try:
                # Remove data URI prefix if present
                if data.startswith('data:'):
                    data = data.split(',', 1)[1]

                decoded = base64.b64decode(data)

                # Size check (max 10MB)
                if len(decoded) > 10 * 1024 * 1024:
                    raise serializers.ValidationError("Image size must be less than 10MB")

                attrs['binary_data'] = decoded
            except Exception as e:
                raise serializers.ValidationError(f"Invalid base64 data: {str(e)}")

        return attrs

    def validate_content_type(self, value):
        """Ensure content type is an image."""
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml']
        if value and value.lower() not in allowed_types:
            raise serializers.ValidationError(f"Content type must be one of: {', '.join(allowed_types)}")
        return value

    def create(self, validated_data):
        """Create image with binary data."""
        # Remove temporary fields
        validated_data.pop('data', None)
        validated_data.pop('file', None)

        # Get the binary data we prepared in validate()
        binary_data = validated_data.pop('binary_data')

        validated_data['size'] = len(binary_data)
        validated_data['data'] = binary_data
        return super().create(validated_data)


class ImageListSerializer(serializers.ModelSerializer):
    """Minimal serializer for listing images."""
    url = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ['id', 'filename', 'content_type', 'size', 'url', 'created_at']

    def get_url(self, obj):
        """Generate the public URL for the image."""
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/api/images/{obj.id}')
        return f'/api/images/{obj.id}'
