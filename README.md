# Ansible Role - LibVirt

An Ansible Role to manage virtual machines with LibVirt

## Requirements

- python libvirt package

## Role Variables

None.

## Dependencies

None.

## Example Playbook

```yaml
- hosts: all
  roles:
    - bkmeneguello.libvirt
  tasks:
    - libvirt_network:
        state: defined
        network:
          name: sample
          forward:
            _mode: nat
          domain:
            _name: virtual
          ip:
            _address: 192.168.200.1
            _netmask: 255.255.255.0
            dhcp:
              range:
                _start: 192.168.200.2
                _end: 192.168.200.254
      register: network
    - libvirt_volume:
        state: present
        pool: default
        upload: /some/local/path/sample.qcow2
        volume:
          name: 'sample-disk'
          format:
            _type: qcow2
          capacity:
            _unit: G
            __value: 2
      register: volume
    - libvirt_domain:
        state: created
        domain:
          _type: kvm
            name: sample
            memory:
              _unit: G
              __value: 2
            os:
              type:
                _arch: x86_64
                __value: hvm
            devices:
              disk:
                - _type: volume
                  _device: disk
                  driver:
                    _name: qemu
                    _type: qcow2
                  source:
                    _pool: default
                    _volume: '{{ volume.name }}'
                  target:
                    _dev: vda
                    _bus: virtio
              interface:
                - _type: network
                  source:
                    _network: '{{ network.name }}'
      
```

## License

MIT
