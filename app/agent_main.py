#! python3
# agent_main.py - Run an agent for a DCOP system in the hospital
# Usage: py.exe agent_main.py <agentId> - Run the agent number <agentId>
from helpers import log
from helpers.constants import Constants
from helpers.event_manager import EventManager
from model.hospital import Hospital
from mqtt.agent_mqtt import AgentMQTT
from datetime import datetime

import sys

from threads.event import Event

if __name__ == "__main__":

    # FOR DEBUG : TO REMOVE !
    monitored_area = None
    hospital = Hospital(Constants.NB_ROOMS)

    for r in hospital.monitored_area_list:
        if r.id == int(sys.argv[1]):
            monitored_area = r
            break

    log_file = "logs/agents/log_agent_" + str(monitored_area.id) + "_" + datetime.now().strftime("%Y-%m-%d") + ".json"
    log.setup_custom_logger(log_file)
    log.info(monitored_area.to_json_format(), monitored_area.id, Constants.STATE)

    agent_mqtt = AgentMQTT(monitored_area)

    monitored_area.attach_observer(EventManager(monitored_area, agent_mqtt.client))
    Event(monitored_area).start()

    agent_mqtt.run()
