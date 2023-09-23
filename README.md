# balance-scale-frontend-kivy

The frontend of a game based on Alice in Borderland, a TV show on Netflix. 

## Technology

Written in Python mainly using the asyncio library to handle communication with the server via websocket. I used the Kivy framework for GUI support and conversion to an Android app.

## Installation (for running the game)

Requires Python 3.10 and pip

[Check out how to install pip](https://pip.pypa.io/en/stable/installation/)

[Follow the Kivy installation guide](https://kivy.org/doc/stable/gettingstarted/installation.html)

Here are the commands for MacOS.

You need to create the venv outside of the project directory
```bash
python3.10 -m virtualenv venv
source venv/bin/activate
python -m pip install "kivy[base]" httpx websocket_client

```

## Running the game

```bash
source venv/bin/activate
python main.py
```
## Installation (for Android build)

First finish the normal installation.

I tried using Buildozer but there are too many errors. I used the hardcore python for android module instead.

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

I also modified `venv/lib/setuptools/_distutils/version.py` because there are .DS_Store files getting in the way creating an error.

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

```bash
p4a aab --private . --arch arm64-v8a --arch armeabi-v7a --permission android.permission.INTERNET --permission android.permission.ACCESS_NETWORK_STATE --package=com.kidprof.tenbin --name "Tenbin"  --bootstrap=sdl2 --requirements=python3,kivy,httpx,websocket_client,certifi,httpcore,idna,sniffio,anyio,exceptiongroup,h11 --orientation landscape --orientation landscape-reverse --icon assets/icon.png --presplash assets/background.jpg --blacklist-requirements=sqlite3,libffi,openssl --release --version 0.4.2
```

Signing app bundle:

```bash
jarsigner -keystore <key_location> <bundle_location> <key_alias>
```

APK for debug:

Remove `--release` flag and replace `aab` with `apk`.

Signing APKs:

```bash
$ANDROIDSDK/build-tools/34.0.0/zipalign -v -p 4 orig.apk aligned.apk
$ANDROIDSDK/build-tools/34.0.0/apksigner sign --ks ~/kidprof.jks --out signed.apk aligned.apk
```

Clean:

```bash
rm **/*.pyc
mv *.apk bin
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

Every player chooses a number between 0 and 100 in each round. The player closest to the target wins the round. The target would be the average of the numbers multiplied by 0.8. 

All players start with 0 points. If a player reaches -5 points, it is a GAME OVER for that player. The last person standing wins. 

A new rule will be introduced for every player eliminated.

### The new rules upon elimination

4 players remaining: If two or more players choose the same number, the number is invalid and all players who selected the number will lose a point.

3 players remaining: If a player chooses the exact correct number, they win the round and all other players lose two points.

2 players remaining: If someone chooses 0, a player who chooses 100 wins the round.

### FAQs

Q: I am confused after reading the rules.

A: You are not alone! The key to the game is that 0.8 multiplier. With that, it means that the target will never be above 80, as the average is at most 100. Then people should never choose a number above 80 to win. But if everyone thinks the same, they should not choose a number above 64, as the average will not go beyond 80. This creates a dilemma that leads to people choosing smaller and smaller numbers.

Q: I watched Alice in Borderland, are there any differences between your game and the game in the TV show?

A: Not much except for a few technicalities, and the fact that you don't die if you lose. This game is designed to recreate the game in Alice in Borderland, so that viewers can try it out for themselves. 

Here are the differences:

1. The round time is shortened to 2 minutes. 

2. The GAME OVER score is changed to -5.

3. Players can disconnect anytime, it counts as a GAME OVER for that player.

4. Players need to type in the number digit by digit.

The changes are mainly to address the fast lifestyle of people outside of the Borderland, and the fact that your screen is smaller than the one the TV show uses.

Q: Am I allowed to communicate?

A: Absolutely. That's what makes the game interesting. It is a shame that I do not have time to add communication features in-game. You are encouraged to communicate with your opponents during the game using other means.

Q: How do computer players behave?

A: Computer players will fill the game if there are no new joiners for 15 seconds. Or else I think there will never be a successful game being held. 

For the math nerds, they will choose a number at random (uniformly) between 0 and 100*0.8^(round-1). 

In other words, they would choose a number between 0 and 100 in the first round, then between 0 and 80, then between 0 and 64. I hope you get the idea.

When there are two players left the computer player would choose a number among 0, 1, and 100. 