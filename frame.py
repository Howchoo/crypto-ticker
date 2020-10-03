import time
import sys

from rgbmatrix import RGBMatrix, RGBMatrixOptions


class Frame:
    def __init__(self, *args, **kwargs):
        self.args = {}
        self.args['led_rows'] = kwargs.get('led_rows', 32)
        self.args['led_cols'] = kwargs.get('led_cols', 64)
        self.args['led_chain'] = kwargs.get('led_chain', 1)
        self.args['led_parallel'] = kwargs.get('led_parallel', 1)
        self.args['led_pwm_bits'] = kwargs.get('led_pwm_bits', 11)
        self.args['led_brightness'] = kwargs.get('led_brightness', 100)
        self.args['led_gpio_mapping'] = kwargs.get('led_gpio_mapping', 'adafruit-hat')
        self.args['led_scan_mode'] = kwargs.get('led_scan_mode', 1)
        self.args['led_pwm_lsb_nanoseconds'] = kwargs.get('led_pwm_lsb_nanoseconds', 130)
        self.args['led_show_refresh'] = kwargs.get('led_show_refresh', False)
        self.args['led_slowdown_gpio'] = kwargs.get('led_slowdown_gpio', 1)
        self.args['led_no_hardware_pulse'] = kwargs.get('led_no_hardware_pulse', False)  # double check
        self.args['led_rgb_sequence'] = kwargs.get('led_rgb_sequence', 'RGB')
        self.args['led_pixel_mapper'] = kwargs.get('led_pixel_mapper', '')
        self.args['led_row_addr_type'] = kwargs.get('led_row_addr_type', 0)
        self.args['led_multiplexing'] = kwargs.get('led_multiplexing', 0)
        self.args['led_panel_type'] = kwargs.get('led_panel_type', '')

    def usleep(self, value):
        time.sleep(value / 1000000.0)

    def run(self):
        print('Running')

    def process(self):
        options = RGBMatrixOptions()

        if self.args['led_gpio_mapping'] is not None:
            options.hardware_mapping = self.args['led_gpio_mapping']

        options.rows = self.args['led_rows']
        options.cols = self.args['led_cols']
        options.chain_length = self.args['led_chain']
        options.parallel = self.args['led_parallel']
        options.row_address_type = self.args['led_row_addr_type']
        options.multiplexing = self.args['led_multiplexing']
        options.pwm_bits = self.args['led_pwm_bits']
        options.brightness = self.args['led_brightness']
        options.pwm_lsb_nanoseconds = self.args['led_pwm_lsb_nanoseconds']
        options.led_rgb_sequence = self.args['led_rgb_sequence']
        options.pixel_mapper_config = self.args['led_pixel_mapper']
        options.panel_type = self.args['led_panel_type']

        if self.args['led_show_refresh']:
            options.show_refresh_rate = 1

        if self.args['led_slowdown_gpio'] is not None:
            options.gpio_slowdown = self.args['led_slowdown_gpio']

        if self.args['led_no_hardware_pulse']:
            options.disable_hardware_pulsing = True

        self.matrix = RGBMatrix(options=options)

        try:
            print('Press CTRL-C to stops')
            self.run()
        except KeyboardInterrupt:
            print('Exiting\n')
            sys.exit(0)

        return True
