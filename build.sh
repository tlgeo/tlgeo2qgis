mkdir -p tlgeo2qgis
# Move all .pyc files to dist
rsync -a --include="*/" --include="*.py" --exclude="dist/*" --exclude="tlgeo2qgis/*" --exclude="*" --prune-empty-dirs . tlgeo2qgis/

# (Optional) Remove empty __pycache__ directories
find . -type d -name "__pycache__" -empty -delete

cp logo.png tlgeo2qgis/
cp metadata.prod.txt tlgeo2qgis/metadata.txt