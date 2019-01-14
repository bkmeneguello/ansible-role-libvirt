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
module: libvirt_domain

short_description: TBD

version_added: "2.7"

description:
    - "https://libvirt.org/formatdomain.html"

options:
    state:
        description:
            - TBD
        required: false
    name:
        description:
            - TBD
        required: false
    xml:
        description:
            - TBD
        required: false
    domain:
        description:
            - TBD
        required: false

author:
    - Your Name (@bkmeneguello)
'''

EXAMPLES = '''
# Define a domain using XML
- name: Define domain
  libvirt_domain:
    xml: >
      <domain type='kvm'>
        <name>web</name>
        <memory unit='G'>1</memory>
        <vcpu>1</vcpu>
        <os>
          <type arch='x86_64' machine='pc'>hvm</type>
          <boot dev='hd'/>
        </os>
        <devices>
          <emulator>/usr/bin/kvm-spice</emulator>
          <disk type='volume' device='disk'>
            <driver name='qemu' type='qcow2'/>
            <source pool='default' volume='web-disk'/>
            <target dev='vda' bus='virtio'/>
          </disk>
          <disk type='volume' device='cdrom'>
            <driver name='qemu'/>
            <source pool='default' volume='web-cidata'/>
            <target dev='hda' bus='ide'/>
            <readonly/>
          </disk>
          <interface type='network'>
            <source network='default'/>
          </interface>
          <graphics type='spice' autoport='yes'/>
        </devices>
      </domain>

# Define a domain using YAML
- name: Define domain
  libvirt_domain:
    domain:
      _type: kvm
      name: web
      memory:
        _unit: G
        __value: 1
      vcpu: 1
      os:
        type:
          _arch: x86_64
          _machine: pc-i440fx-bionic
          __value: hvm
      devices:
        emulator: /usr/bin/kvm-spice
        disk:
          - _type: volume
            _device: disk
            driver:
              _name: qemu
              _type: qcow2
            source:
              _pool: default
              _volume: web-disk
            target:
              _dev: vda
              _bus: virtio
          - _type: volume
            _device: cdrom
            driver:
              _name: qemu
            source:
              _pool: default
              _volume: web-cidata
            target:
              _dev: hda
              _bus: ide
            readonly: true
        interface:
          - _type: network
            source:
              _network: default
        graphics:
          _type: spice
          _autoport: 'yes'

# Undefine a domain
- name: Ensure domain is not defined
  libvirt_domain:
    state: undefined 
    name: web
    undefine_snapshots_metadata: true
'''

RETURN = '''
name:
    description: TBD
    type: str
xml:
    description: TBD
    type: str
id:
    description: TBD
    type: str
uuid:
    description: TBD
    type: str
state:
    description: TBD
    type: str
reason:
    description: TBD
    type: str
'''

STATE_DESTROYED = 'destroyed'
STATE_DEFINED = 'defined'
STATE_CREATED = 'created'
STATE_UNDEFINED = 'undefined'
STATE_STOPPED = 'stopped'


def run_module():
    module_args = dict(
        state=dict(type='str',
                   choices=[STATE_DEFINED, STATE_CREATED, STATE_DESTROYED, STATE_UNDEFINED, STATE_STOPPED],
                   default=STATE_CREATED),
        name=dict(type='str'),
        domain=dict(type='dict'),
        xml=dict(type='str'),
        persistent=dict(type='bool', default=True),
        destroy_graceful=dict(type='bool', default=True),
        undefine_destroy=dict(type='bool', default=True),
        undefine_managed_save=dict(type='bool', default=False),
        undefine_snapshots_metadata=dict(type='bool', default=False),
        undefine_keep_nvram=dict(type='bool', default=False),
        undefine_nvram=dict(type='bool', default=False),
        shutdown_acpi_power_btn=dict(type='bool', default=False),
        shutdown_guest_agent=dict(type='bool', default=False),
        shutdown_initctl=dict(type='bool', default=False),
        shutdown_signal=dict(type='bool', default=False),
        shutdown_paravirt=dict(type='bool', default=False),
        # undefine_remove_all_storage=dict(type='bool', default=False),  # TODO
        # undefine_storage=dict(type='list'),  # TODO
        # undefine_wipe_storage=dict(type='bool', default=False),  # TODO
    )
    module_args.update(util.common_args)

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=module_args,
        mutually_exclusive=[
            ['domain', 'xml', 'name'],
            ['undefine_keep_nvram', 'undefine_nvram'],
        ],
        required_if=[
            ['state', STATE_CREATED, ['domain', 'xml'], True],
            ['state', STATE_DEFINED, ['domain', 'xml'], True],
            ['state', STATE_DESTROYED, ['name']],
        ],
    )

    domain = module.params['domain']
    if module.params['xml'] is not None:
        domain = util.from_xml(module.params['xml'])

    state = module.params['state']
    name = module.params['name'] or domain['name']
    if not name.strip():
        module.fail_json(msg='missing domain name', **result)
    persistent = module.params['persistent']
    if state == STATE_DEFINED and not persistent:
        module.fail_json(msg='persistent cannot be false when state is defined')
    destroy_graceful = module.params['destroy_graceful']
    undefine_destroy = module.params['undefine_destroy']
    undefine_managed_save = module.params['undefine_managed_save']
    undefine_snapshots_metadata = module.params['undefine_snapshots_metadata']
    undefine_keep_nvram = module.params['undefine_keep_nvram']
    undefine_nvram = module.params['undefine_nvram']
    shutdown_acpi_power_btn = module.params['shutdown_acpi_power_btn']
    shutdown_guest_agent = module.params['shutdown_guest_agent']
    shutdown_initctl = module.params['shutdown_initctl']
    shutdown_signal = module.params['shutdown_signal']
    shutdown_paravirt = module.params['shutdown_paravirt']

    conn = util.get_conn(module.params)  # type: libvirt.virConnect
    if conn is None:
        module.fail_json(msg='cannot open connection to libvirt', **result)

    try:
        vir_dom = conn.lookupByName(name)  # type: libvirt.virDomain
        if domain:
            domain['uuid'] = vir_dom.UUIDString()
    except libvirt.libvirtError:
        vir_dom = None

    if state == STATE_DEFINED:
        if vir_dom is None:
            result['changed'] = True
            vir_dom = define_domain(conn, domain)
            result.update(util.describe_domain(vir_dom))
        else:
            changed, path, cause = domain_has_changed(vir_dom, domain)
            if changed:
                result['changed'] = True
                result['changed_path'] = path
                result['changed_cause'] = cause
                vir_dom = define_domain(conn, domain)
                changed, path, cause = domain_has_changed(vir_dom, domain)
                if changed:
                    module.warn('the provided domain definition was modified by the virtualization platform, '
                                'check the current definition to avoid unnecessary updates')
                    result['domain'] = domain
                    result['changed_path'] = path
                    result['changed_cause'] = cause
                result.update(util.describe_domain(vir_dom))
    elif state == STATE_CREATED:
        if vir_dom is None:
            result['changed'] = True
            if persistent:
                vir_dom = define_domain(conn, domain)
                vir_dom.create()
            else:
                vir_dom = create_domain(conn, domain)
            result.update(util.describe_domain(vir_dom))
        else:
            if vir_dom.isActive():
                # TODO: detect changes
                changed, path, cause = domain_has_changed(vir_dom, domain, active=True)
                if changed:
                    module.warn('some configurations cannot be applied to running domain')
                    module.warn('{}: {}'.format(path, cause))
            if persistent:
                result['changed'] = True
                vir_dom = define_domain(conn, domain)
                if not vir_dom.isActive():
                    vir_dom.create()
                result.update(util.describe_domain(vir_dom))
            elif vir_dom.isPersistent():
                result['changed'] = True
                undefine_domain(vir_dom,
                                undefine_managed_save,
                                undefine_snapshots_metadata,
                                undefine_keep_nvram,
                                undefine_nvram)
    elif state == STATE_UNDEFINED:
        if vir_dom is not None:
            destroy = vir_dom.isActive() and undefine_destroy
            if vir_dom.isPersistent():
                result['changed'] = True
                undefine_domain(vir_dom,
                                undefine_managed_save,
                                undefine_snapshots_metadata,
                                undefine_keep_nvram,
                                undefine_nvram)
            if destroy:
                result['changed'] = True
                destroy_domain(vir_dom, destroy_graceful)
    elif state == STATE_DESTROYED:
        if vir_dom is not None:
            result['changed'] = True
            destroy_domain(vir_dom, destroy_graceful)
    elif state == STATE_STOPPED:
        if vir_dom is None:
            module.warn('domain does not exists so cannot shutdown')
        else:
            result['changed'] = True
            domain_shutdown(vir_dom,
                            shutdown_acpi_power_btn,
                            shutdown_guest_agent,
                            shutdown_initctl,
                            shutdown_paravirt,
                            shutdown_signal)

    module.exit_json(**result)


def create_domain(conn, domain):
    xml = encode_domain(domain)
    vir_dom = conn.createXML(xml)
    return vir_dom


def define_domain(conn, domain):
    xml = encode_domain(domain)
    vir_dom = conn.defineXML(xml)
    return vir_dom


def undefine_domain(vir_dom,
                    undefine_managed_save,
                    undefine_snapshots_metadata,
                    undefine_keep_nvram,
                    undefine_nvram):
    flags = 0
    flags |= libvirt.VIR_DOMAIN_UNDEFINE_MANAGED_SAVE if undefine_managed_save else 0
    flags |= libvirt.VIR_DOMAIN_UNDEFINE_SNAPSHOTS_METADATA if undefine_snapshots_metadata else 0
    flags |= libvirt.VIR_DOMAIN_UNDEFINE_KEEP_NVRAM if undefine_keep_nvram else 0
    flags |= libvirt.VIR_DOMAIN_UNDEFINE_NVRAM if undefine_nvram else 0
    return vir_dom.undefineFlags(flags)


def destroy_domain(domain, graceful):
    flags = libvirt.VIR_DOMAIN_DESTROY_GRACEFUL if graceful else 0
    return domain.destroyFlags(flags)


def domain_shutdown(vir_dom,
                    shutdown_acpi_power_btn,
                    shutdown_guest_agent,
                    shutdown_initctl,
                    shutdown_paravirt,
                    shutdown_signal):
    flags = libvirt.VIR_DOMAIN_SHUTDOWN_DEFAULT
    flags |= libvirt.VIR_DOMAIN_SHUTDOWN_ACPI_POWER_BTN if shutdown_acpi_power_btn else 0
    flags |= libvirt.VIR_DOMAIN_SHUTDOWN_GUEST_AGENT if shutdown_guest_agent else 0
    flags |= libvirt.VIR_DOMAIN_SHUTDOWN_INITCTL if shutdown_initctl else 0
    flags |= libvirt.VIR_DOMAIN_SHUTDOWN_SIGNAL if shutdown_signal else 0
    flags |= libvirt.VIR_DOMAIN_SHUTDOWN_PARAVIRT if shutdown_paravirt else 0
    return vir_dom.shutdownFlags(flags)


def domain_has_changed(vir_dom, domain, active=False):
    flags = libvirt.VIR_DOMAIN_XML_SECURE
    flags |= libvirt.VIR_DOMAIN_XML_INACTIVE if not active else 0
    current = util.from_xml(vir_dom.XMLDesc(flags))
    eq, path, cause = util.compare(domain, current, 'domain')
    return not eq, path, cause


def encode_domain(domain):
    xml = util.to_xml({'domain': domain})
    return util.xml_to_str(xml)


def main():
    run_module()


if __name__ == '__main__':
    main()
