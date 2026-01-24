import os
import requests
from typing import Optional, Dict, Any, List
from PyQt5.QtCore import QSettings
from ...auth.util.auth_service import AuthService

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
        Fetch list of projects from /api/projects-ext/my-projects
        
        Returns:
            dict: Response with 'success' and 'data' (list of projects) or 'error'
        """
        if not self.auth_service.is_authenticated():
            return {'success': False, 'error': 'User not authenticated'}

        try:
            url = f"{self.strapi_url}/api/projects-ext/my-projects"
            headers = self.get_headers()
            params = {"sort": "createdAt:desc"} 
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                projects = data.get('data', data) if isinstance(data, dict) else data
                if not isinstance(projects, list):
                     projects = []
                return {'success': True, 'data': projects}
            else:
                return {'success': False, 'error': f'Failed to fetch projects: {response.status_code}'}
                
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f'Network error: {str(e)}'}

    def get_shared_projects(self) -> Dict[str, Any]:
        """
        Fetch list of shared projects from /api/projects-ext/shared-with-me
        """
        if not self.auth_service.is_authenticated():
            return {'success': False, 'error': 'User not authenticated'}

        try:
            url = f"{self.strapi_url}/api/projects-ext/shared-with-me"
            headers = self.get_headers()
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Based on controller, returns list of ACL entries populated with project
                # We need to extract the project object from each entry
                entries = data.get('data', data) if isinstance(data, dict) else data
                if not isinstance(entries, list):
                     entries = []
                
                projects = []
                for entry in entries:
                    # Depending on Strapi structure (flat or nested 'attributes')
                    # Controller uses populate: ['project'], so entry has 'project' field
                    # It might be entry['project'] or entry['attributes']['project']
                    
                    proj = None
                    if 'project' in entry:
                        proj = entry['project']
                    elif 'attributes' in entry and 'project' in entry['attributes']:
                        # Strapi v4 standard
                        proj = entry['attributes']['project']
                        # If project is a relation, it might have 'data' wrapper
                        if isinstance(proj, dict) and 'data' in proj:
                            proj = proj['data']
                            
                    if proj:
                        # Add a flag to indicate it's shared
                        # Check if proj is the object or wrapper
                        if 'attributes' in proj:
                             # It's a v4 object wrapper, we might want to flatten or keep consistent
                             pass
                        projects.append(proj)
                        
                return {'success': True, 'data': projects}
            else:
                return {'success': False, 'error': f'Failed to fetch shared projects: {response.status_code}'}
                
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f'Network error: {str(e)}'}
            
    def delete_project(self, project_id: int) -> Dict[str, Any]:
        """Delete a project by ID"""
        if not self.auth_service.is_authenticated():
            return {'success': False, 'error': 'User not authenticated'}
            
        try:
            url = f"{self.strapi_url}/api/projects-ext/{project_id}"
            headers = self.get_headers()
            response = requests.delete(url, headers=headers, timeout=10)
            
            if response.status_code in [200, 204]:
                return {'success': True}
            else:
                return {'success': False, 'error': f'Failed to delete project: {response.status_code}'}
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f'Network error: {str(e)}'}

    def update_project(self, project_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update project metadata"""
        if not self.auth_service.is_authenticated():
            return {'success': False, 'error': 'User not authenticated'}
            
        try:
            url = f"{self.strapi_url}/api/projects-ext/{project_id}"
            headers = self.get_headers()
            payload = {"data": data}
            response = requests.put(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                res_data = response.json()
                return {'success': True, 'data': res_data.get('data', res_data)}
            else:
                return {'success': False, 'error': f'Failed to update project: {response.status_code}'}
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f'Network error: {str(e)}'}
