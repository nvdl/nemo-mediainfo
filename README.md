# About This Fork
* Fix issues with the missing explicit versions of PyGObject.
* Add more fields to the media information.

# About
View video, audio and image information from the properties tab in Nemo.

# Installation
Clone the repository (or download the ZIP).
```
git clone <this-repo>
```

Install the dependencies:
```
sudo apt install nemo-python python3-pymediainfo python3-exifread
```

For supporting HEIC images as well (latest version of "exifread" has issues with HEIC files):
```
sudo apt purge python3-exifread
sudo pip3 install 'exifread==2.3.2' --break-system-packages
sudo apt install nemo-python python3-pymediainfo
```

Create a soft link to the script:
```
mkdir -p ~/.local/share/nemo-python/extensions
cd ~/.local/share/nemo-python/extensions
ln -s path/to/nemo-mediainfo.py
```

Nemo needs to be restarted. Close all the instances or do:
```
killall nemo
```

# Screenshots

## Video file
![screenshot-1](doc/images/screenshot-video.png?raw=true "Screenshot 1")

## Audio file
![screenshot-2](doc/images/screenshot-audio.png?raw=true "Screenshot 2")

## Image file
![screenshot-3](doc/images/screenshot-image.png?raw=true "Screenshot 3")
