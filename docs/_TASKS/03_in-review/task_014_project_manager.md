# Task 014: Project Manager UI

## Description
Develop a "Projects" tab within the main DockPanel to list, manage, and view cloud maps published by the user. This provides visibility into what's already on the server.

## Objectives
- [x] **Project List View:**
    - Fetch list of projects from API (`GET /api/map-projects`).
    - Display in a `QTableWidget` or `QListView`.
    - Columns: Name, Date, Status, Link.
- [x] **Project Actions:**
    - **View:** Open URL in browser.
    - **Delete:** Remove project from server.
    - **Edit:** Update metadata (Title/Description).
- [x] **Sync/Refresh:**
    - Button to refresh the list manually.

## Technical Details
- **API Client:** Extend `AuthService` or create `ProjectService` class.
- **UI Components:**
    - `QTableWidget` for the list.
    - Context menu (Right-click) for actions.

## Acceptance Criteria
- [x] "Projects" tab displays list of maps from server.
- [x] Clicking a project row shows details or opens the map.
- [x] User can delete a project via the UI.
