#!/bin/bash

echo "Removing docs/html/"
rm -rf docs/html
echo "Creating documentation..."
pdoc --footer-text 'Version 1.7' \
--favicon 'https://images.peternearing.ca/PyPapertrail_icon.ico' \
--logo 'https://images.peternearing.ca/PyPapertrail_logo.png' \
--output-directory 'docs/html/' \
src/PyPapertrail/*.py
echo "Complete."