# AAISP to MQTT Service #

A script to publish [Andrews & Arnold / AAISP](http://aa.net.uk) broadband quota and sync rates to [MQTT](http://mqtt.org/). It uses version 2 of AAISPs [CHAOS](https://support.aa.net.uk/CHAOS) API. Useful for integrating and displaying AAISP line properties in home automation applications, such as [Home Assistant](https://home-assistant.io/) or [openHAB](http://www.openhab.org/).

This is a fork of the original [aaisp2mqtt project](https://github.com/natm/aaisp-to-mqtt) by [natm](http://github.com/natm) with the aim to increase integration with Home Assistant and fixing a few minor issues.

## Features ##

* Home Assistant auto discovery


## Use cases ##

* Displaying line properties in Home Assistant / openHAB
* Asking Amazon Alexa Echo for the remaining quota
* Flashing a light in the office when the downstream sync rate drops
* Sending line info to [Crouton](https://github.com/edfungus/Crouton)

## Configuration ##

Create a config file, for example in /etc/aaisp-mqtt.conf, minimal viable with no MQTT authentication:

```
[aaisp]
username = aa000@x.a
password = LongAccountPassword

[mqtt]
broker = 127.0.0.1
port = 1883
topic_prefix = aaisp
```

You can also optionally specify MQTT username and password:

```
[aaisp]
username = aa000@x.a
password = LongAccountPassword

[mqtt]
broker = 127.0.0.1
port = 1883
topic_prefix = aaisp
username = aaisp-service
password = AnotherLongPassword
```

Install the dependencies:

```
$ pip install -r requirements.txt
```

Run the service:

```
$ aaisp2mqtt.py /etc/aaisp-mqtt.conf
```

It will display debug output similar to:

```
INFO [2020-05-16 14:49:05,142] Connecting to AAISP CHAOSv2 endpoint as xx000@x.a
INFO [2020-05-16 14:49:06,002] Got 1 circuits
INFO [2020-05-16 14:49:06,003] * Lines: 41429
INFO [2020-05-16 14:49:06,004] * Logins: xx000@x.0
INFO [2020-05-16 14:49:06,005] Connecting to MQTT broker 127.0.0.1:1883
INFO [2020-05-16 14:49:06,016] Connected to MQTT Server 127.0.0.1
INFO [2020-05-16 14:49:06,023] Published version and index messages
INFO [2020-05-16 14:49:06,031] Published details for 1 circuits
INFO [2020-05-16 14:49:06,033] Disconnecting from MQTT
```

Schedule the script via a crontab to run every hour or 30 minutes.

## Topics ##

Single account:

```
aaisp/$lines                                    32891
aaisp/$logins                                   gb12@a.1
aaisp/$version                                  0.1
aaisp/login/gb12@a.1/postcode                   SA65 9RR
aaisp/login/gb12@a.1/quota/monthly              100000000000
aaisp/login/gb12@a.1/quota/monthly/human        100 GB
aaisp/login/gb12@a.1/quota/remaining            84667320096
aaisp/login/gb12@a.1/quota/remaining/human      84.67 GB
aaisp/login/gb12@a.1/syncrate/down              5181000
aaisp/login/gb12@a.1/syncrate/down/human        5.18 MB
aaisp/login/gb12@a.1/syncrate/up                1205000
aaisp/login/gb12@a.1/syncrate/up/human          1.21 MB
```

For multiple accounts:

```
aaisp/$lines                                    32891,37835,37964
aaisp/$logins                                   gb12@a.1,el6@a.1,el6@a.2
aaisp/$version                                  0.1
aaisp/login/el6@a.1/postcode                    SA62 5EY
aaisp/login/el6@a.1/quota/monthly               1000000000000
aaisp/login/el6@a.1/quota/monthly/human         1 TB
aaisp/login/el6@a.1/quota/remaining             752408843915
aaisp/login/el6@a.1/quota/remaining/human       752.41 GB
aaisp/login/el6@a.1/syncrate/down               68083000
aaisp/login/el6@a.1/syncrate/down/human         68.08 MB
aaisp/login/el6@a.1/syncrate/up                 19999000
aaisp/login/el6@a.1/syncrate/up/human           20 MB
aaisp/login/el6@a.2/postcode                    SA62 5EY
aaisp/login/el6@a.2/quota/monthly               1000000000000
aaisp/login/el6@a.2/quota/monthly/human         1 TB
aaisp/login/el6@a.2/quota/remaining             819343151266
aaisp/login/el6@a.2/quota/remaining/human       819.34 GB
aaisp/login/el6@a.2/syncrate/down               74425000
aaisp/login/el6@a.2/syncrate/down/human         74.42 MB
aaisp/login/el6@a.2/syncrate/up                 19978000
aaisp/login/el6@a.2/syncrate/up/human           19.98 MB
aaisp/login/gb12@a.1/postcode                   SA65 9RR
aaisp/login/gb12@a.1/quota/monthly              100000000000
aaisp/login/gb12@a.1/quota/monthly/human        100 GB
aaisp/login/gb12@a.1/quota/remaining            84667320096
aaisp/login/gb12@a.1/quota/remaining/human      84.67 GB
aaisp/login/gb12@a.1/syncrate/down              5181000
aaisp/login/gb12@a.1/syncrate/down/human        5.18 MB
aaisp/login/gb12@a.1/syncrate/up                1205000
aaisp/login/gb12@a.1/syncrate/up/human          1.21 MB
```

## Docker ##

Build the Docker image with:

```
docker build -t aaisp-mqtt .
```

### Configuration ###

You have two options for passing the configuration to the container. Either you can run the container with a volume mounted config file:

```
docker run -d -v <path_to_config>:/app/config.cfg --name AAISPmqtt aaisp-mqtt
```

Or you can pass the configuration values as environment variables:

* AAISP_USERNAME
* AAISP_PASSWORD
* MQTT_BROKER
* MQTT_PORT
* MQTT_USERNAME
* MQTT_PASSWORD
* MQTT_TOPIC_PREFIX
* HOMEASSISTANT_ENABLED
* HOMEASSISTANT_DISCOVERY_PREFIX

## Setup ##

TODO

## License ##

MIT

## Contributing guidelines ##

* Fork the repo
* Create a branch
* Make your changes
* Open a pull request back from your branch to master in this repo

Found a bug? open an [issue](https://github.com/nikdoof/aaisp2mqtt/issues).
