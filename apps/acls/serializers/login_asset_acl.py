from rest_framework import serializers
from django.utils.translation import ugettext_lazy as _
from orgs.mixins.serializers import BulkOrgResourceModelSerializer
from assets.models import SystemUser
from common.drf.serializers import MethodSerializer
from common.db.utils import ModelJSONFieldUtil
from acls import models
from orgs.models import Organization


__all__ = ['LoginAssetACLSerializer']


common_help_text = _('Format for comma-delimited string.')


class RuleSerializer(serializers.Serializer):
    attr = MethodSerializer()
    operator = serializers.ChoiceField(
        choices=ModelJSONFieldUtil.AttrOperator.choices,
        default=ModelJSONFieldUtil.AttrOperator.equal,
        label=_('Operator')
    )
    values = serializers.ListField(default=[], child=serializers.CharField(), label=_('Content'))

    def get_params_attr_choices(self):
        choices = []
        parent = self.parent
        while parent is not None:
            if isinstance(parent, ResourceSerializer) and hasattr(parent, 'attr_choices'):
                choices = parent.attr_choices
                break
            parent = parent.parent
        return choices

    def get_attr_serializer(self):
        choices = self.get_params_attr_choices()
        return serializers.ChoiceField(choices=choices, label=_('Attribute'))


class AttrsSerializer(serializers.Serializer):
    logical_operator = serializers.ChoiceField(
        choices=ModelJSONFieldUtil.RuleLogicalOperator.choices,
        default=ModelJSONFieldUtil.RuleLogicalOperator.and_,
        label=_('Logical operator')
    )
    rules = serializers.ListField(default=[], child=RuleSerializer(), label=_('Rules'))


class ResourceSerializer(serializers.Serializer):
    strategy = serializers.ChoiceField(
        required=True, choices=ModelJSONFieldUtil.ResourceStrategy.choices, label=_('Strategy')
    )
    objects = serializers.ListField(
        required=False, default=[], child=serializers.UUIDField(), label=_('Objects')
    )
    attrs = AttrsSerializer(required=False, default={})

    def __init__(self, attr_choices: list, **kwargs):
        self.attr_choices = attr_choices
        super().__init__(**kwargs)


class LoginAssetACLSerializer(BulkOrgResourceModelSerializer):
    users = ResourceSerializer(
        attr_choices=[
            ('username', _('Username'))
        ]
    )
    assets = ResourceSerializer(
        attr_choices=[
            ('hostname', _('Hostname')),
            ('ip', 'IP')
        ]
    )
    system_users = ResourceSerializer(
        attr_choices=[
            ('name', _('Name')),
            ('username', _('Username')),
            ('protocol', _('Protocol'))
        ]
    )
    reviewers_amount = serializers.IntegerField(read_only=True, source='reviewers.count')
    action_display = serializers.ReadOnlyField(source='get_action_display', label=_('Action'))

    class Meta:
        model = models.LoginAssetACL
        fields_mini = ['id', 'name']
        fields_small = fields_mini + [
            'users', 'system_users', 'assets',
            'is_active',
            'date_created', 'date_updated',
            'priority', 'action', 'action_display', 'comment', 'created_by', 'org_id'
        ]
        fields_m2m = ['reviewers', 'reviewers_amount']
        fields = fields_small + fields_m2m
        extra_kwargs = {
            "reviewers": {'allow_null': False, 'required': True},
            'priority': {'default': 50},
            'is_active': {'default': True},
        }

    def validate_reviewers(self, reviewers):
        org_id = self.fields['org_id'].default()
        org = Organization.get_instance(org_id)
        if not org:
            error = _('The organization `{}` does not exist'.format(org_id))
            raise serializers.ValidationError(error)
        users = org.get_members()
        valid_reviewers = list(set(reviewers) & set(users))
        if not valid_reviewers:
            error = _('None of the reviewers belong to Organization `{}`'.format(org.name))
            raise serializers.ValidationError(error)
        return valid_reviewers
