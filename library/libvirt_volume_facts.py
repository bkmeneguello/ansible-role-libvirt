#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
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
module: libvirt_domain_volume_facts

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
        name=dict(type='str'),
        pool=dict(type='str', required=True),
        all=dict(type='bool', default=False),
    )
    module_args.update(util.common_args)

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        mutually_exclusive=[
            ['name', 'all']
        ]
    )

    name = module.params['name']
    pool = module.params['pool']
    show_all = module.params['all']

    conn = util.get_conn(module.params)  # type: libvirt.virConnect
    if conn is None:
        module.fail_json(msg='Cannot open connection to libvirt', **result)

    try:
        vir_pool = conn.storagePoolLookupByName(pool)
        if name:
            try:
                vir_vol_list = vir_pool.storageVolLookupByName(name)
                result['exists'] = True
                result.update(util.describe_volume(vir_vol_list))
            except libvirt.libvirtError:
                result['exists'] = False
        else:
            vir_vol_list = vir_pool.listAllVolumes() if show_all else vir_pool.listVolumes()
            desc_list = [util.describe_volume(vir_vol) for vir_vol in vir_vol_list]
            result['list'] = desc_list
            result['exists'] = bool(desc_list)
    except libvirt.libvirtError as e:
        module.fail_json(msg='Cannot find pool {}'.format(pool), e=e.get_error_message())

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
