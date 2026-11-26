"""Validate the laboratory policy against `docker compose config --format json`."""
import json
import sys


def validate(config):
    errors = []
    services = config.get('services') if isinstance(config, dict) else None
    if not isinstance(services, dict) or not services:
        return ['services must be a non-empty object']

    def require(condition, service, message):
        if not condition:
            errors.append(f'{service}: {message}')

    for name, service in services.items():
        if not isinstance(service, dict):
            errors.append(f'{name}: service must be an object')
            continue
        require(service.get('user') == '65532:65532', name, 'user must be 65532:65532')
        ports = service.get('ports', [])
        require(isinstance(ports, list) and bool(ports) and all(
            isinstance(port, dict) and port.get('host_ip') == '127.0.0.1'
            and port.get('target') == 3000 and str(port.get('published')) == '3000'
            and port.get('protocol', 'tcp') == 'tcp' for port in ports
        ), name, 'publish only 127.0.0.1:3000:3000/tcp')
        require(not service.get('privileged'), name, 'privileged mode is forbidden')
        for key in ('network_mode', 'pid', 'ipc'):
            require(service.get(key) != 'host', name, f'{key}=host is forbidden')
        require(service.get('cap_drop') == ['ALL'] and not service.get('cap_add'), name, 'drop ALL capabilities without adding any')
        require(service.get('security_opt') == ['no-new-privileges:true'], name, 'require no-new-privileges:true without overrides')
        require(not any(service.get(key) for key in
                        ('volumes', 'volumes_from', 'devices', 'configs', 'secrets', 'use_api_socket')),
                name, 'host mounts, persistent volumes, devices and API socket access are forbidden')
        for key, maximum in (('pids_limit', 256), ('mem_limit', 1073741824), ('cpus', 2)):
            value = service.get(key)
            if key == 'mem_limit' and isinstance(value, str) and value.isdecimal():
                value = int(value)
            require(isinstance(value, (int, float)) and not isinstance(value, bool)
                    and 0 < value <= maximum, name, f'{key} must be positive and at most {maximum}')
        health = service.get('healthcheck', {})
        test = health.get('test', []) if isinstance(health, dict) else []
        require(isinstance(health, dict) and not health.get('disable')
                and isinstance(test, list) and len(test) >= 3
                and test[:2] == ['CMD', '/nodejs/bin/node'], name, 'require a Node exec healthcheck')
    return errors


def main():
    try:
        errors = validate(json.load(sys.stdin))
    except (ValueError, TypeError) as error:
        print(json.dumps({'passed': False, 'errors': [f'Invalid Compose JSON: {error}']}))
        return 2
    print(json.dumps({'passed': not errors, 'errors': errors}, indent=2))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
