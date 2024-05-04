import os
import time

import requests
import tinytuya
from dotenv import load_dotenv

load_dotenv()

TEMP_SENSOR_URL = os.getenv('TEMP_SENSOR_URL')
TUYA_DEVICE_ID = os.getenv('TUYA_DEVICE_ID')
TUYA_LOCAL_KEY = os.getenv('TUYA_LOCAL_KEY')
TUYA_ADDRESS = os.getenv('TUYA_ADDRESS')
MIN_TEMPERATURE = float(os.getenv('MIN_TEMPERATURE', 10))
MAX_TEMPERATURE = float(os.getenv('MAX_TEMPERATURE', 50))
COLD_COLOR = tuple(float(x) for x in os.getenv('COLD_COLOR', '0,0,255').split(','))
MID_COLOR = tuple(float(x) for x in os.getenv('MID_COLOR', '255,204,0').split(','))
HOT_COLOR = tuple(float(x) for x in os.getenv('HOT_COLOR', '255,0,0').split(','))
UPDATE_INTERVAL = float(os.getenv('UPDATE_INTERVAL', 60))

print(f'{TEMP_SENSOR_URL=}')
print(f'{TUYA_DEVICE_ID=}')
print(f'{TUYA_LOCAL_KEY=}')
print(f'{TUYA_ADDRESS=}')
print(f'{MIN_TEMPERATURE=}')
print(f'{MAX_TEMPERATURE=}')
print(f'{COLD_COLOR=}')
print(f'{MID_COLOR=}')
print(f'{HOT_COLOR=}')
print(f'{UPDATE_INTERVAL=}')


def scale_color(value, low_color, high_color):
    return (value * (high_color[0] - low_color[0]) + low_color[0],
            value * (high_color[1] - low_color[1]) + low_color[1],
            value * (high_color[2] - low_color[2]) + low_color[2])


def generate_color(temp):
    t_scaled = (temp - MIN_TEMPERATURE) / (MAX_TEMPERATURE - MIN_TEMPERATURE)
    if t_scaled < 0.5:
        return scale_color(t_scaled * 2, COLD_COLOR, MID_COLOR)
    else:
        return scale_color((t_scaled - 0.5) * 2, MID_COLOR, HOT_COLOR)


def fetch_temperature():
    data = requests.get(TEMP_SENSOR_URL).json()
    return data['temperature']


def build_led_strip():
    return tinytuya.BulbDevice(
        dev_id=TUYA_DEVICE_ID,
        address=TUYA_ADDRESS,
        local_key=TUYA_LOCAL_KEY,
        version=3.3
    )


def main():
    led_strip = build_led_strip()

    status = led_strip.status()
    print(f'Connected to led strip at {TUYA_ADDRESS}. Status: ${status}')

    print(f'Updating led strip color according to temperature every {UPDATE_INTERVAL} seconds.')
    while True:
        try:
            status = led_strip.status()
            if status is None or status['dps'] is None or status['dps']['21'] is None:
                print('Status is None! Rebuilding led strip.')
                led_strip.close()
                led_strip = build_led_strip()
            else:
                temp = fetch_temperature()

                current_mode = status['dps']['21']
                if current_mode == 'colour':
                    print(f'Updating color. {temp=}')
                    r, g, b = generate_color(temp)
                    led_strip.set_colour(r, g, b)
                else:
                    print(f'Mode isn\'t colour but {current_mode}, not updating color. {temp=}')
        except Exception as e:
            print(f'Error performing update! {e}')

        time.sleep(UPDATE_INTERVAL)


if __name__ == '__main__':
    main()
