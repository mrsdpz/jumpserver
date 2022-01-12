from contextlib import contextmanager

from django.db import connections, models
from django.db.models import Q
from orgs.utils import tmp_to_org

from common.utils import get_logger

logger = get_logger(__file__)


def get_object_if_need(model, pk):
    if not isinstance(pk, model):
        try:
            return model.objects.get(id=pk)
        except model.DoesNotExist as e:
            logger.error(f'DoesNotExist: <{model.__name__}:{pk}> not exist')
            raise e
    return pk


def get_objects_if_need(model, pks):
    if not pks:
        return pks
    if not isinstance(pks[0], model):
        objs = list(model.objects.filter(id__in=pks))
        if len(objs) != len(pks):
            pks = set(pks)
            exists_pks = {o.id for o in objs}
            not_found_pks = ','.join(pks - exists_pks)
            logger.error(f'DoesNotExist: <{model.__name__}: {not_found_pks}>')
        return objs
    return pks


def get_objects(model, pks):
    if not pks:
        return pks

    objs = list(model.objects.filter(id__in=pks))
    if len(objs) != len(pks):
        pks = set(pks)
        exists_pks = {o.id for o in objs}
        not_found_pks = pks - exists_pks
        logger.error(f'DoesNotExist: <{model.__name__}: {not_found_pks}>')
    return objs


def close_old_connections():
    for conn in connections.all():
        conn.close_if_unusable_or_obsolete()


@contextmanager
def safe_db_connection():
    close_old_connections()
    yield
    close_old_connections()


class ModelJSONFieldUtil(object):
    class ResourceStrategy(models.TextChoices):
        all = 'all', 'All'
        objects = 'objects', 'Objects'
        attrs = 'attrs', 'Attributes'

    class RuleLogicalOperator(models.TextChoices):
        and_ = 'and', 'AND'

    class AttrOperator(models.TextChoices):
        equal = '=', '='

    def __init__(self, value: dict, queryset, org):
        self.value = value
        self.queryset = queryset
        self.org = org

    def to_queryset(self):
        queries = self._get_queries()
        with tmp_to_org(self.org):
            if queries is None:
                queryset = self.queryset.none()
            else:
                queryset = self.queryset.filter(queries)
        return queryset

    def _get_queries(self):
        objects = self.value.get('objects', [])
        strategy = self.value.get('strategy', self.ResourceStrategy.all)
        attrs = self.value.get('attrs', {})
        if strategy == self.ResourceStrategy.all:
            queries = Q()
        elif strategy == self.ResourceStrategy.objects:
            queries = Q(id__in=objects)
        elif strategy == self.ResourceStrategy.attrs:
            logical_operator = attrs.get('logical_operator', self.RuleLogicalOperator.and_)
            rules = attrs.get('rules', [])
            queries = self._get_rules_queries(rules=rules, logical_operator=logical_operator)
        else:
            queries = None
        return queries

    def _get_rules_queries(self, rules, logical_operator):
        q_list = self._get_rules_query_list(rules)
        if logical_operator == self.RuleLogicalOperator.and_:
            queries = Q()
            for q in q_list:
                queries &= q
        else:
            queries = None
        return queries

    def _get_rules_query_list(self, rules) -> list:
        query_list = []
        for rule in rules:
            attr = rule.get('attr')
            values = rule.get('values')
            operator = rule.get('operator', self.AttrOperator.equal)
            if not attr or not values:
                continue
            if operator == self.AttrOperator.equal:
                query_dict = {
                    f'{attr}__in': values
                }
            else:
                continue
            q = Q(**query_dict)
            query_list.append(q)
        return query_list