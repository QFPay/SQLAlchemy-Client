SQLAlchemy-Client
==============

本项目通过一个 Client 对象提供了对 SQLAlchemy 基本查询语句的封装，用以使操作数据库的代码更自然简洁，提高开发速度。

Installation
------------

将本项目代码作为子模块 (submodule) 添加到用户自己的项目中即可。

使用本项目默认的前提是：

1. 项目有一个 ``models`` 模块，所有表都映射为一个 ``model``
2. ``Session`` 对象的构建和管理由用户自己实现

Usage
-----

用户使用的唯一接口是一个 ``Client`` 对象的实例，初始化参数为：

* 全部 model 的列表或 models 模块自身，必需
* 一个可以返回 session 实例的可调用对象（``SessionFactory``），可选
  
    如果初始化时没有传入 ``SessionFactory``，则在调用 dao 方法时需要传入一个可用的 session 实例。

    ``Client`` 会尝试为每次请求实例化一次 ``SessionFactory``, 因此建议使用 ``scoped_session``

    在项目中， ``Client`` 实例应是全局的，并发导致的线程安全等问题应在 Session 上解决

.. code-block:: python

    >>> from sqlalchemy_dao import Client
    >>> import models
    >>> from somewhere import Session
    >>> 
    >>> dao = Client(models=models, SessionFactory=Session)
    >>> dao.create_user(id=1234)



Method
^^^^^^

对 dao 对象的方法调用的基本模式是三段元素由下划线分割： ``METHOD_TABLENAME_(list)``。

**METHOD** 限于

1. get
2. create
3. count
4. update
5. increase
   
**TABLENAME** 即为 model 的 ``__tablename__``属性，所以这个属性是必需的。（表名中允许有下划线）

最后可选的 **list** 仅用于 ``get`` 方法时，有 **list** 就返回一个 model 列表，没有就返回单个 model。

Params
^^^^^^

**所有 dao 方法调用的参数都应是关键字参数**

除了 ``(spec, session, set_value, offset, limit, order_by, desc)`` 这几个特殊参数名外，其他参数都会被当做表字段传入 ``filter`` 中。如

.. code-block:: python

    >>> dao.get_user_list(status=1, offset=0, limit=10, order_by='created', desc=True)  # select * from user where
    >>> dao.update_user(id=10000, set_value={'status': 0})  # update user set status=0 where id=10000;
    >>> dao.increase_item(id=10000, set_value={'amount': -1})  # update item set amount=amount-1 where id=10000;

关于参数类型，标量 ``（str, number）`` 代表等于，``list`` 代表 in。

``set_value`` 类型为字典，用于 ``update`` 与 ``increase`` 方法。表示 update 的值或增量

Spec
^^^^

更加复杂的查询，使用 mongodb 的语法来实现。即通过一个名为 ``spec`` 的字典。如果这个名字与项目的某张表的字段名冲突了，可以在实例化 ``Client`` 时传入一个 ``spec_alias`` 参数来改变默认的名字。 ``spec`` 参数可以与关键字参数共存，之间为 **和** 的关系

mongodb 的查询语法可以参见 `mongodb Query and Projection Operators`_ 

.. _mongodb Query and Projection Operators: http://docs.mongodb.org/manual/reference/operator/query/

Demo
^^^^

.. code-block:: python

    >>> dao.create_user(name='test', mobile='12345678')
    >>> dao.create_user(session, name='test', mobile='12345678')  # 当实例化 Client 没有传入 SessionFactory 时
    >>> 
    >>> user = dao.get_user(id=10000)
    >>> user_list = dao.get_user_list(status=1, group_id=2, order_by='created', desc=True)
    >>> 
    >>> spec = {
        'id': {'$gt': 10000},
        'status': [1, 2, 3],
    }
    >>> spec = {
        '$or': [
            'created': {'$gt': '1920-01-01'},
            'created': {'$lt': '1920-12-12'}
        ]
    }
    >>> dao.count_user(spec=spec)
    >>> dao.count_user(spec=spec, status=1)  # spec 与 status 此时是 "与" 的逻辑关系
    >>> 
    >>> dao.update_user(id=10000, set_value={'status': 0})  # update user set status=0 where id=10000;
    >>> 
    >>> dao.increase_item(id=10000, set_value={'amount': -1})  # update item set amount=amount-1 where id=10000;

More
^^^^

代码不多，上面文档有不清楚的地方直接看代码就明白了
