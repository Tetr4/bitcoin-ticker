# Bitcoin Ticker
Display [bitcoin.de](https://www.bitcoin.de) exchange rate on the [PaPiRus](https://github.com/PiSupply/PaPiRus) ePaper display with Raspberry Pi.

<p align="center">
  <img width="460" src="https://user-images.githubusercontent.com/3826929/29338946-0b44f320-8218-11e7-826c-b3070eb061d8.jpg">
</p>

## Auto Startup
1. Install `screen`:
```sh
sudo apt-get install screen
```

2. Create a startup script at `/home/pi/startup`:
```sh
#!/usr/bin/env bash
# run ticker in a screen
screen -dmS ticker /home/pi/bitcoin-ticker/ticker.py
```

3. Add the following line to `/etc/rc.local` just before `exit 0`:
```sh
# Run startup script as user pi
su - pi /home/pi/startup
```

4. Restart the Pi with `sudo reboot`.

After connecting (`ssh pi@raspberrypi.local`), you can check that the screen is running with `screen -ls`.  
You can attach to it with `screen -r` and detach with `ctrl+a` and then `d`.
