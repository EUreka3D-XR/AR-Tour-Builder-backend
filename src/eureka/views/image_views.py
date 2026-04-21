from django.http import HttpResponse
from rest_framework import generics, permissions, status
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from eureka.models import Image
from eureka.serializers.image_serializers import ImageUploadSerializer, ImageListSerializer


class ImageUploadView(generics.CreateAPIView):
    """
    Upload a new image via JSON (base64) or multipart/form-data.
    Requires authentication.
    """
    queryset = Image.objects.all()
    serializer_class = ImageUploadSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    @extend_schema(
        summary="Upload an image",
        description=(
            "Upload an image using either:\n"
            "1. JSON with base64-encoded data\n"
            "2. Multipart/form-data with file upload\n\n"
            "Returns the image ID and public URL."
        ),
        examples=[
            OpenApiExample(
                'Base64 JSON upload',
                value={
                    "data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                    "content_type": "image/png",
                    "filename": "example.png"
                },
                request_only=True,
            ),
            OpenApiExample(
                'Multipart file upload',
                value={
                    "file": "(binary)",
                    "filename": "example.png"
                },
                request_only=True,
            ),
        ],
        responses={
            201: ImageUploadSerializer,
            400: OpenApiResponse(description="Invalid image data"),
            401: OpenApiResponse(description="Authentication required"),
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        """Set the uploaded_by field to the current user."""
        serializer.save(uploaded_by=self.request.user)


class ImageListView(generics.ListAPIView):
    """
    List all images (metadata only).
    Public access.
    """
    queryset = Image.objects.all()
    serializer_class = ImageListSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="List all images",
        description="Get metadata for all images (does not include binary data).",
        responses={200: ImageListSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ImageRetrieveView(APIView):
    """
    Retrieve an image by ID.
    Returns the actual image data with correct content-type.
    Public access.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Get an image",
        description="Retrieve image binary data by ID with appropriate content-type header.",
        responses={
            200: OpenApiResponse(
                description="Image binary data",
                response=bytes,
            ),
            404: OpenApiResponse(description="Image not found"),
        }
    )
    def get(self, request, pk):
        try:
            image = Image.objects.get(pk=pk)
        except Image.DoesNotExist:
            return Response(
                {"detail": "Image not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Return binary data with correct content-type
        response = HttpResponse(bytes(image.data), content_type=image.content_type)

        # Add cache headers for better performance
        response['Cache-Control'] = 'public, max-age=3600'

        # Add Content-Disposition for better filename handling
        if image.filename:
            response['Content-Disposition'] = f'inline; filename="{image.filename}"'

        return response
