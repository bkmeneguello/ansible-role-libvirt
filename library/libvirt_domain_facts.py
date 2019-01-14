#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
import libvirt
from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.libvirt_utils as util

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: libvirt_domain_facts

short_description: TBD

version_added: "2.7"

description:
    - ""

options:
    name:
        description:
            - TBD
        required: false

author:
    - Your Name (@bkmeneguello)
'''

EXAMPLES = '''
# Pass in a message
- name: Test with a message
  my_new_test_module:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_new_test_module:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_new_test_module:
    name: fail me
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
message:
    description: The output message that the sample module generates
'''


def run_module():
    module_args = dict(
        name=dict(type='str', required=False),
        interfaces_addresses=dict(type='str', required=False, choices=['lease', 'agent', 'arp']),
    )
    module_args.update(util.common_args)

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    name = module.params['name']
    interfaces_addresses = module.params['interfaces_addresses']

    conn = util.get_conn(module.params)  # type: libvirt.virConnect
    if conn is None:
        module.fail_json(msg='Cannot open connection to libvirt', **result)

    if name:
        try:
            vir_dom = conn.lookupByName(name)
            result['exists'] = True
            result.update(util.describe_domain(vir_dom, interfaces_addresses))
        except libvirt.libvirtError:
            result['exists'] = False
    else:
        desc_list = [util.describe_domain(vir_dom, interfaces_addresses) for vir_dom in conn.listAllDomains()]
        result['list'] = desc_list
        result['exists'] = bool(desc_list)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
