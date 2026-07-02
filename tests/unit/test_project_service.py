import pytest
from unittest.mock import MagicMock, patch
from app.projects.util.project_service import ProjectService
from qgis.PyQt.QtCore import QSettings

class TestProjectService:
    @pytest.fixture
    def project_service(self):
        # Reset settings
        settings = QSettings("TLGeo", "QGIS2Plugin")
        settings.store = {}
        return ProjectService()

    def test_get_projects_not_authenticated(self, project_service):
        """Test fetching projects when not logged in"""
        # Ensure no token
        project_service.auth_service.logout()
        
        result = project_service.get_projects()
        
        assert result['success'] is False
        assert result['error'] == 'User not authenticated'

    def test_get_projects_success(self, project_service):
        """Test successful project fetch"""
        # Mock login
        project_service.auth_service.save_token("fake_token")
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": [
                    {"id": 1, "attributes": {"name": "Test Map"}}
                ]
            }
            mock_get.return_value = mock_response
            
            result = project_service.get_projects()
            
            assert result['success'] is True
            assert len(result['data']) == 1
            assert result['data'][0]['id'] == 1
            
            # Verify call
            mock_get.assert_called_with(
                f"{project_service.strapi_url}/api/projects-ext/my-projects",
                headers={"Authorization": "Bearer fake_token", "Content-Type": "application/json"},
                params={"sort": "createdAt:desc"},
                timeout=10
            )

    def test_delete_project_success(self, project_service):
        """Test successful deletion"""
        project_service.auth_service.save_token("fake_token")
        
        with patch('requests.delete') as mock_delete:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_delete.return_value = mock_response
            
            result = project_service.delete_project(123)
            
            assert result['success'] is True
            
            mock_delete.assert_called_with(
                f"{project_service.strapi_url}/api/projects-ext/123",
                headers={"Authorization": "Bearer fake_token", "Content-Type": "application/json"},
                timeout=10
            )

    def test_update_project_success(self, project_service):
        """Test successful update"""
        project_service.auth_service.save_token("fake_token")
        
        with patch('requests.put') as mock_put:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {"id": 1, "attributes": {"name": "New Name"}}
            }
            mock_put.return_value = mock_response
            
            result = project_service.update_project(1, {"name": "New Name"})
            
            assert result['success'] is True
            assert result['data']['attributes']['name'] == "New Name"
            
            mock_put.assert_called_with(
                f"{project_service.strapi_url}/api/projects-ext/1",
                headers={"Authorization": "Bearer fake_token", "Content-Type": "application/json"},
                json={"data": {"name": "New Name"}},
                timeout=10
            )
