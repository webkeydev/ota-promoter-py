# Ota-promoter-py

This is a python client implementation for ota-promoter server service.
With this tool you can update your MicroPython project on your running
devices. For more details visit the [ota-promoter-server](https://github.com/pappz/ota-promoter)

I tested this tool on ESP-8266 device.

## Example usage


```python
import otapromoter
from machine import reset


def ota_check():

    try:
        promoter = otapromoter.OTAPromoter('http://192.168.0.10:9090')
        if promoter.check_and_update():
            reset()
    except otapromoter.OTAException as e:
        print(e)
        return
    except OSError as e:
        print(e)
        return

if __name__ == '__main__':
    ota_check()
``` 
