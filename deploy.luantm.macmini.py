#!/usr/bin/env python3
import os
import shutil
import sys

def main():
    project_src = "/Users/taluan/Workshop/TLGeo/GEOADMIN_WORKSPACE/SRC/PLUGINS_PROJECTS/tlgeo2qgis/src"
    
    qgis_paths = [
        "/Users/taluan/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/tlgeo2qgis",
        "/Users/taluan/Library/Application Support/QGIS/QGIS4/profiles/default/python/plugins/tlgeo2qgis"
    ]
    
    print("=== TLGeo2QGIS Deploy Script for luantm.macmini ===")
    
    if not os.path.exists(project_src):
        print(f"Error: Project source directory '{project_src}' does not exist.")
        sys.exit(1)
        
    for path in qgis_paths:
        parent_dir = os.path.dirname(path)
        if not os.path.exists(parent_dir):
            print(f"Directory '{parent_dir}' does not exist. Skipping.")
            continue
            
        print(f"\nProcessing deployment to: {path}")
        
        # Check if target already exists (file, directory, or symlink)
        if os.path.islink(path):
            current_target = os.readlink(path)
            if current_target == project_src:
                print(f"✓ Already symlinked correctly to {project_src}")
                continue
            else:
                print(f"Removing old symlink: {path} -> {current_target}")
                os.unlink(path)
        elif os.path.exists(path):
            if os.path.isdir(path):
                print(f"Removing existing directory: {path}")
                shutil.rmtree(path)
            else:
                print(f"Removing existing file: {path}")
                os.remove(path)
                
        # Create the symlink
        try:
            os.symlink(project_src, path)
            print(f"✓ Created symlink: {path} -> {project_src}")
        except Exception as e:
            print(f"❌ Error creating symlink: {e}")
            
    print("\nDeployment finished successfully!")

if __name__ == "__main__":
    main()
