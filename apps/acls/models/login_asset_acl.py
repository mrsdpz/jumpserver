from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from orgs.mixins.models import OrgModelMixin, OrgManager
from .base import BaseACL, BaseACLQuerySet
from common.utils.ip import contains_ip
from common.db.utils import ModelJSONFieldUtil
from orgs.utils import tmp_to_org
from common.db.encoder import ModelJSONFieldEncoder


class ACLManager(OrgManager):

    def valid(self):
        return self.get_queryset().valid()


class LoginAssetACL(BaseACL, OrgModelMixin):
    class ActionChoices(models.TextChoices):
        login_confirm = 'login_confirm', _('Login confirm')

    # 条件
    # TODO: 下一步封装一个多策略Model和Serializer字段
    users = models.JSONField(
        encoder=ModelJSONFieldEncoder, default=dict, verbose_name=_("User")
    )
    assets = models.JSONField(
        encoder=ModelJSONFieldEncoder, default=dict, verbose_name=_("Asset")
    )
    system_users = models.JSONField(
        encoder=ModelJSONFieldEncoder, default=dict, verbose_name=_("System User")
    )
    # 动作
    action = models.CharField(
        max_length=64, choices=ActionChoices.choices, default=ActionChoices.login_confirm,
        verbose_name=_('Action')
    )
    # 动作: 附加字段
    # - login_confirm
    reviewers = models.ManyToManyField(
        'users.User', related_name='review_login_asset_acls', blank=True,
        verbose_name=_("Reviewers")
    )

    objects = ACLManager.from_queryset(BaseACLQuerySet)()

    class Meta:
        unique_together = ('name', 'org_id')
        ordering = ('priority', '-date_updated', 'name')
        verbose_name = _('Login asset acl')

    def __str__(self):
        return self.name

    # TODO: 下一步放入封装的Model字段中
    def get_users_objects(self):
        queryset = self.org.get_members()
        util = ModelJSONFieldUtil(value=self.users, queryset=queryset, org=self.org)
        queryset = util.to_queryset()
        return queryset

    def get_assets_objects(self):
        from assets.models import Asset
        queryset = Asset.objects
        util = ModelJSONFieldUtil(value=self.users, queryset=queryset, org=self.org)
        queryset = util.to_queryset()
        return queryset

    def get_system_users_objects(self):
        from assets.models import SystemUser
        queryset = SystemUser.objects
        util = ModelJSONFieldUtil(value=self.users, queryset=queryset, org=self.org)
        queryset = util.to_queryset()
        return queryset

    @classmethod
    def filter(cls, user, asset, system_user, action):
        queryset = cls.objects.filter(action=action)
        queryset = cls.filter_by_json_field(queryset, field_name='users', instance=user)
        queryset = cls.filter_by_json_field(queryset, field_name='assets', instance=asset)
        queryset = cls.filter_by_json_field(queryset, field_name='system_users', instance=system_user)
        return queryset

    @classmethod
    def filter_by_json_field(cls, queryset, field_name, instance):
        ids = []
        for q in queryset:
            get_instances = getattr(q, f'get_{field_name}_objects', None)
            if not get_instances:
                continue
            instances = get_instances()
            instances_ids = instances.values_list('id', flat=True)
            if instance.id in instances_ids:
                ids.append(q.id)
        queryset = cls.objects.filter(id__in=ids)
        return queryset

    @classmethod
    def create_login_asset_confirm_ticket(cls, user, asset, system_user, assignees, org_id):
        from tickets.const import TicketType
        from tickets.models import Ticket
        data = {
            'title': _('Login asset confirm') + ' ({})'.format(user),
            'type': TicketType.login_asset_confirm,
            'meta': {
                'apply_login_user': str(user),
                'apply_login_asset': str(asset),
                'apply_login_system_user': str(system_user),
            },
            'org_id': org_id,
        }
        ticket = Ticket.objects.create(**data)
        ticket.create_process_map_and_node(assignees)
        ticket.open(applicant=user)
        return ticket
