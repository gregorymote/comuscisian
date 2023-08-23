# Comuscisian

**Requirements:**

`pip install -r requirements.txt`

You also might have to 
`sudo apt install libasound-dev portaudio19-dev libportaudio2 libportaudiocpp0` (tested on Ubuntu)


Alternatively to pyaudio, you can use [sounddevice](https://python-sounddevice.readthedocs.io/en/0.3.15/installation.html) which might be more compatible with Windows/Mac
* just run `python3 -m pip install sounddevice`
* Tested on Ubuntu 18.04 with sounddevice version 0.3.15
* The code to switch between the two sound interfaces is in the `__init__` function of the Stream_Analyzer class

CMD Line to create loopback playback using pulse audio
`pacmd load-module module-loopback latency_msec=5`