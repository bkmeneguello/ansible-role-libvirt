import os

import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_vm(host):
    cmd = host.run('virsh domstate sample')

    assert cmd.stdout == 'running'
