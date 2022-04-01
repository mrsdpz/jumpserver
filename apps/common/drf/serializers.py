from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.serializers import Serializer
from rest_framework.serializers import ModelSerializer
from rest_framework_bulk.serializers import BulkListSerializer

from common.mixins import BulkListSerializerMixin
from django.utils.functional import cached_property
from common.mixins.serializers import BulkSerializerMixin
from common.const.choices import AssetProtocol

__all__ = [
    'MethodSerializer',
    'EmptySerializer', 'BulkModelSerializer', 'AdaptedBulkListSerializer', 'CeleryTaskSerializer',
    'AssetProtocol', 'AssetProtocolsField', 'AssetProtocolField'
]


# MethodSerializer
# ----------------


class MethodSerializer(serializers.Serializer):

    def __init__(self, method_name=None, **kwargs):
        self.method_name = method_name
        super().__init__(**kwargs)

    class Meta:
        # 生成swagger时使用
        ref_name = None

    def bind(self, field_name, parent):
        if self.method_name is None:
            method_name = 'get_{field_name}_serializer'.format(field_name=field_name)
            self.method_name = method_name

        super().bind(field_name, parent)

    @cached_property
    def serializer(self) -> serializers.Serializer:
        method = getattr(self.parent, self.method_name)
        _serializer = method()
        # 设置serializer的parent值，否则在serializer实例中获取parent会出现断层
        setattr(_serializer, 'parent', self.parent)
        return _serializer

    @cached_property
    def fields(self):
        """
        重写此方法因为在 BindingDict 中要设置每一个 field 的 parent 为 `serializer`,
        这样在调用 field.parent 时, 才会达到预期的结果，
        比如: serializers.SerializerMethodField
        """
        return self.serializer.fields

    def run_validation(self, data=serializers.empty):
        return self.serializer.run_validation(data)

    def to_representation(self, instance):
        return self.serializer.to_representation(instance)

    def get_initial(self):
        return self.serializer.get_initial()


# Other Serializer
# ----------------


class EmptySerializer(Serializer):
    pass


class BulkModelSerializer(BulkSerializerMixin, ModelSerializer):
    pass


class AdaptedBulkListSerializer(BulkListSerializerMixin, BulkListSerializer):
    pass


class CeleryTaskSerializer(serializers.Serializer):
    task = serializers.CharField(read_only=True)


def validate_duplicate_protocols(values):
    errors = []
    names = []

    for value in values:
        if not value or '/' not in value:
            continue
        name = value.split('/')[0]
        if name in names:
            errors.append(_("Protocol duplicate: {}").format(name))
        names.append(name)
        errors.append('')
    if any(errors):
        raise serializers.ValidationError(errors)


class AssetProtocolField(serializers.RegexField):
    protocols = '|'.join(dict(AssetProtocol.choices).keys())
    default_error_messages = {
        'invalid': _('Protocol format should {}/{}').format(protocols, '1-65535')
    }
    regex = r'^(%s)/(\d{1,5})$' % protocols

    def __init__(self, *args, **kwargs):
        super().__init__(self.regex, **kwargs)


class AssetProtocolsField(serializers.ListField):
    default_validators = [validate_duplicate_protocols]

    def __init__(self, *args, **kwargs):
        kwargs['child'] = AssetProtocolField()
        kwargs['allow_null'] = True
        kwargs['allow_empty'] = True
        kwargs['min_length'] = 1
        kwargs['max_length'] = 4
        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        if not value:
            return []
        return value.split(' ')
