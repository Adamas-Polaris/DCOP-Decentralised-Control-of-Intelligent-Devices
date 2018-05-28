#! python3
# starter.py - Thread which gives "TOP" to the DPOP agents
# It is a thread intended to be launched by the server
import json
import time
import operator

from threading import Thread
from helpers.constants import Constants
from helpers.message_types import MessageTypes
from helpers import log
from mqtt.mqtt_manager import MQTTManager


class Starter(Thread):

    def __init__(self, agents, mqtt_client):

        Thread.__init__(self)

        self.agents = agents
        self.priorities = {}
        self.old_results_index = {}
        self.mqtt_manager = MQTTManager(mqtt_client)

        for agent in self.agents:
            self.priorities[str(agent.id)] = 0
            self.old_results_index[str(agent.id)] = Constants.INFINITY_IDX

    def run(self):

        while 1:

            self.do_one_iteration()
            time.sleep(Constants.TWO_MINUTS)

    def do_one_iteration(self):
        log.info("Start", Constants.SERVER, Constants.INFO)

        for agent in self.agents:
            self.mqtt_manager.publish_on_msg_to(agent.id)

        root = self.choose_root()

        for agent in self.agents:
            self.mqtt_manager.publish_elected_root_msg_to(agent.id, root)

        received_index = self.get_values()
        sorted_priorities = self.update_and_get_priorities(received_index)

        results = ""
        for agent_id, priority in sorted_priorities:

            results += "Room " + str(agent_id) + \
                       " need intervention in " + str(Constants.DIMENSION[received_index[agent_id]]) + \
                       " minutes. PRIORITY : " + str(priority) + " "
            self.old_results_index[agent_id] = received_index[agent_id]

        log.info(results, Constants.SERVER, Constants.RESULTS)

    def choose_root(self):
        root = 0
        best_value = 0

        while len(self.mqtt_manager.client.list_msgs_waiting) < len(self.agents):
            # Wait for ROOTs messages
            pass

        for msg in self.mqtt_manager.client.list_msgs_waiting:

            split_msg = msg.split(":")
            value = int(split_msg[1]) + (2 * self.priorities[split_msg[0]])

            if value > best_value:
                root = int(split_msg[0])
                best_value = value

        self.mqtt_manager.client.list_msgs_waiting = []
        return root

    def update_and_get_priorities(self, data_received):

        for key in data_received:

            if Constants.DIMENSION[self.old_results_index[key]] <= Constants.URGT_TIME \
                    and Constants.DIMENSION[data_received[key]] < Constants.URGT_TIME:
                self.priorities[key] += 1
            else:
                self.priorities[key] = 0

        return sorted(self.priorities.items(), key=operator.itemgetter(1))

    def get_values(self):
        received_index = {}
        while len(received_index) < len(self.agents):

            if not self.mqtt_manager.has_value_msg():
                # Wait for VALUES results
                continue

            msg_received = self.mqtt_manager.client.value_msgs.pop(0)
            value_data = msg_received.split(MessageTypes.VALUES.value + " ")[1]
            received_index.update(json.loads(value_data))
        return received_index

