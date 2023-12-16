class Mdata():
    """ Container holding static data """

    availability = {
        'payload_available': False,
        'payload_not_available': True,
        'value_template': '{{ value_json.v|bool }}'
    }
    cTemplate = '{"v": {{ value }} }'
    cTemplatePrg = '{"v": true}'
    diag = ('BATTERY_STATE',
            'BURST_LIMIT_WARNING',
            'CONFIG_PENDING',
            'DUTY_CYCLE',
            'ERROR_DEGRADED_CHAMBER',
            'LEVEL', 'LOW_BAT',
            'OPERATING_VOLTAGE',
            'RSSI_DEVICE', 'RSSI_PEER',
            'SMOKE_DETECTOR_ALARM_STATUS',
            'SMOKE_DETECTOR_TEST_RESULT',
            'TIME_OF_OPERATION')
    jTemplateTs = '{% set ts=value_json.ts|int %}{{ {"lang15": iif(' + \
                  'ts==0, "lang16", (ts/1000)|timestamp_local(), "n' + \
                  '/a")}|to_json() }}'
    lang = {
        'lang0': ('off', 'ein'),
        'lang1': ('primary', 'primär'),
        'lang2': ('intrusion', 'Eindringling'),
        'lang3': ('secondary', 'sekundär'),
        'lang4': ('alarm', 'Alarm'),
        'lang5': ('n/a', 'n/a'),
        'lang6': ('smoke test ok', 'Rauchtest ok'),
        'lang7': ('smoke test fail', 'Rauchtestfehler'),
        'lang8': ('connection test started', 'Verbindungstest gestartet'),
        'lang9': ('connection test ok', 'Verbindungstest ok'),
        'lang10': ('days', 'Tage'),
        'lang11': ('no', 'nein'),
        'lang12': ('yes', 'ja'),
        'lang13': ('System Variables', 'Systemvariablen'),
        'lang14': ('Programs', 'Programme'),
        'lang15': ('Last run', 'Zuletzt ausgeführt'),
        'lang16': ('never', 'nie')
    }
    langTr = [
        [0, 1, 2, 3, 4],
        [5, 6, 7, 8, 9],
        [10],
        [11, 12],
        [13],
        [14],
        [15, 16]
    ]
    mqttAbbr = {
        'availability_template': 'avty_tpl',
        'availability_topic': 'avty_t',
        'availability': 'avty',
        'command_template': 'cmd_tpl',
        'command_topic': 'cmd_t',
        'configuration_url': 'cu',
        'device_class': 'dev_cla',
        'device': 'dev',
        'entity_category': 'ent_cat',
        'hw_version': 'hw',
        'icon': 'ic',
        'json_attributes_topic': 'json_attr_t',
        'json_attributes_template': 'json_attr_tpl',
        'identifiers': 'ids',
        'manufacturer': 'mf',
        'model': 'mdl',
        'mode': 'mode',
        'object_id': 'obj_id',
        'origin': 'o',
        'payload_available': 'pl_avail',
        'payload_not_available': 'pl_not_avail',
        'payload_off': 'pl_off',
        'payload_on': 'pl_on',
        'payload_open': 'pl_open',
        'payload_press': 'pl_prs',
        'state_template': 'stat_tpl',
        'state_topic': 'stat_t',
        'state_value_template': 'stat_val_tpl',
        'subtype': 'stype',
        'suggested_area': 'sa',
        'suggested_display_precision': 'sug_dsp_prc',
        'support_url': 'url',
        'sw_version': 'sw',
        'topic': 't',
        'unique_id': 'uniq_id',
        'unit_of_measurement': 'unit_of_meas',
        'value_template': 'val_tpl'
    }
    origin = {
        'name': 'Jacking2Ha',
        'sw_version': '0.1.1',
        'support_url': 'https://github.com/elix-g/jacking2ha'
    }
    vTemplate = '{{ value_json.v }}'
    vTemplateBinary = '{{ value_json.v|bool }}'
    vTemplateLevel = '{{ value_json.v|float * 100 }}'
    vTemplateSdas = '{% set text = value_json.v|string|regex_replace(fin' + \
                    'd="0", replace="lang0")|regex_replace(find="1", rep' + \
                    'lace="lang1")|regex_replace(find="2", replace="lang' + \
                    '2")|regex_replace(find="3", replace="lang3") %}lang' + \
                    '4 {{ text }}'
    vTemplateSdtr = '{% set text = value_json.v|string|regex_replace(fin' + \
                    'd="0", replace="lang5")|regex_replace(find="1", rep' + \
                    'lace="lang6")|regex_replace(find="2", replace="lang' + \
                    '7")|regex_replace(find="3", replace="lang8")|regex_' + \
                    'replace(find="4", replace="lang9") %}{{ text }}'
    vTemplateToo = '{{ (value_json.v|int / 86400)|int }} lang10'
