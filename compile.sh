mkdir -p dist
python3 -m compileall -b -f -d dist .

# Move all .pyc files to dist
rsync -a --include="*/" --include="*.pyc" --exclude="dist/*" --exclude="*" --prune-empty-dirs . dist/

# (Optional) Remove empty __pycache__ directories
find . -type d -name "__pycache__" -empty -delete

cp logo.png dist/
cp metadata.prod.txt dist/metadata.txt