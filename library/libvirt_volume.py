#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
import os

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
module: libvirt_domain_volume

short_description: TBD

version_added: "2.7"

description:
    - "https://libvirt.org/formatstorage.html#StorageVol"

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
        state=dict(type='str', choices=['absent', 'present'], default='present'),
        name=dict(type='str'),
        pool=dict(type='str', required=True),
        volume=dict(type='dict'),
        xml=dict(type='str'),
        upload=dict(type='path'),
        resize=dict(type='int'),
    )
    module_args.update(util.common_args)

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=module_args,
        mutually_exclusive=[
            ['volume', 'xml']
        ],
        required_if=[
            ['state', 'present', ['volume', 'xml'], True],
            ['state', 'absent', ['name']]
        ]
    )

    state = module.params['state']
    pool = module.params['pool']
    upload = module.params['upload']
    resize = module.params['resize']

    volume = module.params['volume']
    if module.params['xml'] is not None:
        volume = util.from_xml(module.params['xml'])

    name = module.params['name'] or volume['name']
    if not name.strip():
        module.fail_json(msg='Missing volume name', **result)

    conn = util.get_conn(module.params)  # type: libvirt.virConnect
    if conn is None:
        module.fail_json(msg='Cannot open connection to libvirt', **result)

    vir_pool = None
    try:
        vir_pool = conn.storagePoolLookupByName(pool)
    except libvirt.libvirtError:
        pass

    vir_vol = None
    if vir_pool is not None:
        try:
            vir_vol = vir_pool.storageVolLookupByName(name)
        except libvirt.libvirtError:
            pass

    if state == 'absent':
        if vir_vol is not None:
            vir_vol.delete()
            result['name'] = vir_vol.name()
            result['changed'] = True
    elif state == 'present':
        if vir_vol is None:
            xml = encode_volume(volume)
            vir_vol = vir_pool.createXML(xml)
            result['changed'] = True
            result.update(util.describe_volume(vir_vol))

            if upload is not None:
                size = os.path.getsize(upload)
                if not module.check_mode:
                    stream = conn.newStream()
                    vir_vol.upload(stream, 0, size)
                    with open(upload, 'rb') as f:
                        stream.sendAll(lambda _, data, file_: file_.read(data), f)
                    stream.finish()
                result['uploaded'] = upload
                result['uploaded_bytes'] = size

            if resize is not None:
                vir_vol.resize(resize)
                result['resized'] = resize
        else:
            # TODO
            result.update(util.describe_volume(vir_vol))

    module.exit_json(**result)


def encode_volume(volume):
    xml = util.to_xml({'volume': volume})
    return util.xml_to_str(xml)


def main():
    run_module()


if __name__ == '__main__':
    main()
