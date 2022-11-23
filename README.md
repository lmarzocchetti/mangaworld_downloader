# mangaworld_downloader
A manga pdf downloader from mangaworld

Un programma per scaricare manga da mangaworld(sito italiano)

--------------------------------------
# Setup
## Install Python and dipendencies
- Arch-based:

      sudo pacman -S python python-pip

- Debian/Ubuntu:

      sudo apt install python3 python3-pip


## Install dependencies of Python
    pip install -r requirements.txt

# Usage
    python3 mangaworld_downloader.py [name_of_manga]

- Call the script with the manga to research, follow the instruction on the screen and select a manga to download.
- Once selected the manga and press enter, wait the program to finish, don't worry (i have not implemented a bar yet).
- After the program finished, you will find in the same directory all the pdf separated in Volumes

# To implement
- Progress Bar
- Gui

# Windows User
I haven't tested this script on Windows, but i have used the os independent paths. So i think its gonna work.
