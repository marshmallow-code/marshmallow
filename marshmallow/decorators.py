PRE_DUMP = 'pre_dump'
POST_DUMP = 'post_dump'
PRE_LOAD = 'pre_load'
POST_LOAD = 'post_load'


def pre_dump(fn=None, raw=False):
    return tag_processor(PRE_DUMP, fn, raw)


def post_dump(fn=None, raw=False):
    return tag_processor(POST_DUMP, fn, raw)


def pre_load(fn=None, raw=False):
    return tag_processor(PRE_LOAD, fn, raw)


def post_load(fn=None, raw=False):
    return tag_processor(POST_LOAD, fn, raw)


class _StaticProcessorMethod(staticmethod):
    """Allows setting attributes on a staticmethod"""
    pass


class _ClassProcessorMethod(classmethod):
    """Allows setting attributes on a classmethod"""
    pass


def tag_processor(tag_name, fn, raw):
    """Tags decorated processor function to be picked up later

    :return: Decorated function if supplied, else this decorator with its args
        bound.
    """
    if fn is None:
        return lambda fn_actual: tag_processor(tag_name, fn_actual, raw)

    # Special-case rewrapping staticmethod and classmethod, because we can't
    # directly set attributes on those.
    if isinstance(fn, staticmethod):
        try:
            unwrapped = fn.__func__
        except AttributeError:
            # For Python 2.6.
            unwrapped = fn.__get__(True)
        fn = _StaticProcessorMethod(unwrapped)
    elif isinstance(fn, classmethod):
        try:
            unwrapped = fn.__func__
        except AttributeError:
            # For Python 2.6.
            unwrapped = fn.__get__(True).im_func
        fn = _ClassProcessorMethod(unwrapped)

    # Set a processor_tags attribute instead of wrapping in some class,
    # because I still want this to end up as a normal (unbound) method.
    try:
        processor_tags = fn.__processor_tags__
    except AttributeError:
        fn.__processor_tags__ = processor_tags = set()
    processor_tags.add((tag_name, raw))

    return fn
