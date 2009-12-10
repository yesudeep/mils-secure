#!/bin/sh
#
# Ideally this should be a part of puppy configurable via puppy.yaml.

cp -R app/public/ $HOME/DropBoxes/mils-alumni/Dropbox/Public/public/
rsync -avc app/public/ yesudeep@assets.milsalumni.org:/var/www/assets.milsalumni.org/

