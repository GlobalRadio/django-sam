import asyncio
from unittest.mock import AsyncMock, MagicMock

from django.conf import settings
from django.http import FileResponse, StreamingHttpResponse
from django.test import RequestFactory

from django_sam.middleware import gather_files, static_admin_middleware


def test_gather_files_dict_with_valid_path(mocker):
    mocker.patch('os.path.isdir', return_value=True)
    mocker.patch(
        'os.walk',
        return_value=[
            ('/srv/service/static', ('admin',), ()),
            ('/srv/service/static/admin', ('css', 'js'), ()),
            ('/srv/service/static/admin/css', (), ('admin.css',)),
            ('/srv/service/static/admin/js', (), ('admin.js',)),
        ],
    )

    files = gather_files('/srv/service/static', '/static')

    assert files == {
        '/static/admin/css/admin.css': '/srv/service/static/admin/css/admin.css',
        '/static/admin/js/admin.js': '/srv/service/static/admin/js/admin.js',
    }


def test_gather_files_logs_error_with_invalid_path(mocker):
    mocker.patch('os.path.isdir', return_value=False)
    mock_logger = mocker.patch('django_sam.middleware.logger')

    gather_files('/srv/service/static', '/static')

    mock_logger.error.assert_called_once_with(
        "Static root directory '/srv/service/static/' does not exist."
    )


class TestStaticAdminMiddleware:
    def setup_method(self):
        if not settings.configured:
            settings.configure(
                STATIC_ROOT='/test/static',
                STATIC_URL='/static/',
            )
        self.factory = RequestFactory()
        self.mock_files = {'/static/admin/css/admin.css': '/srv/service/static/admin/css/admin.css'}

    def test_middleware_initialization_calls_gather_files(self, mocker):
        mock_gather_files = mocker.patch('django_sam.middleware.gather_files', return_value={})

        def get_response(request):
            return MagicMock()

        static_admin_middleware(get_response)
        mock_gather_files.assert_called_once_with('/test/static', '/static/')

    def test_sync_middleware_serves_static_file(self, mocker):
        mocker.patch('django_sam.middleware.gather_files', return_value=self.mock_files)

        mock_file = MagicMock()
        mocker.patch('builtins.open', return_value=mock_file)

        def get_response(request):
            return MagicMock()

        middleware = static_admin_middleware(get_response)
        request = self.factory.get('/static/admin/css/admin.css')
        response = middleware(request)

        assert isinstance(response, FileResponse)
        assert response.file_to_stream == mock_file

    def test_sync_middleware_handles_non_existent_file(self, mocker):
        mocker.patch('django_sam.middleware.gather_files', return_value=self.mock_files)

        expected_response = MagicMock()
        def get_response(request):
            return expected_response

        middleware = static_admin_middleware(get_response)
        request = self.factory.get('/static/admin/css/nonexistent.css')
        response = middleware(request)

        assert response == expected_response

    def test_sync_middleware_passes_through_non_static_requests(self, mocker):
        mocker.patch('django_sam.middleware.gather_files', return_value=self.mock_files)

        expected_response = MagicMock()
        def get_response(request):
            return expected_response

        middleware = static_admin_middleware(get_response)
        request = self.factory.get('/admin/')
        response = middleware(request)

        assert response == expected_response

    def test_async_middleware_serves_static_file(self, mocker):
        mocker.patch('django_sam.middleware.gather_files', return_value=self.mock_files)

        mock_file = AsyncMock()
        mock_file.read = AsyncMock(side_effect=[b'chunk1', b'chunk2', b''])
        mock_aiofiles = mocker.patch('django_sam.middleware.aiofiles')
        mock_aiofiles.open.return_value.__aenter__.return_value = mock_file

        async def get_response(request):
            return MagicMock()

        middleware = static_admin_middleware(get_response)
        request = self.factory.get('/static/admin/css/admin.css')
        async def run_test():
            response = await middleware(request)
            return response
        response = asyncio.run(run_test())

        assert isinstance(response, StreamingHttpResponse)
        assert response['Content-Type'] == 'text/css'
        assert response['Content-Disposition'] == 'inline; filename="admin.css"'

    def test_async_middleware_handles_nonexistent_file(self, mocker):
        mocker.patch('django_sam.middleware.gather_files', return_value=self.mock_files)

        expected_response = MagicMock()
        async def get_response(request):
            return expected_response

        middleware = static_admin_middleware(get_response)
        request = self.factory.get('/static/admin/css/nonexistent.css')
        async def run_test():
            response = await middleware(request)
            return response
        response = asyncio.run(run_test())

        assert response == expected_response

    def test_async_middleware_handles_unknown_mimetype(self, mocker):
        mocker.patch('django_sam.middleware.gather_files', return_value=self.mock_files)

        mock_file = AsyncMock()
        mock_file.read = AsyncMock(side_effect=[b'content', b''])
        mock_aiofiles = mocker.patch('django_sam.middleware.aiofiles')
        mock_aiofiles.open.return_value.__aenter__.return_value = mock_file

        mocker.patch('django_sam.middleware.mimetypes.guess_type', return_value=(None, None))

        async def get_response(request):
            return MagicMock()

        middleware = static_admin_middleware(get_response)
        request = self.factory.get('/static/admin/css/admin.css')
        async def run_test():
            response = await middleware(request)
            return response
        response = asyncio.run(run_test())

        assert isinstance(response, StreamingHttpResponse)
        assert response['Content-Type'] == 'application/octet-stream'

    def test_async_middleware_passes_through_non_static_requests(self, mocker):
        mocker.patch('django_sam.middleware.gather_files', return_value=self.mock_files)

        expected_response = MagicMock()
        async def get_response(request):
            return expected_response

        middleware = static_admin_middleware(get_response)
        request = self.factory.get('/admin/')
        async def run_test():
            response = await middleware(request)
            return response
        response = asyncio.run(run_test())

        assert response == expected_response
