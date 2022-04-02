# -*- coding: utf-8 -*-
#

from django.db.models import TextChoices
from django.utils.translation import ugettext_lazy as _

# Replay & Command Storage Choices
# --------------------------------


class ReplayStorageTypeChoices(TextChoices):
    null = 'null', 'Null',
    server = 'server', 'Server'
    s3 = 's3', 'S3'
    ceph = 'ceph', 'Ceph'
    swift = 'swift', 'Swift'
    oss = 'oss', 'OSS'
    azure = 'azure', 'Azure'
    obs = 'obs', 'OBS'
    cos = 'cos', 'COS'


class CommandStorageTypeChoices(TextChoices):
    null = 'null', 'Null',
    server = 'server', 'Server'
    es = 'es', 'Elasticsearch'


# Component Status Choices
# ------------------------

class ComponentStatusChoices(TextChoices):
    critical = 'critical', _('Critical')
    high = 'high', _('High')
    normal = 'normal', _('Normal')
    offline = 'offline', _('Offline')

    @classmethod
    def status(cls):
        return set(dict(cls.choices).keys())


class TerminalTypeChoices(TextChoices):
    koko = 'koko', 'KoKo'
    guacamole = 'guacamole', 'Guacamole'
    omnidb = 'omnidb', 'OmniDB'
    xrdp = 'xrdp', 'Xrdp'
    lion = 'lion', 'Lion'
    core = 'core', 'Core'
    celery = 'celery', 'Celery'
    magnus = 'magnus',  'Magnus'

    @classmethod
    def types(cls):
        return set(dict(cls.choices).keys())

    def support_protocols(self):
        pass


class ProtocolName(TextChoices):
    http = 'http', 'HTTP'
    ssh = 'ssh', 'SSH'
    rdp = 'rdp', 'RDP'
    mysql = 'mysql', 'MySQL'
    mariadb = 'mariadb', 'MariaDB'
    postgresql = 'postgresql', 'PostgreSQL'
    # oracle = 'oracle', 'Oracle'
    # sqlserver = 'sqlserver', 'SQLServer'
    # redis = 'redis', 'Redis'
    # mongodb = 'mongodb', 'MongoDB'

    @property
    def default_port(self):
        default_port_mapper: dict = {
            self.http: 80,
            self.ssh: 22,
            self.rdp: 3389,
            self.mysql: 3306,
            self.mariadb: 3306,
            self.postgresql: 5432,
            # self.oracle: 1521,
            # self.sqlserver: 1433,
            # self.redis: 6379,
            # self.mongodb: 27017
        }
        assert self.name in default_port_mapper, 'No support protocol: {}'.format(self.name)
        return default_port_mapper[self.name]


terminal_type_protocols_mapper = {
    TerminalTypeChoices.koko: [
        ProtocolName.http, ProtocolName.ssh
    ],
    TerminalTypeChoices.lion: [
        ProtocolName.http
    ],
    TerminalTypeChoices.omnidb: [
        ProtocolName.http
    ],
    TerminalTypeChoices.xrdp: [
        ProtocolName.rdp
    ],
    TerminalTypeChoices.magnus: [
        ProtocolName.mysql, ProtocolName.mariadb, ProtocolName.postgresql
        # ProtocolName.oracle, ProtocolName.sqlserver,
        # ProtocolName.redis, ProtocolName.mongodb
    ],
    TerminalTypeChoices.core: [
        ProtocolName.http
    ],
    TerminalTypeChoices.celery: [
        ProtocolName.http
    ],
    TerminalTypeChoices.guacamole: [
        ProtocolName.http
    ]
}
