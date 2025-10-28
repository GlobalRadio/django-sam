import logging
import mimetypes
import os

import aiofiles
from asgiref.sync import iscoroutinefunction
from django.conf import settings
from django.http import FileResponse, StreamingHttpResponse
from django.utils.decorators import sync_and_async_middleware

logger = logging.getLogger(__name__)


def gather_files(static_root: str, static_url: str) -> dict:
    files = {}

    # Establish various paths we'll need
    root = os.path.abspath(static_root)
    root = root.rstrip(os.path.sep) + os.path.sep
    path = static_url.strip('/')
    path = f'/{path}/' if path else '/'

    if os.path.isdir(root):
        for dirpath, _, filenames in os.walk(root):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                file_url = file_path.replace(root, path)
                files[file_url] = file_path
    else:
        logger.error(f"Static root directory '{root}' does not exist.")

    return files


@sync_and_async_middleware
def static_admin_middleware(get_response):
    files = gather_files(settings.STATIC_ROOT, settings.STATIC_URL)

    if iscoroutinefunction(get_response):

        async def middleware(request):
            if files.get(request.path):
                file_path = files[request.path]

                async def file_iterator():
                    async with aiofiles.open(file_path, 'rb') as f:
                        while chunk := await f.read(8192):
                            yield chunk

                content_type, _ = mimetypes.guess_type(file_path)
                if content_type is None:
                    content_type = 'application/octet-stream'

                response = StreamingHttpResponse(
                    file_iterator(), content_type=content_type
                )

                filename = os.path.basename(file_path)
                response['Content-Disposition'] = f'inline; filename="{filename}"'
                return response

            response = await get_response(request)
            return response

    else:

        def middleware(request):
            if files.get(request.path):
                return FileResponse(open(files[request.path], 'rb'))

            response = get_response(request)
            return response

    return middleware
