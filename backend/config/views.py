from django.conf import settings
from django.http import FileResponse, HttpResponse


def spa(request, path=""):
    """Serve the built React app (frontend/dist/index.html) for every non-API URL."""
    index = settings.FRONTEND_DIST / "index.html"
    if index.exists():
        return FileResponse(open(index, "rb"), content_type="text/html")
    return HttpResponse(
        "The React app is not built. In development open http://localhost:5173. "
        "For production run 'npm run build' inside frontend/.", status=404, content_type="text/plain")
