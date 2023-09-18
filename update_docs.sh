#!/bin/bash

rm -rf docs/html

pdoc --footer-text 'Version 1.7' \
--favicon 'https://images.peternearing.ca/PyPapertrail_icon.ico' \
--logo 'https://images.peternearing.ca/PyPapertrail_logo.png' \
--output-directory 'docs/html/' \
src/PyPapertrail/*.py
