import limone
import persistent
from persistent.list import PersistentList


class _MappingNode(persistent.Persistent, limone._MappingNode):
    pass


class _SequenceNode(limone._SequenceNode):
    _data_type = PersistentList


class _MetaType(type):
    def __new__(cls, name, bases, members):
        already_persistent = False
        for base in bases:
            if issubclass(base, persistent.Persistent):
                already_persistent = True
                break
        if not already_persistent:
            bases = (persistent.Persistent,) + bases
        return type.__new__(cls, name, bases, members)

    def __init__(cls, name, bases, members):
        type.__init__(cls, name, bases, members)
        cls._MappingNode = _MappingNode
        cls._SequenceNode = _SequenceNode


content_type = limone._ContentTypeDecorator(_MetaType)
content_schema = limone._ContentSchemaDecorator(_MetaType)


def make_content_type(schema, name, module=None, bases=(object,),
                      meta=_MetaType):
    return limone.make_content_type(
        schema, name, module, bases, meta)