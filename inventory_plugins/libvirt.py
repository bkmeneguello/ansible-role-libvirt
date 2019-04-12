from __future__ import (absolute_import, division, print_function)

import re
from typing import Union, Dict, Any

import libvirt

__metaclass__ = type

from ansible.errors import AnsibleParserError
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable

from xml.etree import ElementTree

DOCUMENTATION = '''
    name: libvirt
    plugin_type: inventory
    short_description: LibVirt inventory source
    version_added: "2.7"
    author:
      - Bruno Meneguello
    description:
        TBD
    extends_documentation_fragment:
      - inventory_cache
    requirements:
      - "Python >= 2.7"
    options:
        uri:
            description: LibVirt connection URI
            env:
              - name: LIBVIRT_URI
            ini:
              - section: libvirt
                key: uri
        host_xpath:
            description: XPath to evaluate against a XML representation of LibVirt interface addresses API call.
            default: ./*/addrs[1]/addr
            env:
              - name: LIBVIRT_HOST_XPATH
            ini:
              - section: libvirt
                key: host_xpath
        state_groups:
            description: If true or if defined as dict of {tpl} produces groups of hosts by state. The 'tpl' attribute
                         is formatted to replace '{}' by state value.
            default: false
        group_by:
            description: List of XPath expressions or a dict of {xpath, tpl} to create groups by attributes. The xpath
                         can, optionally, have an @attr appended, to pick a node attribute instead of the text. The 
                         'tpl' attribute is formatted to replace '{}' by matched value.
            default: []
            type: list
        extra_attributes:
            description: Dictionary of extra attributes to define for each host. The keys are the attribute name and the
                         values are XPath expressions to query the domain.
            default: {}
            type: dict
'''

EXAMPLES = '''
plugin: libvirt
uri: qemu:///system
host_xpath: ./*/addrs[2]/addr
state_groups:
  tpl: state_{}
group_by:
  - xpath: "./devices/interface[@type='network']/source@network"
    tpl: net_{}
  - xpath: "./devices/disk[@type='volume'][@device='cdrom']"
    tpl: cdrom
  - xpath: "./os/type"
    tpl: os_type_{}
  - xpath: ".@type"
    tpl: virt_{}
extra_attributes:
  arch: "./os/type@arch"
  machine: "./os/type@machine"
  emulator: "./devices/emulator"
'''


def dict2xml(values, name):
    root = ElementTree.Element(name)
    return ElementTree.tostring(buildxml(root, values))


def buildxml(root, values):  # type: (ElementTree.Element, Union[Dict, str, Any]) -> ElementTree.Element
    if isinstance(values, dict):
        for k, v in values.items():
            if isinstance(v, (tuple, list)):
                for item in v:
                    s = ElementTree.SubElement(root, k)
                    buildxml(s, item)
            else:
                s = ElementTree.SubElement(root, k)
                buildxml(s, v)
    elif isinstance(values, str):
        root.text = values
    else:
        root.text = str(values)
    return root


def xpath_attrib(xpath):
    return (re.split('@(?=\\w+$)', xpath) + [None])[:2]


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):

    NAME = 'libvirt'

    def __init__(self):
        super(InventoryModule, self).__init__()

    def verify_file(self, path):

        valid = False
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(('libvirt.yaml', 'libvirt.yml')):
                valid = True

        return valid

    def parse(self, inventory, loader, path, cache=False):

        super(InventoryModule, self).parse(inventory, loader, path, cache=cache)

        self._read_config_data(path)

        conn = libvirt.open(self.get_option('uri'))
        if conn is None:
            raise AnsibleParserError('cannot open connection to libvirt')

        for vir_dom in conn.listAllDomains():
            host = vir_dom.name()
            self.inventory.add_host(host)
            self.set_state_group(vir_dom, host)

            if vir_dom.isActive():
                addrs = vir_dom.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE)  # type: dict
                root = ElementTree.fromstring(dict2xml(addrs, 'addrs'))  # type: ElementTree.Element
                addr = root.find(self.get_option('host_xpath'))  # type: ElementTree.Element
                if addr is not None:
                    self.inventory.set_variable(host, 'ansible_host', addr.text)

            self.set_groups(vir_dom, host)
            self.set_extra_attribs(vir_dom, host)

        self.inventory.reconcile_inventory()

    def set_groups(self, vir_dom, host):  # type: (libvirt.virDomain, str) -> None
        root = ElementTree.fromstring(vir_dom.XMLDesc())
        for xpath in self.get_option('group_by'):  # type: str
            tpl = '{}'
            if isinstance(xpath, dict):
                tpl = xpath.get('tpl', tpl)
                xpath = xpath['xpath']

            xpath, attrib = xpath_attrib(xpath)
            try:
                for node in root.findall(xpath):
                    group_name = tpl.format(node.attrib[attrib] if attrib else node.text)
                    if group_name not in self.inventory.get_groups_dict():
                        self.inventory.add_group(group_name)
                    self.inventory.add_child(group_name, host)
            except SyntaxError as e:
                raise AnsibleParserError('invalid XPath provided "{}"'.format(xpath), orig_exc=e)

    def set_extra_attribs(self, vir_dom, host):  # type: (libvirt.virDomain, str) -> None
        root = ElementTree.fromstring(vir_dom.XMLDesc())
        for key, xpath in self.get_option('extra_attributes').items():  # type: str
            xpath, attrib = xpath_attrib(xpath)
            node = root.find(xpath)
            if node is not None:
                value = node.attrib[attrib] if attrib else node.text
                if value:
                    self.inventory.set_variable(host, key, value)

    def set_state_group(self, vir_dom, host):  # type: (libvirt.virDomain, str) -> None
        state_groups = self.get_option('state_groups')
        if state_groups is not False:
            state = 'active' if vir_dom.isActive() else 'inactive'

            if isinstance(state_groups, dict):
                group_name = state_groups.get('tpl', '{}').format(state)
            elif isinstance(state_groups, str):
                group_name = state_groups.format(state)
            else:
                group_name = state

            if group_name not in self.inventory.get_groups_dict():
                self.inventory.add_group(group_name)

            self.inventory.add_child(group_name, host)
