# Open433

This project is an opensource usb 433Mhz rf transmitter / receiver based on an atmega328p the board uses a serial communication with a "packet" based systems (simples structs that are sent over the serial port).
The project has a basic but working implementation of a custom component for homeassistant  which is similar to the rpi_rf configuration)

See my blog articles on the implementation / creation of the project:

[https://blog.turtleforgaming.fr/open433-lets-turn-light-on-with-the-computer](https://blog.turtleforgaming.fr/open433-lets-turn-light-on-with-the-computer)

[https://blog.turtleforgaming.fr/creating-a-custom-component-for-homeassistant](https://blog.turtleforgaming.fr/creating-a-custom-component-for-homeassistant)

# Building the project

If you just got your own barebone pcbs you just need to flash the arduino bootloader to do that you can use any iscp programmer (or even "arduino as isp") for the bootloader I use the arduino uno bootloader the hardware is using an atmega328p running at 16MHz at 5V.
After that you just have to compile compile and upload the scketch in the arduino folder

# Using the project

## Using the library

If you don't use homeassistant you can see an example in the software folder.


## From homeassistant
If you want to use the board with homeassistant you need to create a `custom_components` folder in the homeassistant configuration directory (same one as the configuration.yaml) then you need to rename the `homeassistant_open433` to `open433` and put it in the `custom_components`.
Then after restarting the server you need to set the configure homeassistant to use the module:
```
open433:
  port: COM3
  speed: 9600 #(Optional default to 9600)
```
Then you can add switches like this:
```
switch:
  - platform: open433
    switches:
      KitchenLamp:
        code_on: 2523794944
        code_off: 2658012672
        protocol: 2 #(Optional default to 2)
        length: 32 #(Optional default to 32)
        signal_repetitions: 5 #(Optional default to 15)
        enable_receive: true #(Optional default to false) enable listening to incoming rf message of the switch codes
```
Or add binary sensors (with a possible timeout) like this:
```
binary_sensor:
  - platform: open433
    switches:
      inputA:
        code_on: 2389577216
        code_off: 2171473408
        protocol: 2 #(Optional default to 2)
        length: 32 #(Optional default to 32)
        on_timeout: 2 #(Optional 0 to turn off) Will turn off 2sec after receiving code_on, code_off will still be functional
```

An implementation of the light component has been done and can be used like this:
```
light:
  - platform: open433
    switches:
      BedSideLamp:
        levels:
          - brightness: 0
            code: 2658045484
          - brightness: 100
            code: 2523827756
        protocol: 2
        length: 32
        signal_repetitions: 5
        enable_receive: true
        force_levels: true
```
For this example, the entity KitchenLamp will send the code `2658045484` from brightness 0 to 99 and `2523827756` to 100 
The `force_levels` option allows the module to clamp homeassistant brightness slider to the specific value set in the config (ie. here sending the value 42 will go back to 0)
You can add multiple brightness stages with different codes, example:
```
- brightness: 0
  code: 2658045484
- brightness: 50
  code: 2926480940
- brightness: 100
  code: 2523827756
```
This will send the code `2658045484` from 0 to 49 , the code `2926480940` from 50 to 99 and the code `2523827756` at 100

You can also listen to events (open433_rx) to get received codes and send events to open433_tx with the following data to send an rf code:
```
code: 2658012672
protocol: 2
bitlength: 32
```

## Licences
- Software License: GPL v. 3
- Hardware License: CERN OHL v. 1.2
- Documentation License: CC BY-SA 4.0 International
