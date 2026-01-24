import os
import requests
from typing import Optional, Dict, Any, List
from PyQt5.QtCore import QSettings
from .auth_service import AuthService

class ProjectService:
    """
    Service for managing Map Projects (fetching, deleting, updating)
    """
    
    def __init__(self):
        """Initialize ProjectService"""
        self.settings = QSettings("TLGeo", "QGIS2Plugin")
        self.auth_service = AuthService()
        self.strapi_url = self.auth_service.strapi_url
        
    def get_headers(self) -> Dict[str, str]:
        """Get headers with Authorization token"""
        token = self.auth_service.get_token()
        if not token:
            return {}
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def get_projects(self) -> Dict[str, Any]:
        """
        Fetch list of projects from /api/map-projects
        
        Returns:
            dict: Response with 'success' and 'data' (list of projects) or 'error'
        """
        if not self.auth_service.is_authenticated():
            return {'success': False, 'error': 'User not authenticated'}

        try:
            # Assuming standard Strapi find endpoint, usually it returns { data: [...], meta: ... }
            # But based on the task description, it might be a specific endpoint.
            # I will assume standard usage for now but handle potential variations.
            # Also adding populate=* or specific fields might be needed, but I'll start simple.
            # If map-projects is a content type, the endpoint is /api/map-projects
            url = f"{self.strapi_url}/api/map-projects"
            headers = self.get_headers()
            
            # Using params to sort by date descending by default if possible
            params = {"sort": "createdAt:desc"} 
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Strapi v4/v5 usually returns {'data': [...]}. 
                # If 'data' is a list, that's our projects.
                projects = data.get('data', [])
                return {'success': True, 'data': projects}
            else:
                return {
                    'success': False, 
                    'error': f'Failed to fetch projects: {response.status_code}'
                }
                
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f'Network error: {str(e)}'}
            
    def delete_project(self, project_id: int) -> Dict[str, Any]:
        """
        Delete a project by ID
        """
        if not self.auth_service.is_authenticated():
            return {'success': False, 'error': 'User not authenticated'}
            
        try:
            url = f"{self.strapi_url}/api/map-projects/{project_id}"
            headers = self.get_headers()
            
            response = requests.delete(url, headers=headers, timeout=10)
            
            if response.status_code in [200, 204]:
                return {'success': True}
            else:
                return {
                    'success': False, 
                    'error': f'Failed to delete project: {response.status_code}'
                }
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f'Network error: {str(e)}'}

    def update_project(self, project_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update project metadata
        """
        if not self.auth_service.is_authenticated():
            return {'success': False, 'error': 'User not authenticated'}
            
        try:
            url = f"{self.strapi_url}/api/map-projects/{project_id}"
            headers = self.get_headers()
            
            # Strapi expects wrapped data usually { "data": { ... } }
            payload = {"data": data}
            
            response = requests.put(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                return {'success': True, 'data': response.json().get('data')}
            else:
                return {
                    'success': False, 
                    'error': f'Failed to update project: {response.status_code}'
                }
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f'Network error: {str(e)}'}
