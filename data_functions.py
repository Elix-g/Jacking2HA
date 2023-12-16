from dataclasses import fields
from mdata import Mdata


class DataFunctions():
    """ Container for data and functions"""

    def _abbr(self, source: dict) -> dict:
        rVal = {}
        try:
            for key, value in source.items():
                try:
                    abbr = Mdata.mqttAbbr[key]
                    newValue = \
                        self._abbr(value) if isinstance(value, dict) else value
                    rVal.setdefault(abbr, newValue)
                except KeyError:
                    rVal.setdefault(key, value)
        except AttributeError:
            pass
        return rVal

    def _analyze(self) -> None:
        attType = self.attType_
        ccuType = self.ccuType_
        keyType = self.keyType_
        writable = self.writable_
        rVal = {}

        match ccuType, attType, writable, keyType:
            case _, 'ACTION', _, _:
                rVal = {'command_template': Mdata.cTemplate,
                        'haType_': 'button',
                        'payload_press': True,
                        'state_topic': None,
                        'value_template': None}

            case 'device', 'BOOL', _, 'STATE':
                rVal = {'haType_': 'binary_sensor',
                        'payload_on': True,
                        'payload_off': False,
                        'value_template': Mdata.vTemplateBinary}

            case 'device', 'BOOL', False, _:
                rVal = {'haType_': 'binary_sensor',
                        'payload_on': True,
                        'payload_off': False,
                        'value_template': Mdata.vTemplateBinary}

            case 'device', 'BOOL', True, _:
                rVal = {'haType_': 'switch',
                        'payload_on': True,
                        'payload_off': False,
                        'value_template': Mdata.vTemplateBinary}

            case 'device', 'ENUM', _, 'VALVE_STATE':
                rVal = {'haType_': 'binary_sensor',
                        'suggested_display_precision': 0}

            case 'device', 'ENUM', _, 'STATE' | 'WINDOW_STATE':
                rVal = {'device_class': 'opening',
                        'haType_': 'binary_sensor',
                        'payload_off': False,
                        'payload_on': True,
                        'value_template': Mdata.vTemplateBinary}

            case 'device', 'ENUM', _, _:
                rVal = {'haType_': 'binary_sensor'}

            case 'device', 'FLOAT', _, 'LEVEL':
                rVal = {'haType_': 'sensor',
                        'suggested_display_precision': 0,
                        'unit_of_measurement': '%',
                        'value_template': Mdata.vTemplateLevel}

            case 'device', 'FLOAT', _, 'SETPOINT' | 'SET_POINT_TEMPERATURE':
                rVal = {'command_template': Mdata.cTemplate,
                        'device_class': 'temperature',
                        'haType_': 'number',
                        'step': 0.5}

            case 'device', 'FLOAT', False, _:
                rVal = {'haType_': 'sensor',
                        'suggested_display_precision': 1}

            case 'device', 'FLOAT', True, _:
                rVal = {'haType_': 'number',
                        'step': 0.5}

            case 'device', 'INTEGER', False, _:
                rVal = {'haType_': 'sensor',
                        'suggested_display_precision': 0}

            case 'device', 'INTEGER', True, _:
                if isinstance(self.max, int) and self.max < 10:
                    haType = 'select'
                    options = [str(item) for item in
                               range(self.min, self.max + 1)]
                    cTemplate = Mdata.cTemplate
                else:
                    haType, options, cTemplate = \
                        'sensor', None, None
                rVal = {'command_template': cTemplate,
                        'haType_': haType,
                        'options': options}

            case 'device', 'STRING', _, _:
                rVal = {'haType_': 'sensor'}

            case 'program', _, _, _:
                rVal = {'command_template': Mdata.cTemplatePrg,
                        'json_attributes_topic': self.state_topic,
                        'json_attributes_template': Mdata.jTemplateTs,
                        'state_topic': None,
                        'haType_': 'button',
                        'value_template': None}

            case 'sysvar', 'ALARM' | 'BOOL', _, _:
                rVal = {'haType_': 'switch',
                        'payload_off': '{"v": false}',
                        'payload_on': '{"v": true}',
                        'state_off': False,
                        'state_on': True}

            case 'sysvar', 'FLOAT', _, _:
                rVal = {'command_topic': None,
                        'haType_': 'sensor',
                        'suggested_display_precision': 1}

            case 'sysvar', 'STRING', _, _:
                rVal = {'command_topic': None,
                        'haType_': 'sensor'}

        match keyType:
            case 'ACTUAL_TEMPERATURE' | 'TEMPERATURE':
                rVal.update({'device_class': 'temperature'})

            case 'HUMIDITY':
                rVal.update({'device_class': 'humidity',
                             'suggested_display_precision': 1,
                             'unit_of_measurement': '%'})

            case 'LEVEL':
                rVal.update({'haType_': 'sensor'})

            case 'LOW_BAT' | 'LOWBAT':
                rVal.update({'device_class': 'battery'})

            case 'BATTERY_STATE' | 'OPERATING_VOLTAGE':
                rVal.update({'device_class': 'voltage',
                             'unit_of_measurement': 'V'})

            case 'RSSI_DEVICE' | 'RSSI_PEER':
                rVal.update({'device_class': 'signal_strength',
                             'unit_of_measurement': 'dBm'})

            case 'SMOKE_DETECTOR_ALARM_STATUS':
                rVal.update({'haType_': 'sensor',
                             'value_template': Mdata.vTemplateSdas})

            case 'SMOKE_DETECTOR_TEST_RESULT':
                rVal.update({'haType_': 'sensor',
                             'value_template': Mdata.vTemplateSdtr})

            case 'TIME_OF_OPERATION':
                rVal.update({'haType:': 'sensor',
                             'suggested_display_precision': None,
                             'value_template': Mdata.vTemplateToo})

        for key, value in rVal.items():
            setattr(self, key, value)

    @property
    def _items_(self) -> dict:
        rVal = {}
        if self.deleted_:
            return None
        for att in [x for x in fields(self) if not x.name.endswith('_')
                    and self.get(x.name) not in (None, '', '-', '""')]:
            rVal.setdefault(att.name, self.get(att.name))
        return dict(sorted(rVal.items()))

    @property
    def _items_debug(self) -> dict:
        rVal = {}
        for att in fields(self):
            rVal.setdefault(att.name, self.get(att.name))
        return dict(sorted(rVal.items()))

    def get(self, field_: str) -> any:
        return getattr(self, field_, None)

    def for_json(self):
        return self._items_debug if self._debug_ else self._items_

    def for_mqtt(self) -> dict:
        return self._abbr(self._items_) if self._abbr_ else self._items_

    def update(self, updtValue: any) -> None:
        if isinstance(updtValue, dict):
            for key, value in updtValue.items():
                setattr(self, key, value)
        elif isinstance(updtValue, str) and updtValue == '-':
            self.deleted_ = True
