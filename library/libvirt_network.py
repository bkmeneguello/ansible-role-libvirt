#!/usr/bin/python

# Copyright: (c) 2018, Bruno Meneguello
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

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
TBD
https://libvirt.org/formatnetwork.html
'''

EXAMPLES = '''
TBD
'''

RETURN = '''
TCB
'''


STATE_DEFINED = 'defined'
STATE_STARTED = 'started'
STATE_UNDEFINED = 'undefined'
STATE_DESTROYED = 'destroyed'


def run_module():
    module_args = dict(
        state=dict(type='str',
                   choices=[STATE_DEFINED, STATE_STARTED, STATE_UNDEFINED, STATE_DESTROYED],
                   default=STATE_STARTED),
        name=dict(type='str'),
        network=dict(type='dict'),
        xml=dict(type='str'),
        autostart=dict(type='bool', default=True),
        persistent=dict(type='bool', default=True),
        undefine_destroy=dict(type='bool', default=True),
    )
    module_args.update(util.common_args)

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=module_args,
        mutually_exclusive=[
            ['domain', 'xml', 'name'],
        ],
        required_if=[
            ['state', STATE_STARTED, ['network', 'xml'], True],
            ['state', STATE_DEFINED, ['network', 'xml'], True],
            ['state', STATE_UNDEFINED, ['name']],
            ['state', STATE_DESTROYED, ['name']],
        ],
    )

    network = module.params['network']
    if module.params['xml'] is not None:
        network = util.from_xml(module.params['xml'])

    state = module.params['state']
    name = module.params['name'] or network['name']
    if not name.strip():
        module.fail_json(msg='missing network name', **result)
    autostart = module.params['autostart']
    persistent = module.params['persistent']
    if state == STATE_DEFINED and not persistent:
        module.fail_json(msg='persistent cannot be false when state is defined')
    undefine_destroy = module.params['undefine_destroy']

    conn = util.get_conn(module.params)  # type: libvirt.virConnect
    if conn is None:
        module.fail_json(msg='cannot open connection to libvirt', **result)

    try:
        vir_net = conn.networkLookupByName(name)  # type: libvirt.virNetwork
        if network:
            network['uuid'] = vir_net.UUIDString()
    except libvirt.libvirtError as e:
        vir_net = None

    if state == STATE_DEFINED:
        if vir_net is None:
            result['changed'] = True
            vir_net = define_network(conn, network, autostart)
            result.update(util.describe_network(vir_net))
        else:
            changed, path, cause = network_has_changed(vir_net, network)
            if changed:
                result['changed'] = True
                result['changed_path'] = path
                result['changed_cause'] = cause
                vir_net = define_network(conn, network, autostart)
                changed, path, cause = network_has_changed(vir_net, network)
                if changed:
                    module.warn('the provided network definition was modified by the virtualization platform, '
                                'check the current definition to avoid unnecessary updates')
                    result['network'] = network
                    result['changed_path'] = path
                    result['changed_cause'] = cause
                result.update(util.describe_network(vir_net))
    elif state == STATE_STARTED:
        if vir_net is None:
            result['changed'] = True
            if persistent:
                vir_net = define_network(conn, network, autostart)
                vir_net.create()
            else:
                vir_net = create_network(conn, network)
            result.update(util.describe_network(vir_net))
        else:
            if vir_net.isActive():
                # TODO: detect changes
                changed, path, cause = network_has_changed(vir_net, network, active=True)
                if changed:
                    module.warn('some configurations cannot be applied to running network')
                    module.warn('{}: {}'.format(path, cause))
            if persistent:
                result['changed'] = True
                vir_net = define_network(conn, network, autostart)
                if not vir_net.isActive():
                    vir_net.create()
                result.update(util.describe_network(vir_net))
            elif vir_net.isPersistent():
                result['changed'] = True
                undefine_network(vir_net)
    elif state == STATE_UNDEFINED:
        if vir_net is not None:
            destroy = vir_net.isActive() and undefine_destroy
            if vir_net.isPersistent():
                result['changed'] = True
                undefine_network(vir_net)
            if destroy:
                result['changed'] = True
                destroy_network(vir_net)
    elif state == STATE_DESTROYED:
        if vir_net is not None:
            result['changed'] = True
            destroy_network(vir_net)

    module.exit_json(**result)


def create_network(conn, network):
    xml = encode_network(network)
    vir_dom = conn.networkCreateXML(xml)
    return vir_dom


def define_network(conn, domain, autostart):
    xml = encode_network(domain)
    vir_net = conn.networkDefineXML(xml)
    vir_net.setAutostart(autostart)
    return vir_net


def undefine_network(vir_net):
    # type: (libvirt.virNetwork) -> Any
    return vir_net.undefine()


def destroy_network(vir_net):
    # type: (libvirt.virNetwork) -> Any
    return vir_net.destroy()


def network_has_changed(vir_net, network, active=False):
    # type: (libvirt.virNetwork, dict, bool) -> tuple
    flags = libvirt.VIR_NETWORK_XML_INACTIVE if not active else 0
    current = util.from_xml(vir_net.XMLDesc(flags))
    eq, path, cause = util.compare(network, current, 'network')
    return not eq, path, cause


def encode_network(network):
    # type: (dict) -> str
    xml = util.to_xml({'network': network})
    return util.xml_to_str(xml)


def main():
    run_module()


if __name__ == '__main__':
    main()
