# -*- coding: utf-8 -*-
def session_wrapper(*args, **kwargs):
    def real_wrapper(func):
        """
        获取 session 的装饰器
        """
        def wrapped(self, session=None, model=None, expressions=[], **kwargs):
            session = session or self.SessionFactory() if self.SessionFactory else None
            if not session:
                raise AssertionError('No session instance provided.')
            return func(self, session=session, model=model, expressions=expressions, **kwargs)
        return wrapped
    return real_wrapper
