# balance-scale-frontend-kivy

The frontend of a game based on Alice in Borderland, a TV show on Netflix. 

## Technology

Written in Python mainly using the asyncio library to handle communication with the server via websocket.

## Installation (for running the game)

Requires Python 3.10 and pip

[Check out how to install pip](https://pip.pypa.io/en/stable/installation/)

[Follow the Kivy installation guide](https://kivy.org/doc/stable/gettingstarted/installation.html)

Here are the commands for MacOS.

```bash
python3.10 -m virtualenv venv
source venv/bin/activate
python -m pip install "kivy[base]" httpx websocket_client

```

## Installation (for Android build)

First finish the normal installation.

Documentation for p4a:

https://python-for-android.readthedocs.io/en/latest/quickstart/?highlight=archs

```bash
pip install python-for-android

brew install autoconf automake libtool openssl pkg-config
brew tap homebrew/cask-versions
brew install --cask homebrew/cask-versions/adoptopenjdk8

python -m pip install --upgrade Cython==0.29.36 virtualenv
```

In `.zshrc`:

```bash
# Android
export ANDROIDSDK="$HOME/Library/Android/sdk"
export ANDROIDNDK="$HOME/Library/Android/sdk/ndk/25.2.9519653"
export ANDROIDAPI="34"  # Target API version of your application
export NDKAPI="21"  # Minimum supported API version of your application
```

Remember to `source ~/.zshrc`

I also mofified `venv/lib/setuptools/_distutils/version.py` because there are .DS_Store files getting in the way creating an error.

```python
def _cmp(self, other):
    if isinstance(other, str):
        other = LooseVersion(other)
    elif not isinstance(other, LooseVersion):
        return NotImplemented

    print(str(self),str(self)== ".DS_Store")
    print(str(other),str(other) == ".DS_Store")
    if str(self) == ".DS_Store" or str(other) == ".DS_Store":
        return 0
    if self.version == other.version:
        return 0
    if self.version < other.version:
        return -1
    if self.version > other.version:
        return 1
```


## Build for Android

Using buildozer 

Docs:

https://kivy.org/doc/stable/guide/packaging-android.html#packaging-android

https://buildozer.readthedocs.io/en/latest/installation.html#targeting-android

(BUT please use cython version 0.29.36 instead)

https://buildozer.readthedocs.io/en/latest/quickstart.html

```bash
p4a apk --private . --arch arm64-v8a --arch armeabi-v7a --permission INTERNET --permission ACCESS_NETWORK_STATE --package=com.kidprof.tenbin --name "Tenbin" --version 0.2.2 --bootstrap=sdl2 --requirements=python3,kivy,httpx,websocket_client,certifi,httpcore,idna,sniffio,anyio,exceptiongroup,h11 
```

```bash
--orientation landscape --orientation landscape-reverse
```

View logs:
```bash
$ANDROIDSDK/platform-tools/adb logcat | grep python
```

## Installation for Windows/MacOS build

```bash
pip install pyinstaller
```

## Build for Windows/MacOS

```bash
pyinstaller main.spec
```

## Game Rules

*Copied from [Alice in Borderland Fandom](https://aliceinborderland.fandom.com/wiki/King_of_Diamonds_(Netflix)) 

### Rules

Player limit: 5

Time limit: 3 minutes per round (no round limit)

All players start with 0 points.

Each player has a tablet in front of them containing a number grid with numbers 0 to 100.

In each round, the player must select a number from the grid.

Once all numbers are selected, the average will be calculated, then multiplied by 0.8.
The player closest to the number wins the round. The other players each lose a point. 

If a player reaches -10 points, it is a GAME OVER for that player.

A new rule will be introduced for every player eliminated.

4 players remaining: If two or more players choose the same number, the number is invalid and all players who selected the number will lose a point.

3 players remaining: If a player chooses the exact correct number, they win the round and all other players lose two points.

2 players remaining: If someone chooses 0, a player who chooses 100 automatically wins the round.

It is GAME CLEAR for the last remaining player.