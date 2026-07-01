def _coerce_query_value(value):
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered == 'true':
            return True
        if lowered == 'false':
            return False
        if lowered == 'none' or lowered == 'null':
            return None
    return value

def _resolve_query_value_from(value_from, request=None, source_obj=None):
    if not value_from:
        return None
    key = str(value_from).strip()
    if key.startswith("request.GET."):
        return request.GET.get(key.split("request.GET.", 1)[1]) if request is not None else None
    if key.startswith("request."):
        return request.GET.get(key.split("request.", 1)[1]) if request is not None else None
    if key.startswith("instance_id_"):
        return request.GET.get(key) if request is not None else None
    if key.startswith("source."):
        attr = key.split("source.", 1)[1]
        return getattr(source_obj, attr, None) if source_obj is not None else None
    return None

def _safe_select_related(qs, *fields):
    valid_fields = []
    for field in fields:
        try:
            model_field = qs.model._meta.get_field(field)
        except Exception:
            continue
        if getattr(model_field, "is_relation", False) and (
            getattr(model_field, "many_to_one", False) or getattr(model_field, "one_to_one", False)
        ):
            valid_fields.append(field)
    if valid_fields:
        return qs.select_related(*valid_fields)
    return qs

def _resolve_filter_field(field):
    """Normalize filter field name to Django ORM format.
    Supports dot-notation for FK traversal (one-hop or multi-hop):
      'Seller.name'         → 'Seller__name'
      'seller.name'         → 'Seller__name'  (capitalizes first segment)
      'Seller.Category.name'→ 'Seller__Category__name'
    Already-Django notation ('Seller__name') is passed through unchanged.
    """
    if not field:
        return field
    if '__' not in field and '.' in field:
        return field.replace('.', '__')
    return field

_OPERATOR_MAP = {
    'eq': '',
    'neq': '',
    'lt': '__lt',
    'lte': '__lte',
    'gt': '__gt',
    'gte': '__gte',
    'contains': '__icontains',
    'in': '__in',
    'isnull': '__isnull',
}


def _apply_filter_condition(qs, condition, request, source_obj):
    """Apply a single filter condition to a queryset and return the updated queryset."""
    field = _resolve_filter_field(condition.get('field'))
    operator = condition.get('operator', 'eq')
    if not field or operator not in _OPERATOR_MAP:
        return qs
    lookup = f"{field}{_OPERATOR_MAP[operator]}"
    value = _resolve_query_value_from(condition.get('value_from'), request=request, source_obj=source_obj)
    if value is None and condition.get('value_from'):
        return qs
    if value is None:
        value = _coerce_query_value(condition.get('value'))
    if operator == 'in' and not isinstance(value, (list, tuple)):
        value = [v.strip() for v in str(value).split(',') if v.strip()]
    try:
        if operator == 'neq':
            return qs.exclude(**{lookup: value})
        return qs.filter(**{lookup: value})
    except Exception:
        return qs


def _build_order_fields(order_by: list) -> list:
    """Convert order_by config into Django ORM field strings."""
    order_fields = []
    for item in order_by or []:
        if isinstance(item, str):
            order_fields.append(item)
            continue
        field = item.get('field')
        if not field:
            continue
        direction = item.get('direction', 'asc')
        order_fields.append(f"-{field}" if direction == 'desc' else field)
    return order_fields


def _apply_section_query(qs, query, source_obj=None, request=None):
    query = query or {}
    for condition in query.get('filters') or []:
        qs = _apply_filter_condition(qs, condition, request, source_obj)
    if query.get('exclude_source') and source_obj is not None:
        qs = qs.exclude(id=getattr(source_obj, 'id', None))
    order_fields = _build_order_fields(query.get('order_by'))
    if order_fields:
        try:
            qs = qs.order_by(*order_fields)
        except Exception:
            pass
    offset = query.get('offset') or 0
    limit = query.get('limit')
    if limit:
        return qs[offset:offset + int(limit)]
    if offset:
        return qs[offset:]
    return qs

def _apply_search_query(qs, request):
    term = (request.GET.get('q') or '').strip()
    if not term:
        return qs
    try:
        from django.db.models import Q, CharField, TextField
        query = Q()
        for field in qs.model._meta.get_fields():
            if isinstance(field, (CharField, TextField)):
                query |= Q(**{f"{field.name}__icontains": term})
        if query:
            return qs.filter(query).distinct()
    except Exception:
        pass
    return qs
