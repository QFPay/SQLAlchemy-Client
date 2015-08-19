# -*- coding: utf-8 -*-
import re
import types
from functools import partial

from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy import func as sql_func

from .expression import expression_wrapper
from .session import session_wrapper


class Client(object):
    """
    Client 层本体
    """
    def __init__(self, models, SessionFactory, spec_alias='spec', *args, **kwargs):
        # 方法正则模式
        self.method_pattern = re.compile('^(get|count|update|create|increase)_(.+?)(_list)?$')
        # model 对象与表名关联, 因此 model 对象必须有一个  '__tablename__' 属性
        if isinstance(models, types.ModuleType):
            self.TABLE_MODEL_MAP = get_models(models)
        elif isinstance(models, list):
            self.TABLE_MODEL_MAP = {}
            for module in models:
                self.TABLE_MODEL_MAP.update(get_models(module))
        # Session
        self.SessionFactory = SessionFactory
        # spec alias
        self.spec_alias = spec_alias
        return super(Client, self).__init__(*args, **kwargs)

    def __getattr__(self, attr):
        """
        方法访问重定向, 以及 model 对象获取
        """
        matches = re.match(self.method_pattern, attr)
        if not matches or matches.group(2) not in self.TABLE_MODEL_MAP:
            raise AttributeError('Unsupported query method:%s' % attr)
        method, table_name, lists = matches.groups()
        if method == 'get' and lists:
            return partial(self.get_all, model=self.TABLE_MODEL_MAP[table_name])
        elif method == 'get':
            return partial(self.get_first, model=self.TABLE_MODEL_MAP[table_name])
        elif method == 'count':
            return partial(self.count, model=self.TABLE_MODEL_MAP[table_name])
        elif method == 'update':
            return partial(self.update, model=self.TABLE_MODEL_MAP[table_name])
        elif method == 'create':
            return partial(self.create, model=self.TABLE_MODEL_MAP[table_name])
        elif method == 'increase':
            return partial(self.increase, model=self.TABLE_MODEL_MAP[table_name])

    @session_wrapper()
    @expression_wrapper
    def get_first(self, session, model, expressions, **kwargs):
        data = session.query(model).filter(*expressions)
        if kwargs.get('order_by'):
            if kwargs.get('desc'):
                data = data.order_by(kwargs['order_by'].desc())
            else:
                data = data.order_by(kwargs['order_by'])
        if kwargs.get('offset'):
            data = data.offset(kwargs['offset'])
        return data.first()

    @session_wrapper()
    @expression_wrapper
    def get_all(self, session, model, expressions, **kwargs):
        data = session.query(model).filter(*expressions)
        if kwargs.get('order_by'):
            if kwargs.get('desc'):
                data = data.order_by(kwargs['order_by'].desc())
            else:
                data = data.order_by(kwargs['order_by'])
        if kwargs.get('offset'):
            data = data.offset(kwargs['offset'])
        if kwargs.get('limit'):
            data = data.limit(kwargs['limit'])
        return data.all()

    @session_wrapper()
    @expression_wrapper
    def count(self, session, model, expressions, **kwargs):
        data = session.query(sql_func.count()).select_from(model).filter(*expressions)
        return data.scalar()

    @session_wrapper()
    @expression_wrapper
    def update(self, session, model, expressions, **kwargs):
        """
        更新, 返回被更新的数量
        """
        if not expressions:
            raise AssertionError('Client 层的更新操作必须提供查询条件')
        synchronize_session = kwargs.get('synchronize_session', 'fetch')
        data = session.query(model).filter(*expressions).\
            update(kwargs['set_value'], synchronize_session=synchronize_session)
        session.flush()
        return data

    @session_wrapper()
    def create(self, session, model, expressions, **kwargs):
        data = model(**kwargs)
        session.add(data)
        session.flush()
        return data

    @session_wrapper()
    @expression_wrapper
    def increase(self, session, model, expressions, **kwargs):
        """
        数据库数值型列自增减, 返回被更新的数量
        """
        if not expressions:
            raise AssertionError('Client 层的更新操作必须提供查询条件')
        increment = {k: getattr(model, k)+v for k, v in kwargs['set_value'].items()}
        synchronize_session = kwargs.get('synchronize_session', 'evaluate')
        data = session.query(model).filter(*expressions). \
            update(increment, synchronize_session=synchronize_session)
        session.flush()
        return data


def get_models(module):
    all_models = [getattr(module, name) for name in dir(module) if
                  isinstance(getattr(module, name), DeclarativeMeta) and
                  hasattr(getattr(module, name), '__tablename__')]
    return {model.__tablename__: model for model in all_models}
