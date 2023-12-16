#!/usr/bin/env python3

""" Jacking2Ha """

import argparse
import queue
import ssl
import sys

from os import path
from random import randint
from textwrap import TextWrapper
from threading import Event, Thread
from traceback import format_exception

import arrow
import paho.mqtt.client as pahomqtt
import requests
import simplejson as json
import yaml

from data_holder import DataHolder
from mdata import Mdata


class Jacking2Ha:
    """ Module Jacking2Ha """

    class _DumperNoAlias(yaml.CSafeDumper):
        """ CSafeDumper to suppress aliases/anchors """

        def ignore_aliases(self, data) -> bool:
            return True

    _automations = []
    _ccuJackSession = None
    _config = {}
    _customization = {}
    _detection = {}
    _devCount = 0
    _entCount = 0
    _inputButtons = []
    _itemFilter = {}
    _loopControl = Event()
    _mqttClient = None
    _toMqtt = queue.Queue(maxsize=0)

    def __init__(self, configFile: str):
        self._config = self._read_config(configFile)

    def __call__(self, mode: str):
        config = self._config
        self._ccuJackSession = self._init_jack()

        if mode == 'mqtt':
            for job in config.get('readJobs'):
                match job:
                    case 'device' | 'virtdev':
                        update = self._read_jack_devices(job)
                        self._detection.update(update)
                    case 'program' | 'sysvar':
                        update = self._read_jack_sysvar(job)
                        self._detection.update(update)
            self._devCount = len(self._detection)
            self._ccuJackSession.close()

            if config.get('customize'):
                self._detection = self._customize(detection=self._detection,
                                                  custom=self._customization)

            if config.get('enumerateRcButtons'):
                self._detection = self._enum_rc_buttons(self._detection)

            if config.get('miscEntities'):
                self._automations, self._inputButtons = \
                    self._create_misc_entities(self._detection)

            fileDate = arrow.now().format('YYYYMMDD_HHmmss')
            for job in config.get('outputJobs'):
                match job:
                    case 'mqtt':
                        self._init_mqtt()
                        self._output_mqtt(self._detection)
                    case 'json':
                        fileName = f'results_{fileDate}.json'
                        self._output_json(self._detection, fileName)
                    case 'yaml':
                        fileName = f'mqtt_{fileDate}.yaml'
                        self._output_yaml(self._detection, fileName)
                        fileName = f'automations_{fileDate}.yaml'
                        self._output_yaml(input=self._automations,
                                          fileName=fileName,
                                          mode='automations')
                        fileName = f'input_buttons_{fileDate}.yaml'
                        self._output_yaml(input=self._inputButtons,
                                          fileName=fileName,
                                          mode='inputButtons')
            print(f'\n{self._devCount} Homematic devices with ' +
                  f'{self._entCount} entities detected and processed\n')
        else:
            modes = ['device', 'program', 'sysvar'] \
                if mode == 'all' else [mode]
            outputJobs = []
            if 'device' in modes:
                update = self._read_jack_devices('device')
                self._detection.update(update)
                update = self._read_jack_devices('virtdev')
                self._detection.update(update)
                outputJobs.append('device')
            for mode in [x for x in modes if x != 'device']:
                update = self._read_jack_sysvar(mode)
                self._detection.update(update)
                outputJobs.append(mode)
            for job in outputJobs:
                match job:
                    case 'device':
                        self._output_table_device(self._detection, job)
                    case 'program' | 'sysvar':
                        input = self._detection.get(job)['0']
                        self._output_table_sysvar(input, job)

    def _create_misc_entities(self, input: dict) -> tuple:
        print('Creating automations...', end='')
        automations, inputButtons = [], []
        for type_ in ('program', 'sysvar'):
            actions = []
            id = randint(1000000000000, 2000000000000)
            trigger = [{'platform': 'state',
                        'entity_id': f'input_button.update_{type_}'}]
            for entry in input.get(type_)['0']:
                data = {'qos': 0,
                        'retain': False,
                        'topic': entry.getTopic_,
                        'payload': ''}
                actions.append({'service': 'mqtt.publish',
                                'data': data})
            if len(actions):
                automations.append({'id': f'{id}',
                                    'alias': f'Update {type_}',
                                    'description': '',
                                    'trigger': trigger,
                                    'condition': [],
                                    'action': actions,
                                    'mode': 'single'})
                inputButtons.append(
                    {f'update_{type_}': {'name': f'Update {type_}'}})
        print('done')
        return (automations, inputButtons)

    def _customize(self, detection: dict, custom: dict) -> dict:
        print('Applying user customizations...', end='')
        for cDev, cChans in custom.items():
            if cChans in ('-', None):
                detection[cDev] = None
                continue
            for (dev, chans) in [(d, c) for (d, c) in detection.items()
                                 if cDev in (d, '~all')]:
                for cChan, cEntries in cChans.items():
                    if cEntries in ('-', None):
                        detection[cDev][cChan] = None
                        continue
                    for (chan, entries) in [(ch, en) for (ch, en) in
                                            chans.items() if cChan in
                                            (ch, '~all')]:
                        for cKeyType, cValues in cEntries.items():
                            for entry in [ent for ent in entries if
                                          cKeyType in (ent.keyType_, '~all')]:
                                entry.update(cValues)
        rVal = {}
        for (dev, chans) in [(d, c) for (d, c) in detection.items()
                             if c is not None]:
            channel = {}
            for (chan, entries) in [(ch, en) for (ch, en) in chans.items()
                                    if en is not None]:
                channel.update({chan: entries})
            rVal.update({dev: channel})
        print('done')
        return rVal

    def _enum_rc_buttons(self, detection: dict) -> dict:
        print('Enumerating Rc Buttons...', end='')
        for dev, channels in detection.items():
            pLCount, pSCount = 0, 0
            for channel, entries in channels.items():
                for entry in [x for x in entries if
                              x.keyType_ == 'PRESS_LONG']:
                    pLCount += 1
                for entry in [x for x in entries if
                              x.keyType_ == 'PRESS_SHORT']:
                    pSCount += 1
            for channel, entries in channels.items():
                for entry in [x for x in entries if (x.keyType_ == 'PRESS_LONG'
                              and pLCount > 1) or (x.keyType_ ==
                              'PRESS_SHORT' and pSCount > 1)]:
                    entry.name = f'{entry.name} {int(entry.channel_):02d}'
        print('done')
        return detection

    def _http_get(self, urlPart: str, filter_='', attempts=1) -> dict:
        baseUrl = self._config['ccuJackUrl']
        url = f'{baseUrl}{urlPart}'
        try:
            r = self._ccuJackSession.get(url)
        except Exception as e:
            msg = ''.join(format_exception(None, e, e.__traceback__))
            print(f'\nWeb Request Error while opening {url}:\n\n{msg}\n')
            sys.exit(1)
        if r.ok:
            return r.json().get(filter_) if len(filter_) else r.json()
        if r.status_code == 404:
            return {}
        if attempts > 3:
            print(f'\nImpossible to establish a connection to {url}.\n')
            sys.exit(1)
        attempts += 1
        print(f'\nWaiting for response from {url}.\n')
        Event().wait(timeout=300)
        if r.status_code == 401:
            self._ccuJackSession = self._init_jack()
        return self._http_get(urlpart=urlPart,
                              filter_=filter_,
                              attempts=attempts)

    def _init_jack(self) -> requests.session:
        sess = requests.Session()
        url = self._config.get('ccuJackUrl')
        sess.auth = (self._config.get('ccuJackUser'),
                     self._config.get('ccuJackPass'))
        if self._config.get('jackSsl'):
            sess.verify = self._config.get('ccuJackCaCert')
        r = sess.get(f'{url}/~vendor')
        if not r.ok:
            print(f'\nCannot establish connection to {url}.\n')
            sys.exit(1)
        try:
            if r.json().get('serverName') != 'CCU-Jack':
                raise ValueError
        except (KeyError, ValueError):
            print('\nNo CCU-Jack VEAP server detected.\n')
            sys.exit(1)
        return sess

    def _init_mqtt(self, secure=True) -> None:
        mqtt = pahomqtt.Client(client_id='jacking2ha',
                               transport='tcp',
                               protocol=pahomqtt.MQTTv311)
        mqtt.username_pw_set(username=self._config['mqttUser'],
                             password=self._config['mqttPass'])
        if secure:
            mqtt.tls_set(ca_certs=self._config['mqttCaCert'],
                         cert_reqs=ssl.CERT_REQUIRED,
                         ciphers=None,)
            try:
                mqtt.connect(host=self._config['mqttHost'],
                             port=self._config['mqttPort'],
                             keepalive=60)
            except Exception:
                self._init_mqtt(secure=False)
        else:
            try:
                mqtt.connect(host=self._config['mqttHost'],
                             port=self._config['mqttPort'],
                             keepalive=60)
            except Exception as e:
                msg = ''.join(format_exception(None, e, e.__traceback__))
                print(f'\nFailed to connect to MQTT broker:\n\n{msg}\n')
                sys.exit(1)
        mqtt.loop_start()
        self._mqttClient = mqtt

    def _output_json(self, input: dict, fileName: str) -> None:
        print('Writing json file...', end='')
        filePath = self._config.get('outputPath')
        path_ = path.join(filePath, fileName)
        try:
            with open(path_, 'w') as outfile:
                outfile.write(json.dumps(obj=input,
                                         for_json=True,
                                         indent=4,
                                         sort_keys=True))
        except Exception as e:
            msg = ''.join(format_exception(None, e, e.__traceback__))
            print(f'failed:\n\n{msg}\n')
            return
        print('done')

    def _output_mqtt(self, input: dict) -> None:
        print('Output to MQTT server...', end='')
        threadQueueWorker = Thread(target=self._queue_worker,
                                   daemon=False)
        for device, channels in input.items():
            for channelNum, (channel, entries) in enumerate(channels.items()):
                for entryNum, entry in enumerate(entries):
                    if (channelNum == 0 and entryNum > 1) or channelNum > 1:
                        entry.device = {'identifiers': [device]}
                    topic = entry.discTopic_
                    payload = json.dumps(entry.for_mqtt()).encode()
                    self._toMqtt.put_nowait([topic, payload])
        threadQueueWorker.start()
        self._toMqtt.join()
        self._loopControl.clear()
        print('done')

    def _output_table_device(self, input: dict, type: str) -> None:
        output = []
        print('\n\n')
        for (devices, channels) in [(d, c) for (d, c) in input.items()
                                    if d not in ('program', 'sysvar')]:
            atts = []
            for channel, entries in channels.items():
                dev, id = \
                    entries[0].device, entries[0].ident_
                for entry in entries:
                    atts.append(entry.keyType_)
            output.append([id, dev['model'], dev['name'], sorted(atts)])
        twrap = TextWrapper(width=60,
                            break_long_words=False,
                            initial_indent=' |    ',
                            subsequent_indent=' |    ')
        for ent in sorted(output, key=lambda x: x[0]):
            attr = twrap.fill(', '.join(list(set(ent[3]))))
            print(f' |  {ent[0]:<14s}   {ent[1]:<15s}   {ent[2]}')
            print(f' |{"-" * 69}\n{attr}\n\n')

    def _output_table_sysvar(self, input: dict, type: str) -> None:
        output = []
        print(f'\n |  {"ID":<4s}    {type}\n |{"-" * 55}')
        for entry in input:
            id = entry.ident_.replace(type, '')
            output.append((id, entry.name))
        for entry in sorted(output, key=lambda x: int(x[0])):
            print(f' |  {entry[0]:<4s}    {entry[1]}')
        print('\n')

    def _output_yaml(self,
                     input: dict,
                     fileName: str,
                     mode='mqtt') -> None:
        print(f'Writing {mode} yaml file...', end='')
        output = []
        match mode:
            case 'mqtt':
                for device, channels in input.items():
                    for channel, entries in channels.items():
                        for entry in [x for x in entries if x is not None]:
                            try:
                                output.append({entry.haType_: entry._items_})
                            except AttributeError:
                                output.append({device: entry})
            case _:
                output = input

        filePath = self._config.get('outputPath')
        outputFile = path.join(filePath, fileName)
        try:
            with open(outputFile, 'wt', encoding='utf-8') as outfile:
                for entry in output:
                    yaml.dump(data=[entry],
                              stream=outfile,
                              Dumper=self._DumperNoAlias,
                              indent=3,
                              allow_unicode=True,
                              encoding='utf-8',
                              sort_keys=False)
                    outfile.write('\n')
        except Exception as e:
            msg = ''.join(format_exception(None, e, e.__traceback__))
            print(f'failed:\n\n{msg}\n')
            sys.exit(1)
        print('done')

    def _queue_worker(self) -> None:
        self._loopControl.set()
        while self._loopControl.is_set():
            try:
                data = self._toMqtt.get_nowait()
            except queue.Empty:
                Event().wait(timeout=.5)
                continue
            topic, payload = data
            self._mqttClient.publish(topic=topic,
                                     payload=payload,
                                     qos=1,
                                     retain=True)
            self._toMqtt.task_done()

    def _read_config(self, configFile: str) -> dict:
        print('Reading config file...', end='')
        filePath = path.dirname(path.abspath(__file__))
        if ('/' or '\\') not in configFile:
            configFile = path.join(filePath, configFile)
        outputPath = path.join(filePath, '_output')
        try:
            with open(file=configFile,
                      mode='r',
                      encoding='utf-8') as infile:
                content = json.load(fp=infile)
        except json.errors.JSONDecodeError as e:
            msg = ''.join(format_exception(None, e, e.__traceback__))
            print(f'failed while parsing:\n\n{msg}\n')
            sys.exit(1)
        except Exception as e:
            msg = ''.join(format_exception(None, e, e.__traceback__))
            print(f'failed:\n\n{msg}\n')
            sys.exit(1)

        try:
            config = content['config']
            confUrl = config['ccuJackUrl']
            confUrlP = confUrl.split(':')
            confUrl = f'{confUrlP[0]}:{confUrlP[1]}'
            customization = content.get('customization')
            itemFilter = content['itemFilter']

            jackSsl = True in [len(config['ccuJackCaCert']) > 0,
                               confUrl.startswith('https'),
                               confUrl.endswith('2122')]
            mqttPort = int(config['mqttPort'])

            readJobs = []
            if config['ccuJackReadDevice']:
                readJobs.append('device')
            if config['ccuJackReadProgram']:
                readJobs.append('program')
            if config['ccuJackReadSysvar']:
                readJobs.append('sysvar')
            if config['ccuJackReadVirtdev']:
                readJobs.append('virtdev')
            if not len(readJobs):
                raise ValueError

            outputJobs = []
            if config['outputToJson']:
                outputJobs.append('json')
            if config['outputToMqtt']:
                outputJobs.append('mqtt')
            if config['outputToYaml']:
                outputJobs.append('yaml')
            if not len(outputJobs):
                raise ValueError

            miscEntities = False not in [config['createMiscEntities'],
                                         ('program' or 'sysvar') in readJobs]
            customize = True

        except (KeyError, ValueError):
            print('failed: Error in config file.\n')
            sys.exit(1)

        config.update({'confUrl': confUrl,
                       'customize': customize,
                       'filePath': filePath,
                       'jackSsl': jackSsl,
                       'miscEntities': miscEntities,
                       'mqttPort': mqttPort,
                       'outputJobs': outputJobs,
                       'outputPath': outputPath,
                       'readJobs': readJobs})
        self._customization, self._itemFilter = \
            customization, itemFilter
        Mdata.jTemplateTs = self._translate(Mdata.jTemplateTs, 6, 2)
        Mdata.vTemplateSdas = self._translate(Mdata.vTemplateSdas, 0, 2)
        Mdata.vTemplateSdtr = self._translate(Mdata.vTemplateSdtr, 1, 2)
        Mdata.vTemplateToo = self._translate(Mdata.vTemplateToo, 2, 2)
        print('done')
        return config

    def _read_jack_devices(self, ccuType: str) -> dict:
        print(f'Reading {ccuType} info from CCU-Jack...', end='')
        detection = {}
        abbr = self._config.get('mqttAbbreviations')
        ccuTopic = self._config.get('ccuJackBaseTopic')
        try:
            ccuTopic = f'{ccuTopic}/' if ccuTopic[-1] != '/' else ccuTopic
        except IndexError:
            pass
        debug = self._config.get('debug', False)
        discBase = self._config.get('haDiscoveryTopic')
        hDevHrefs = self._http_get(f'/{ccuType}', '~links')
        for hDevHref in [x for x in hDevHrefs if x['title'] != 'Root']:
            detDevice = {}
            ident = hDevHref.get('href')
            hDevInfo = self._http_get(f'/{ccuType}/{ident}')
            hAvailInfo = self._http_get(f'/{ccuType}/{ident}/0/UNREACH')
            unreach = len(hAvailInfo) > 0
            devConfigUrl = self._config.get('confUrl')
            hChanHrefs = hDevInfo.get('~links')
            for hChanHref in [y for y in hChanHrefs if y['rel'] == 'channel'
                              and len(y['href']) == 1]:
                chanNum = hChanHref.get('href')
                detChannel = []
                url = f'/{ccuType}/{ident}/{chanNum}'
                hChanInfo = self._http_get(url, '~links')
                devRecord = {'configuration_url': devConfigUrl,
                             'identifiers': [ident],
                             'manufacturer': 'eq3',
                             'model': hDevInfo.get('type'),
                             'name': hDevInfo.get('title'),
                             'sw_version': hDevInfo.get('firmware')}
                for room in [z for z in hChanInfo if z['rel'] == 'room']:
                    devRecord.setdefault('suggested_area', room.get('title'))
                    break
                for attHref in [z for z in hChanInfo if
                                z['href'] in self._itemFilter or
                                f'{z["href"]}:{chanNum}' in self._itemFilter]:
                    detAttName = attHref.get('href')
                    hDetails = self._http_get(f'{url}/{detAttName}')
                    statusTopic = hDetails.get('mqttStatusTopic')
                    detChannel.append(
                        DataHolder(_abbr_=abbr,
                                   _debug_=debug,
                                   attType_=hDetails.get('type'),
                                   ccuTopic_=ccuTopic,
                                   ccuType_=ccuType,
                                   channel_=chanNum,
                                   device=devRecord,
                                   discBase_=discBase,
                                   ident_=ident,
                                   max=hDetails.get('maximum'),
                                   min=hDetails.get('minimum'),
                                   name=detAttName,
                                   setTopic_=hDetails.get('mqttSetTopic'),
                                   statusTopic_=statusTopic,
                                   unit_of_measurement=hDetails.get('unit'),
                                   unreach_=unreach))
                    self._entCount += 1
                if len(detChannel):
                    sortedDetChannel = sorted(detChannel,
                                              key=lambda x: x.keyType_)
                    detDevice.update({chanNum: sortedDetChannel})
            sortedDetDevice = dict(sorted(detDevice.items()))
            detection.setdefault(ident, sortedDetDevice)
        print('done')
        return dict(sorted(detection.items()))

    def _read_jack_sysvar(self, ccuType: str) -> dict:
        print(f'Reading {ccuType} info from CCU-Jack...', end='')
        detection = {}
        abbr = self._config.get('mqttAbbreviations')
        ccuTopic = self._config.get('ccuJackBaseTopic')
        debug = self._config.get('debug', False)
        discBase = self._config.get('haDiscoveryTopic')
        hVersion = self._http_get('/~vendor', 'serverVersion')
        devRecord = {'configuration_url': self._config.get('confUrl'),
                     'manufacturer': 'eq3',
                     'model': 'CCU3',
                     'sw_version': hVersion}
        devRecord['identifiers'] = self._translate('lang13', 4, 2) \
            if ccuType == 'sysvar' else self._translate('lang14', 5, 2)
        hDevHrefs = self._http_get(f'/{ccuType}', '~links')
        detChannel = []
        for hDevHref in [x for x in hDevHrefs if x['rel'] == ccuType]:
            ident = hDevHref.get('href')
            detAttName = hDevHref.get('title')
            hDetails = self._http_get(f'/{ccuType}/{ident}')
            detChannel.append(
                DataHolder(_abbr_=abbr,
                           _debug_=debug,
                           attType_=hDetails.get('type', 'STRING'),
                           ccuTopic_=ccuTopic,
                           ccuType_=ccuType,
                           channel_='0',
                           device=devRecord,
                           discBase_=discBase,
                           ident_=f'{ccuType}{ident}',
                           name=detAttName,
                           payload_off=hDetails.get('valueName0'),
                           payload_on=hDetails.get('valueName1'),
                           setTopic_=hDetails.get('mqttSetTopic'),
                           statusTopic_=hDetails.get('mqttStatusTopic'),
                           unit_of_measurement=hDetails.get('unit')))
        sortedDetChannel = sorted(detChannel, key=lambda x: x.name)
        detDevice = {'0': sortedDetChannel}
        detection.setdefault(ccuType, detDevice)
        print('done')
        return detection

    def _translate(self, text: str, tgt=None, langId=0) -> str:
        langId -= 1
        try:
            for num in Mdata.langTr[tgt]:
                attribute = f'lang{num}'
                translation = Mdata.lang.get(attribute)
                text = text.replace(attribute, translation[langId])
        except TypeError:
            for entry in Mdata.lang:
                for attribute in entry.keys():
                    text = text.replace(attribute, entry[attribute][langId])
        return text


def main() -> None:
    """ main """

    helpConfig = 'path and name of json config file'
    helpEnumerate = 'list sysvar and/or program identities'
    choices = ['all', 'device', 'program', 'sysvar']
    parser = argparse.ArgumentParser(add_help=True,
                                     description='\n',
                                     epilog='\n',
                                     prog='Jacking2Ha')
    parser.add_argument('--config', '-c',
                        help=helpConfig,
                        required=True)
    parser.add_argument('-e', '--enumerate',
                        choices=choices,
                        default='mqtt',
                        help=helpEnumerate,
                        required=False)
    parsed = parser.parse_args()
    jacking = Jacking2Ha(parsed.config)
    jacking(mode=parsed.enumerate)


if __name__ == '__main__':
    main()
