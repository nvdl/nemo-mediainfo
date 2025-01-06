# The Script
View video/audio/image information from the properties tab in Nemo.

![image](https://github.com/chocolateimage/nemo-mediainfo/assets/45315451/0a6fb0c9-c24b-48da-9bb0-1774a21e44b7)

### Installation

Clone the repository.

Install the dependencies:
```
sudo apt install nemo-python python3-pymediainfo python3-exifread
```

Create a soft link to the script:
```
mkdir -p ~/.local/share/nemo-python/extensions
cd ~/.local/share/nemo-python/extensions
ln -s path/to/nemo-mediainfo.py
```
