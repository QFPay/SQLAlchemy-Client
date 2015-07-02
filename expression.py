# -*- coding: utf-8 -*-
import operator
from numbers import Number

from sqlalchemy import or_, not_, and_


def expression_wrapper(func):
    """
    一个将关键字参数转换为 sqlalchemy 查询(filter)表达式的装饰器
    """
    def wrapped(self, session=None, model=None, expressions=[], **kwargs):
        # 参数处理
        filter_args = kwargs.copy()
        # 特殊参数处理
        if 'order_by' in filter_args:
            kwargs.update({'order_by': getattr(model, str(filter_args.pop('order_by')))})
        [filter_args.pop(k) for k in ('offset', 'limit', 'desc', 'set_value') if k in filter_args]
        # filter 参数
        spec = filter_args.pop(self.spec_alias, {})
        spec.update(filter_args)
        expressions = expression_convert(model, spec)
        return func(self, session=session, model=model, expressions=expressions, **kwargs)
    return wrapped


def operator_in(column, container):
    return column.in_(container)


def operator_nin(column, container):
    return not_(column.in_(container))

base_op = {
    '$eq': operator.eq,
    '$ne': operator.ne,
    '$lt': operator.lt,
    '$lte': operator.le,
    '$gt': operator.gt,
    '$gte': operator.ge,
    '$in': operator_in,
    '$nin': operator_nin,
}

multi_op = {
    '$or': or_,
    '$and': and_,
    # '$nor': NotImplementedError,
}


def expression_convert(model, spec):
    """
    获取 Query 对象列表
    """
    expressions = []
    for k, v in spec.items():
        if not isinstance(k, basestring):
            raise TypeError('Invalid column name:%s' % str(k))
        if not k.startswith('$'):
            # k 为 Column, v 为标量
            if isinstance(v, (basestring, Number)) or v is None:
                expressions.append(getattr(model, k) == v)
            elif isinstance(v, list):
                expressions.append(getattr(model, k).in_(v))
            elif isinstance(v, dict):
                for op, value in v.items():
                    if op not in base_op:
                        raise TypeError('Unsupported operator: %s' % op)
                    expressions.append(base_op[op](getattr(model, k), value))
            else:
                raise TypeError('Unsupported value type: %s' % str(v))
        elif k in multi_op:
            # k 为 operator, v 为 list
            sub_expressions = reduce(lambda x, y: x + expression_convert(model, y), v, [])
            multi_express = multi_op[k](*sub_expressions)
            expressions.append(multi_express)
        elif k == '$not':
            # k 为 operator, v 为 base expression
            expressions.append(not_(expression_convert(model, v)))
        else:
            raise TypeError('Unsupported operator: %s' % k)
    return expressions
