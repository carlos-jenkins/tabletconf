"""
Simple dictionary to object class.
"""

from collections import Mapping
try:
    from pprintpp import pformat
except ImportError:
    from pprint import pformat


def update(to_update, update_with):
    """
    Recursively update a dictionary with another.

    :param dict to_update: Dictionary to update.
    :param dict update_with: Dictionary to update with.

    :return: The first dictionary recursively updated by the second.
    :rtype: dict
    """
    for key, value in update_with.items():
        if isinstance(value, Mapping):
            to_update[key] = update(
                to_update.get(key, type(value)()),
                value,
            )
        else:
            to_update[key] = value

    return to_update


class Namespace:
    """
    Simple dictionary to object class.

    Usage:

    .. code-block:: python3

        >>> from metrica.namespace import Namespace
        >>> ns = Namespace(
        ...     {'one': 100},
        ...     {'two': 300},
        ...     {'two': 400, 'three': {'four': 400}},
        ...     one=200,
        ... )
        >>> ns.two
        400
        >>> ns.one
        200
        >>> ns['two']
        400
        >>> ns['two'] = 300
        >>> ns['two']
        300
        >>> ns.two = 700
        >>> ns['two']
        700
        >>> ns.two
        700
        >>> ns.three.four
        400
        >>> ns['three'].four
        400
        >>> ns['three']['four']
        400
    """

    def __init__(self, *args, **kwargs):

        spread = list(args) + [kwargs]
        assert all(
            isinstance(element, Mapping)
            for element in spread
        )

        head, *tail = spread

        for element in tail:
            update(head, element)

        data = type(head)(
            (
                key, (
                    Namespace(value)
                    if isinstance(value, Mapping)
                    else value
                )
            )
            for key, value in head.items()
        )

        super().__setattr__('_data', data)

    def __getattr__(self, attr):
        return self[attr]

    def __setattr__(self, attr, value):
        self[attr] = value

    def __iter__(self):
        data = super().__getattribute__('_data')
        for key, value in data.items():
            if isinstance(value, self.__class__):
                yield key, type(data)(value)
                continue
            yield key, value

    def __getitem__(self, key):
        data = super().__getattribute__('_data')
        return data[key]

    def __setitem__(self, key, value):
        if isinstance(value, Mapping):
            value = Namespace(value)

        data = super().__getattribute__('_data')
        data[key] = value

    def __repr__(self):
        data = super().__getattribute__('_data')
        return pformat(type(data)(self))

    def __str__(self):
        return repr(self)

    def update(self, update_with):
        data = super().__getattribute__('_data')

        if isinstance(update_with, self.__class__):
            update_with = type(data)(update_with)

        to_update = type(data)(self)
        update(to_update, update_with)

        data = type(data)(
            (
                key, (
                    Namespace(value)
                    if isinstance(value, Mapping)
                    else value
                )
            )
            for key, value in to_update.items()
        )
        super().__setattr__('_data', data)


__all__ = [
    'Namespace',
]
