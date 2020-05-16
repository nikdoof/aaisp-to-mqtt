#!/usr/bin/env python

import os
import sys
import logging
import json
from datetime import datetime
import configparser

import paho.mqtt.client as mqtt
import humanfriendly
import requests



LOG = logging.getLogger(__name__)
VERSION = '0.3.0'

AAISP_INFO_URL = 'https://chaos2.aa.net.uk/broadband/info'


def b_to_gb(value):
    """Bytes to Gibibytes"""
    return round(int(value) / (1000**3), 3)


def bps_to_mbps(value):
    """Bits per second to Mbit/sec"""
    return round(int(value) / (1000**2), 3)

def to_human(value):
    """Human readable value"""
    return humanfriendly.format_size(int(value))


# Name, Topic, Key, Formatter, HA Unit Type
VALUES_MAP = [
    ('quota_remaining', 'quota/remaining', 'quota_remaining', int, 'B', 'mdi:gauge'),
    ('quota_remaining_gb', 'quota/remaining/gb', 'quota_remaining', b_to_gb, 'GB', 'mdi:gauge'),
    ('quota_remaining_human', 'quota/remaining/human', 'quota_remaining', to_human, '', 'mdi:gauge'),
    ('quota_monthly', 'quota/monthly', 'quota_monthly', int, 'B', 'mdi:gauge'),
    ('quota_monthly_gb', 'quota/monthly/gb', 'quota_monthly', b_to_gb, 'GB', 'mdi:gauge'),
    ('quota_monthly_human', 'quota/monthly/human', 'quota_monthly', to_human, '', 'mdi:gauge'),
    ('syncrate_up', 'syncrate/up', 'rx_rate', float, 'bit/s', 'mdi:speedometer'),
    ('syncrate_up_mbps', 'syncrate/up/mb', 'rx_rate', bps_to_mbps, 'Mbit/s', 'mdi:speedometer'),
    ('syncrate_up_human', 'syncrate/up/human', 'rx_rate', to_human, '', 'mdi:speedometer'),
    ('syncrate_down', 'syncrate/down', 'tx_rate', float, 'bit/s', 'mdi:speedometer'),
    ('syncrate_down_mbps', 'syncrate/down/mb', 'tx_rate', bps_to_mbps, 'Mbit/s', 'mdi:speedometer'),
    ('syncrate_down_human', 'syncrate/down/human', 'tx_rate', to_human, '', 'mdi:speedometer'),
    ('postcode', 'postcode', 'postcode', str, '', 'mdi:tag-text'),
]


def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(levelname)8s [%(asctime)s] %(message)s')

    if len(sys.argv) > 1:
        filename = os.path.abspath(os.path.expandvars(sys.argv[1]))
        # load the config
        if os.path.exists(filename):
            config = configparser.ConfigParser()
            config.read(filename)
        else:
            LOG.fatal('Configuration file %s does not exist', filename)

        # check it has the correct sections
        diff = set(['aaisp', 'mqtt']) - set(config.sections())
        if len(diff) > 0:
            LOG.fatal('Sections are missing from the configuration file: %s', ','.join(diff))

        aaisp_username = config.get('aaisp', 'username')
        aaisp_password = config.get('aaisp', 'password')
        mqtt_broker = config.get('mqtt', 'broker')
        mqtt_port = int(config.get('mqtt', 'port', fallback='1883'))
        mqtt_username = config.get('mqtt', 'username', fallback=None)
        mqtt_password = config.get('mqtt', 'password', fallback=None)
        mqtt_topic_prefix = config.get('mqtt', 'topic_prefix', fallback='aaisp')
        homeassistant_enabled = config.get('homeassistant', 'enabled', fallback='false') == 'true'
        homeassistant_discovery_prefix = config.get('homeassistant', 'discovery_prefix', fallback='homeassistant')
    else:
        # Use the environment
        aaisp_username = os.environ.get('AAISP_USERNAME')
        aaisp_password = os.environ.get('AAISP_PASSWORD')
        mqtt_broker = os.environ.get('MQTT_BROKER') or 'localhost'
        mqtt_port = int(os.environ.get('MQTT_PORT') or '1883')
        mqtt_username = os.environ.get('MQTT_USERNAME')
        mqtt_password = os.environ.get('MQTT_PASSWORD')
        mqtt_topic_prefix = os.environ.get('MQTT_TOPIC_PREFIX') or 'aaisp'
        homeassistant_enabled = (os.environ.get('HOMEASSISTANT_ENABLED') or 'false') == 'true'
        homeassistant_discovery_prefix = os.environ.get('HOMEASSISTANT_DISCOVERY_PREFIX') or 'homeassistant'

    if aaisp_username is None or aaisp_password is None:
        LOG.fatal('Username or Password missing for AAISP')
        return 1

    # attempt to get details from aaisp
    LOG.info('Connecting to AAISP CHAOSv2 endpoint as %s', aaisp_username)
    response = requests.get(AAISP_INFO_URL, params={
        'control_login': aaisp_username,
        'control_password': aaisp_password
    })
    if not response.status_code == requests.codes.ok:
        LOG.error('Error connecting to AAISP CHAOSv2 endpoint: %s' % response.body)
        return 1

    data = response.json()

    # Check for response errors
    if 'info' not in data:
        if 'error' in data:
            LOG.fatal('Error encounted: %s' % data['error'])
        else:
            LOG.fatal('info section not found in AAISP CHAOSv2 response')
        return 1

    circuits = data['info']
    LOG.info('Got %s circuits', len(circuits))
    if len(circuits) == 0:
        LOG.fatal('No circuits returned from AAISP CHAOSv2')

    # work out unique line IDs and logins
    logins = set(c['login'] for c in circuits)
    lines = set(c['ID'] for c in circuits)
    LOG.info('* Lines: %s', ', '.join(lines))
    LOG.info('* Logins: %s', ', '.join(logins))

    # connect to the broker
    LOG.info('Connecting to MQTT broker %s:%s', mqtt_broker, mqtt_port)
    client = mqtt.Client()
    client.max_inflight_messages_set(100)

    # do auth?
    if mqtt_username is not None and mqtt_password is not None:
        client.username_pw_set(mqtt_username, mqtt_password)

    try:
        client.connect(mqtt_broker, mqtt_port, 60)
    except Exception:
        LOG.exception('Error connecting to MQTT')
        return 1
    else:
        LOG.info('Connected to MQTT Server %s', mqtt_broker)

    # version and indexes
    publish(client=client, topic='%s/$version' % (mqtt_topic_prefix), payload=VERSION)
    publish(client=client, topic='%s/$lines' % (mqtt_topic_prefix), payload=','.join(lines))
    publish(client=client, topic='%s/$logins' % (mqtt_topic_prefix), payload=','.join(logins))
    publish(client=client, topic='%s/last_update' % (mqtt_topic_prefix), payload=datetime.now().timestamp())
    LOG.info('Published version and index messages')

    # publish per circuit
    for circuit in circuits:
        # If homeassistant is enabled, publish the sensor configs
        if homeassistant_enabled:
            LOG.debug('Publishing Homeassistant configuration.')
            publish_circuit_config(client, circuit, mqtt_topic_prefix, homeassistant_discovery_prefix)

        # Publish the states
        publish_circuit_state(client, circuit, mqtt_topic_prefix)
    LOG.info('Published details for %s circuits', len(circuits))

    # disconnect
    LOG.info('Disconnecting from MQTT')
    client.disconnect()


def publish_circuit_state(client, circuit, mqtt_topic_prefix):
    prefix = '%s/login/%s' % (mqtt_topic_prefix, circuit['login'])
    for _, topic, key, formatter, _, _ in VALUES_MAP:
        topic = '%s/%s' % (prefix, topic)
        publish(client=client, topic=topic, payload=formatter(circuit[key]))


def publish_circuit_config(client, circuit, mqtt_topic_prefix, mqtt_discovery_prefix):
    for name, topic, _, _, unit, icon in VALUES_MAP:
        login = circuit['login'].replace('@', '_').replace('.', '_')
        config_topic = '%s/sensor/%s/%s/config' % (mqtt_discovery_prefix, login, name)
        unique_id = '%s_%s' % (login, name)

        data = {
            'name': '%s %s' % (circuit['login'], name),
            'icon': icon,
            'state_topic':  '%s/login/%s/%s' % (mqtt_topic_prefix, circuit['login'], topic),
            'unique_id': unique_id,
            'unit_of_measurement': unit,
            'device': {
                'identifiers': circuit['login'],
                'name': 'AAISP Circuit %s (%s)' % (circuit['login'], circuit['postcode']),
                'sw_version': VERSION,
            }
        }
        publish(client, config_topic, payload=json.dumps(data), retain=True)


def publish(client, topic, payload, retain=False):
    result = client.publish(topic=topic, payload=payload, qos=0, retain=retain)
    if result[0] != 0:
        LOG.fail('MQTT publish failure: %s %s', topic, payload)


if __name__ == '__main__':
    sys.exit(main())
