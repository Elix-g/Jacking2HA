import re

from dataclasses import dataclass
from typing import Dict

from data_functions import DataFunctions
from mdata import Mdata


@dataclass(init=True)
class DataHolder(DataFunctions):
    """ Container holding entries to publish """

    ccuTopic_: str
    ccuType_: str
    channel_: str
    device: Dict
    discBase_: str
    ident_: str
    name: str

    _abbr_: bool = True
    _debug_: bool = False

    attType_: str = ''
    availability: Dict = None
    command_topic: str = ''
    command_template: str = ''
    deleted_: bool = False
    device_class: str = ''
    discTopic_: str = ''
    entity_category: str = ''
    getTopic_: str = ''
    icon: str = ''
    json_attributes_template: str = ''
    json_attributes_topic: str = ''
    keyType_: str = ''
    max: any = None
    min: any = None
    mode: str = ''
    object_id: str = ''
    options: list = None
    origin: Dict = None
    payload_off: str = ''
    payload_on: str = ''
    payload_press: str = ''
    setTopic_: str = None
    statusTopic_: str = None
    state_off: str = ''
    state_on: str = ''
    state_topic: str = ''
    step: float = None
    suggested_display_precision: int = None
    haType_: str = ''
    unique_id: str = ''
    unit_of_measurement: str = ''
    unreach_: bool = None
    value_template: str = Mdata.vTemplate
    writable_: bool = False

    def __post_init__(self):
        self.keyType_ = self.name
        self.origin = Mdata.origin

        tCh = self.channel_
        tCt = self.ccuTopic_
        tCy = self.ccuType_
        tDt = self.discBase_
        tId = self.ident_.lower()
        tKd = re.sub(r'\W+', '', self.keyType_).lower()

        self.object_id = f'{tId}_ch{tCh}_{tKd}'
        self.unique_id = self.object_id

        if self.setTopic_ is not None:
            self.writable_ = True
            self.command_topic = f'{tCt}{self.setTopic_}'
        if self.statusTopic_ is not None:
            self.state_topic = f'{tCt}{self.statusTopic_}'
        if self.keyType_ in Mdata.diag and self.ccuType_ == 'device':
            self.entity_category = 'diagnostic'
        if self.keyType_ in ('PRESS_LONG', 'PRESS_SHORT'):
            self.command_topic = \
                f'{tCt}{self.statusTopic_.replace("/status/", "/set/")}'
        if self.unreach_:
            self.availability = \
                {'topic': f'{tCt}{tCy}/status/{self.ident_}/0/UNREACH'}
            self.availability.update(Mdata.availability)

        self._analyze()

        if not self.haType_ == 'number':
            self.max = None
            self.min = None
        if self.haType_ not in ('button', 'number', 'select', 'switch') \
           and self.device['model'] != 'HmIP-SWSD' \
           and self.ccuType_ == 'device':
            self.command_topic = None
            self.command_template = None

        tTl = self.haType_.lower()
        tDt = f'{tDt}/' if tDt[-1] != '/' else tDt
        self.discBase_ = tDt
        self.discTopic_ = f'{tDt}{tTl}/{tId}/ch{tCh}_{tKd}/config'
