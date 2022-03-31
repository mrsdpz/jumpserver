from django.db import models

ADMIN = 'Admin'
USER = 'User'
AUDITOR = 'Auditor'


class AssetProtocol(models.TextChoices):
    ssh = 'ssh', 'SSH'
    rdp = 'rdp', 'RDP'
    telnet = 'telnet', 'Telnet'
    vnc = 'vnc', 'VNC'
