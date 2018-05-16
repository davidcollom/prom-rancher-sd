#!/usr/bin/env python

# Copyright 2016 Daniel Dent (https://www.danieldent.com/)
import logging
import sys
import os
import time
import urllib.parse
import urllib.request
import json
import shutil

logger = logging.getLogger(__name__)
out_hdlr = logging.StreamHandler(sys.stdout)
out_hdlr.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
out_hdlr.setLevel(logging.INFO)
logger.addHandler(out_hdlr)
logger.setLevel(logging.INFO)

rancher_metadata_path = os.getenv('RANCHER_METADATA_URL','http://rancher-metadata.rancher.internal/2015-12-19')
prometheus_label      = os.getenv('PROMETHEUS_LABEL', 'com.monitoring.prometheus.port')
sleep_timer           = int(os.getenv('SLEEP_TIMER', '10'))

def get_current_services():
    headers = {
        'User-Agent': "prom-rancher-sd/0.1",
        'Accept': 'application/json'
    }
    try:
      logger.info("Fetching container list from: {}".format(rancher_metadata_path))
      req = urllib.request.Request('{}/containers'.format(rancher_metadata_path), headers=headers)
      with urllib.request.urlopen(req) as response:
        logger.info("Completed container list request.")
        resp = response.read().decode('utf8 ')
        logger.debug("Response: ", resp)
        return json.loads(resp)
    except Exception as e:
        logger.error("Error contacting rancher-metadata:", e)
        raise e

def is_monitored_service(service):
    return 'labels' in service and prometheus_label in service['labels']

def monitoring_config(service):
    return {
        "targets": [service['primary_ip'] + ':' + service['labels'][prometheus_label]],
        "labels": {
            'instance': service['hostname'],
            'name': service['name'],
            'service_name': service['service_name'],
            'service_index': service['service_index'],
            'stack_name': service['stack_name'],
            'health_state': service['health_state'],
            'system': str(service['system']).lower(),
            'start_count': str(service['start_count']),
        }
    }


def get_monitoring_config():
    return list(map(monitoring_config, filter(is_monitored_service, get_current_services())))


if __name__ == '__main__':
    logger.info("Starting up..")
    while True:
        with open('/prom-rancher-sd-data/rancher.json.temp', 'w') as config_file:
            config = get_monitoring_config()
            logger.info("Exported {} jobs with label: {}".format(len(config),prometheus_label))
            json.dump(config, config_file, indent=2)
        shutil.move('/prom-rancher-sd-data/rancher.json.temp','/prom-rancher-sd-data/rancher.json')
        logger.info("Moved file in place, sleeping for {} seconds".format(sleep_timer))
        time.sleep(sleep_timer)
