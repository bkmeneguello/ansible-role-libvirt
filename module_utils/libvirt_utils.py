import copy
import os
import re
from enum import IntEnum
from xml.etree import ElementTree

import libvirt

try:
    from io import StringIO
    from lxml import etree
    VALIDATE = True
except ImportError:
    VALIDATE = False

common_args = dict(
    uri=dict(type='str')
)


def to_xml(obj):
    els, _, _ = __dict_to_xml(obj)
    return els[0]


def xml_to_str(root):
    return ElementTree.tostring(root).decode()


def __dict_to_xml(d):
    children = []
    attrs = {}
    text = None
    for key, value in d.items():
        if key == '__value':
            text = str(value)
        elif key.startswith('_'):
            attrs[key[1:]] = str(value)
        else:
            if isinstance(value, dict):
                el = __build_tag(key, value)
                children.append(el)
            elif isinstance(value, list):
                for item in value:
                    el = __build_tag(key, item)
                    children.append(el)
            elif isinstance(value, bool):
                el = __build_tag(key)
                children.append(el)
            else:
                el = ElementTree.Element(key)
                if value is not None:
                    el.text = str(value)
                children.append(el)
    return children, attrs, text


def __build_tag(key, value=None):
    if value is not None:
        children, tag_attrs, tag_text = __dict_to_xml(value)
        el = ElementTree.Element(key, tag_attrs)
        if tag_text is not None:
            el.text = str(tag_text)
        for child in children:
            el.append(child)
        return el
    else:
        return ElementTree.Element(key)


def str_to_xml(xml):
    root = ElementTree.fromstring(xml)
    return root


def from_xml(xml):
    root = str_to_xml(xml)
    d = __xml_to_dict(root)
    return __build_dict(*d)


def __build_dict(text, attrs, children):
    obj = dict()
    if text is not None:
        if attrs or children:
            obj['__value'] = text
        else:
            obj = text
    for key, value in attrs.items():
        obj['_{}'.format(key)] = value
    for tag, child in children.items():
        obj[tag] = child
    return obj


def __xml_to_dict(element):
    group = dict()
    for child in list(element):
        group.setdefault(child.tag, []).append(__xml_to_dict(child))
    children = dict()
    for tag, child_list in group.items():
        if len(child_list) is 1:
            children[tag] = __build_dict(*child_list[0])
        else:
            children[tag] = [__build_dict(*child) for child in child_list]

    text = None
    if element.text and element.text.strip():
        text = element.text
    return text, element.attrib, children


def get_conn(params):
    conn = libvirt.open(params['uri'])
    return conn


DOMAIN_STATES = {
    libvirt.VIR_DOMAIN_NOSTATE: 'nostate',
    libvirt.VIR_DOMAIN_RUNNING: 'running',
    libvirt.VIR_DOMAIN_BLOCKED: 'blocked',
    libvirt.VIR_DOMAIN_PAUSED: 'paused',
    libvirt.VIR_DOMAIN_SHUTDOWN: 'shutdown',
    libvirt.VIR_DOMAIN_SHUTOFF: 'shutoff',
    libvirt.VIR_DOMAIN_CRASHED: 'crashed',
    libvirt.VIR_DOMAIN_PMSUSPENDED: 'pmsuspended',
}

DOMAIN_STATE_REASONS = {
    libvirt.VIR_DOMAIN_NOSTATE: {
        libvirt.VIR_DOMAIN_NOSTATE_UNKNOWN: 'unknown',
    },
    libvirt.VIR_DOMAIN_RUNNING: {
        libvirt.VIR_DOMAIN_RUNNING_UNKNOWN: 'unknown',
        libvirt.VIR_DOMAIN_RUNNING_BOOTED: 'booted',
        libvirt.VIR_DOMAIN_RUNNING_MIGRATED: 'migrated',
        libvirt.VIR_DOMAIN_RUNNING_RESTORED: 'restored',
        libvirt.VIR_DOMAIN_RUNNING_FROM_SNAPSHOT: 'from_snapshot',
        libvirt.VIR_DOMAIN_RUNNING_UNPAUSED: 'unpaused',
        libvirt.VIR_DOMAIN_RUNNING_MIGRATION_CANCELED: 'migration_canceled',
        libvirt.VIR_DOMAIN_RUNNING_SAVE_CANCELED: 'save_canceled',
        libvirt.VIR_DOMAIN_RUNNING_WAKEUP: 'wakeup',
        libvirt.VIR_DOMAIN_RUNNING_CRASHED: 'crashed',
        libvirt.VIR_DOMAIN_RUNNING_POSTCOPY: 'postcopy',
    },
    libvirt.VIR_DOMAIN_BLOCKED: {
        libvirt.VIR_DOMAIN_BLOCKED_UNKNOWN: 'unknown',
    },
    libvirt.VIR_DOMAIN_PAUSED: {
        libvirt.VIR_DOMAIN_PAUSED_UNKNOWN: 'unknown',
        libvirt.VIR_DOMAIN_PAUSED_USER: 'user',
        libvirt.VIR_DOMAIN_PAUSED_MIGRATION: 'migration',
        libvirt.VIR_DOMAIN_PAUSED_SAVE: 'save',
        libvirt.VIR_DOMAIN_PAUSED_DUMP: 'dump',
        libvirt.VIR_DOMAIN_PAUSED_IOERROR: 'ioerror',
        libvirt.VIR_DOMAIN_PAUSED_WATCHDOG: 'watchdog',
        libvirt.VIR_DOMAIN_PAUSED_FROM_SNAPSHOT: 'from_snapshot',
        libvirt.VIR_DOMAIN_PAUSED_SHUTTING_DOWN: 'shutting_down',
        libvirt.VIR_DOMAIN_PAUSED_SNAPSHOT: 'snapshot',
        libvirt.VIR_DOMAIN_PAUSED_CRASHED: 'crashed',
        libvirt.VIR_DOMAIN_PAUSED_STARTING_UP: 'starting_up',
        libvirt.VIR_DOMAIN_PAUSED_POSTCOPY: 'postcopy',
        libvirt.VIR_DOMAIN_PAUSED_POSTCOPY_FAILED: 'postcopy_failed',
    },
    libvirt.VIR_DOMAIN_SHUTDOWN: {
        libvirt.VIR_DOMAIN_SHUTDOWN_UNKNOWN: 'unknown',
        libvirt.VIR_DOMAIN_SHUTDOWN_USER: 'user',
    },
    libvirt.VIR_DOMAIN_SHUTOFF: {
        libvirt.VIR_DOMAIN_SHUTOFF_UNKNOWN: 'unknown',
        libvirt.VIR_DOMAIN_SHUTOFF_SHUTDOWN: 'shutdown',
        libvirt.VIR_DOMAIN_SHUTOFF_DESTROYED: 'destroyed',
        libvirt.VIR_DOMAIN_SHUTOFF_CRASHED: 'crashed',
        libvirt.VIR_DOMAIN_SHUTOFF_MIGRATED: 'migrated',
        libvirt.VIR_DOMAIN_SHUTOFF_SAVED: 'saved',
        libvirt.VIR_DOMAIN_SHUTOFF_FAILED: 'failed',
        libvirt.VIR_DOMAIN_SHUTOFF_FROM_SNAPSHOT: 'from_snapshot',
    },
    libvirt.VIR_DOMAIN_CRASHED: {
        libvirt.VIR_DOMAIN_CRASHED_UNKNOWN: 'unknown',
        libvirt.VIR_DOMAIN_CRASHED_PANICKED: 'panicked',
    },
    libvirt.VIR_DOMAIN_PMSUSPENDED: {
        libvirt.VIR_DOMAIN_PMSUSPENDED_UNKNOWN: 'unknown',
    },
}

DOMAIN_INTERFACE_ADDRESSES_SOURCES_LOOKUP = {
    'lease': libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE,
    'agent': libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_AGENT,
    'arp': libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_ARP,
}


def describe_domain(vir_dom, interfaces_addresses=None):
    # type: (libvirt.virDomain, str) -> dict
    state, reason = vir_dom.state()
    xml = vir_dom.XMLDesc()
    desc = {
        'name': vir_dom.name(),
        'xml': xml,
        'desc': from_xml(xml),
        'id': vir_dom.ID(),
        'uuid': vir_dom.UUIDString(),
        'state': DOMAIN_STATES[state],
        'reason': DOMAIN_STATE_REASONS[state][reason],
    }
    if interfaces_addresses:
        desc['interfaces_addresses'] = vir_dom.interfaceAddresses(DOMAIN_INTERFACE_ADDRESSES_SOURCES_LOOKUP[interfaces_addresses])
    return desc


Unit = IntEnum('Unit', 'k m g t p e')
p = re.compile('((?P<unit1>[b])(ytes?)?)|((?P<unit2>[kmgtpe])((?P<type>[i]?)[b])?)')


def to_bytes(value, unit):
    # type: (int, str) -> int
    m = p.fullmatch(unit.lower())
    if m:
        if m.group('unit1'):
            return value
        elif m.group('unit2'):
            scale = Unit[m.group('unit2')]
            if m.group('type'):
                return value * (1 << (10 * scale))
            else:
                return value * (10 ** (scale * 3))
    raise ValueError('invalid unit: {}'.format(unit))


# TODO: improve this
UNIT_PATHS = {
    'domain': 'KiB',
    'volume': 'bytes',
}


def compare(e1, e2, path):
    path = [path] if not isinstance(path, list) else path
    e1 = copy.copy(e1)
    e2 = copy.copy(e2)

    if isinstance(e1, dict) and isinstance(e2, dict):
        if any('_unit' in e for e in (e1, e2)) and path[0] in UNIT_PATHS.keys():
            if not all('_unit' in e for e in (e1, e2)):
                return False, '.'.join(path), 'missing unit attribute'
            e1bytes = to_bytes(int(e1['__value']), e1['_unit'] or UNIT_PATHS[path[0]])
            e2bytes = to_bytes(int(e2['__value']), e2['_unit'] or UNIT_PATHS[path[0]])
            e1['__value'], e1['_unit'] = str(e1bytes), 'b'
            e2['__value'], e2['_unit'] = str(e2bytes), 'b'
        if len(e1) != len(e2):
            return False, '.'.join(path), 'member count differ'
        if set(e1.keys()) != set(e2.keys()):
            return False, '.'.join(path), 'member names differ'
        for key in e1.keys():
            eq, p, m = compare(e1[key], e2[key], path=path + [key])
            if not eq:
                return False, p, m
    elif isinstance(e1, list) and isinstance(e2, list):
        if len(e1) != len(e2):
            return False, '.'.join(path), 'element count differ'
        for i in range(len(e1)):
            eq, p, m = compare(e1[i], e2[i], path=path + [i])
            if not eq:
                return False, p, m
    elif str(e1) != str(e2):
        return False, '.'.join(path), 'values differ {} != {}'.format(e1, e2)

    return True, None, None


def describe_volume(volume):
    # type: (libvirt.virStorageVol) -> dict
    xml = volume.XMLDesc()
    return {
        'name': volume.name(),
        'path': volume.path(),
        'key': volume.key(),
        'xml': xml,
        'desc': from_xml(xml),
    }


def describe_network(network):
    # type: (libvirt.virNetwork) -> dict
    xml = network.XMLDesc()
    return {
        'name': network.name(),
        'bridgeName': network.bridgeName(),
        'DHCPLeases': network.DHCPLeases(),
        'xml': xml,
        'desc': from_xml(xml),
    }


SCHEMA_LOOKUP = {
    'domainsnapshot': 'domainsnapshot',
    'domain': 'domain',
    'network': 'network',
    'pool': 'storagepool',
    'volume': 'storagevol',
    'capabilities': 'capability',
    'device': 'nodedev',
    'filterbinding': 'nwfilterbinding',
    'filter': 'nwfilter',
    'secret': 'secret',
    'interface': 'interface',
}

SCHEMA_PATH = '/usr/share/libvirt/schemas'


def validate(xml):
    if not VALIDATE:
        return False

    tree = etree.parse(StringIO(xml))

    root = tree.getroot().tag
    schema_name = SCHEMA_LOOKUP[root]

    schema_doc = etree.parse(os.path.join(SCHEMA_PATH, schema_name + '.rng'))
    schema = etree.RelaxNG(schema_doc)
    schema.assertValid(tree)
    return True
