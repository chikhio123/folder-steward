from app.dependencies import get_settings_repository, get_file_repository
from app.repositories.settings_repository import SettingsRepository
from app.repositories.file_repository import FileRepository

def test_dependency_providers():
    settings_repo = get_settings_repository()
    assert isinstance(settings_repo, SettingsRepository)

    file_repo = get_file_repository()
    assert isinstance(file_repo, FileRepository)