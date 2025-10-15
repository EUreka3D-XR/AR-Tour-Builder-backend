import os
import mimetypes
from django.conf import settings
from django.http import HttpResponse, Http404
from django.views import View
from pathlib import Path

class ExampleFileView(View):
    """
    Serve example files from the example directory.
    Supports arbitrary binary files with proper MIME type detection.
    """
    
    def get(self, request, file_path):
        # Construct the full path to the example file
        example_dir = Path(settings.BASE_DIR) / 'example'
        full_path = example_dir / file_path
        
        # Security check: ensure the file is within the example directory
        try:
            full_path = full_path.resolve()
            example_dir = example_dir.resolve()
            if not str(full_path).startswith(str(example_dir)):
                raise Http404("File not found")
        except (ValueError, RuntimeError):
            raise Http404("File not found")
        
        # Check if file exists
        if not full_path.exists() or not full_path.is_file():
            raise Http404("File not found")
        
        # Read the file content
        try:
            with open(full_path, 'rb') as f:
                content = f.read()
        except (IOError, OSError):
            raise Http404("File not found")
        
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(str(full_path))
        if mime_type is None:
            # Default to binary if we can't determine the type
            mime_type = 'application/octet-stream'
        
        # Create response with proper headers
        response = HttpResponse(content, content_type=mime_type)
        response['Content-Length'] = len(content)
        
        # Add cache headers for better performance
        response['Cache-Control'] = 'public, max-age=3600'  # Cache for 1 hour
        
        return response
