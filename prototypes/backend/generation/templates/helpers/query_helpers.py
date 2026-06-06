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

def _apply_section_query(qs, query, source_obj=None):
    query = query or {}
    operator_map = {
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
    for condition in query.get('filters') or []:
        field = _resolve_filter_field(condition.get('field'))
        operator = condition.get('operator', 'eq')
        if not field or operator not in operator_map:
            continue
        lookup = f"{field}{operator_map[operator]}"
        value = _coerce_query_value(condition.get('value'))
        if operator == 'in' and not isinstance(value, (list, tuple)):
            value = [v.strip() for v in str(value).split(',') if v.strip()]
        try:
            if operator == 'neq':
                qs = qs.exclude(**{lookup: value})
            else:
                qs = qs.filter(**{lookup: value})
        except Exception:
            pass
    if query.get('exclude_source') and source_obj is not None:
        qs = qs.exclude(id=getattr(source_obj, 'id', None))
    order_fields = []
    for item in query.get('order_by') or []:
        if isinstance(item, str):
            order_fields.append(item)
            continue
        field = item.get('field')
        if not field:
            continue
        direction = item.get('direction', 'asc')
        order_fields.append(f"-{field}" if direction == 'desc' else field)
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
