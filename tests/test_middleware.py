from django_sam.middleware import gather_files


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
