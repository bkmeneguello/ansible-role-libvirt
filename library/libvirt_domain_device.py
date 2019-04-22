#!/usr/bin/python

# Copyright: (c) 2018, Bruno Meneguello
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from xml.etree import ElementTree

import ansible.module_utils.libvirt_utils as util
import libvirt
from ansible.module_utils.basic import AnsibleModule

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: libvirt_domain_device

short_description: TBD

version_added: "2.7"

options:
    state:
        description:
            - TBD
        required: false
    domain:
        description:
            - TBD
        required: true
    alias:
        description:
            - TBD
    type:
        description:
            - TBD
    xml:
        description:
            - TBD
    device:
        description:
            - TBD

author:
    - Bruno Meneguello (@bkmeneguello)
'''

EXAMPLES = '''
TBD
'''

RETURN = '''
TBD
'''

STATE_PRESENT = 'present'
STATE_ABSENT = 'absent'


def run_module():
    module_args = dict(
        state=dict(type='str',
                   choices=[STATE_PRESENT, STATE_ABSENT],
                   default=STATE_PRESENT),
        domain=dict(type='str', required=True),
        alias=dict(type='str'),
        type=dict(type='str',
                  choices=['emulator', 'disk', 'filesystem', 'controller', 'lease', 'hostdev', 'source', 'redirdev',
                           'smartcard', 'interface', 'input', 'hub', 'graphics', 'video', 'parallel', 'serial',
                           'console', 'channel', 'sound', 'watchdog', 'memballoon', 'rng', 'tpm', 'nvram', 'panic',
                           'shmem', 'memory', 'iommu', 'vsock']),
        device=dict(type='dict'),
        xml=dict(type='str'),
        update=dict(type='bool', default=False),
    )
    module_args.update(util.common_args)

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=module_args,
        mutually_exclusive=[
            ['device', 'xml'],
            ['alias', 'type'],
        ],
        required_if=[
            ['state', STATE_PRESENT, ['domain', 'xml'], True],
            ['state', STATE_ABSENT, ['alias', 'domain', 'xml'], True],
        ],
    )

    state = module.params['state']
    domain = module.params['domain']

    device_type = module.params['type']
    device = module.params['device']
    if module.params['xml'] is not None:
        device = util.from_xml(module.params['xml'])

    alias = module.params['alias'] or device.get('alias', {}).get('_name')
    if alias and not alias.startswith('ua-'):
        module.fail_json(msg='alias must have "ua-" prefix', **result)

    update = module.params['update']

    conn = util.get_conn(module.params)  # type: libvirt.virConnect
    if conn is None:
        module.fail_json(msg='cannot open connection to libvirt', **result)

    try:
        vir_dom = conn.lookupByName(domain)  # type: libvirt.virDomain
    except libvirt.libvirtError:
        module.fail_json(msg='domain not found', **result)

    # TODO: Check if device already exists. The rules are complex.
    # search disk by <target dev='name'/> then by <source file='name'/>
    if state == STATE_PRESENT:
        xml = encode_device(device_type, device)
        if alias:
            if not alias_exists(vir_dom, device_type, alias):
                vir_dom.attachDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_CURRENT)
                result['changed'] = True
        else:
            vir_dom.attachDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_CURRENT)
            result['changed'] = True
    elif state == STATE_ABSENT:
        if alias:
            if alias_exists(vir_dom, device_type, alias):
                vir_dom.detachDeviceAlias(alias, libvirt.VIR_DOMAIN_AFFECT_CURRENT)
                result['changed'] = True
        else:
            xml = encode_device(device_type, device)
            vir_dom.detachDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_CURRENT)
            result['changed'] = True  # TODO: Check if has changed

    module.exit_json(**result)


def alias_exists(vir_dom, device_type, alias):  # type: (libvirt.virDomain, str, str) -> bool
    root = ElementTree.fromstring(vir_dom.XMLDesc())  # type: ElementTree.Element
    return bool(root.findall('./devices/%s/alias[@name="%s"]' % (device_type, alias)))


def encode_device(device_type, device):
    xml = util.to_xml({device_type: device})
    return util.xml_to_str(xml)


def main():
    run_module()


if __name__ == '__main__':
    main()
