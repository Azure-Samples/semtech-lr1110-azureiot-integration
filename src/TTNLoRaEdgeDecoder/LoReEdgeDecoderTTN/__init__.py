# Copyright (c) Microsoft Corporation.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE


# Copyright (C) 2022, SEMTECH (International) AG.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#    * Neither the name of SEMTECH (International) AG nor the names of its 
#      contributors may be used to endorse or promote products derived from this 
#      software without specific prior written permission.
#
# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE
# GRANTED BY THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT
# HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from typing import List
import base64
import json
import logging
import os
import requests
import time
import azure.functions as func
from azure.iot.hub import IoTHubRegistryManager
from azure.iot.hub.models import Twin, TwinProperties
from azure.eventhub import EventHubProducerClient, EventData

# DAS data
DASURI = os.environ["dasLoRaCloudURI"]
DAS_AUTH_TOKEN =  os.environ["dasAuthToken"]
DAS_TOKEN_HEADER =  {'Authorization': '%s'%DAS_AUTH_TOKEN}

# IOT HUB INFO
IOTHUB_CONNECTION_STRING = os.environ["iotHubConnectionString"] 

# MGS ports
MGS_PORTS = (197,198,199)

# MGS helper lambdas and functions
# MGS errors
has_mgs_errors = lambda __mgs_response__: True if 'errors' in __mgs_response__ else False
get_mgs_errors = lambda __mgs_response__: __mgs_response__['errors']

# MGS result
has_mgs_result = lambda __mgs_response__: True if 'result' in __mgs_response__ else False
get_mgs_result = lambda __mgs_response__: __mgs_response__['result']

# MGS lambdas
get_mgs_usage = lambda __mgs_result__: __mgs_result__['usage']
get_mgs_info_flds = lambda __mgs_result__: __mgs_result__['info_fields']
get_mgs_fports = lambda __mgs_result__: __mgs_result__['fports']
get_mgs_ful_req = lambda __mgs_result__: __mgs_result__['fulfilled_requests']
get_mgs_file = lambda __mgs_result__: __mgs_result__['file']

# MGS pending requests lambdas
get_mgs_pnd_req = lambda __mgs_result__: __mgs_result__['pending_requests']
has_mgs_pnd_req = lambda __mgs_result__: True if __mgs_result__['pending_requests'] else False

# MGS log messages lambdas
has_mgs_log_msgs = lambda __mgs_result__: True if __mgs_result__['log_messages'] else False
get_mgs_log_msgs = lambda __mgs_result__: __mgs_result__['log_messages']
num_mgs_log_msgs = lambda __mgs_result__: len(__mgs_result__['log_messages']) if __mgs_result__['log_messages'] else 0
get_mgs_log_msgs_lvl = lambda __index__, __mgs_result__: __mgs_result__['log_messages'][__index__]['level'] if num_mgs_log_msgs(__mgs_result__) > __index__ else None
get_mgs_log_msgs_tstmp = lambda __index__, __mgs_result__: __mgs_result__['log_messages'][__index__]['timestamp'] if num_mgs_log_msgs(__mgs_result__) > __index__ else None
get_mgs_log_msgs_lgmsg = lambda __index__, __mgs_result__: __mgs_result__['log_messages'][__index__]['logmsg'] if num_mgs_log_msgs(__mgs_result__) > __index__ else None

# MGS position solution lambdas
get_mgs_pos_sol = lambda __mgs_result__:__mgs_result__['position_solution']
has_mgs_pos_sol = lambda __mgs_result__: True if __mgs_result__['position_solution'] else False
get_mgs_pos_sol_algrm = lambda __mgs_result__:__mgs_result__['algorithm_type']
get_mgs_pos_sol_lat = lambda __mgs_result__:__mgs_result__['llh'][0]
get_mgs_pos_sol_lon = lambda __mgs_result__:__mgs_result__['llh'][1]
get_mgs_pos_sol_alt = lambda __mgs_result__:__mgs_result__['llh'][2]

# MGS stream records lambdas
has_mgs_strm_rec = lambda __mgs_result__: True if __mgs_result__['stream_records'] else False
num_mgs_strm_rec = lambda __mgs_result__: len(__mgs_result__['stream_records']) if __mgs_result__['stream_records'] else 0
get_mgs_strm_rec = lambda __mgs_result__: __mgs_result__['stream_records']
get_mgs_strm_rec_ofst = lambda __index__, __mgs_result__: __mgs_result__['stream_records'][__index__][0] if num_mgs_strm_rec(__mgs_result__) > __index__ else None
get_mgs_strm_rec_data = lambda __index__, __mgs_result__: __mgs_result__['stream_records'][__index__][1] if num_mgs_strm_rec(__mgs_result__) > __index__ else None

# MGS downlink lambdas and functions
get_mgs_dnlink = lambda __mgs_result__: __mgs_result__['dnlink']
has_mgs_dnlink = lambda __mgs_result__: True if __mgs_result__['dnlink'] else False
get_mgs_dnlink_port = lambda __mgs_result__: __mgs_result__['dnlink']['port'] if __mgs_result__['dnlink'] else None
get_mgs_dnlink_payload = lambda __mgs_result__: __mgs_result__['dnlink']['payload'] if __mgs_result__['dnlink'] else None
def set_mgs_dnlink_port(port, mgs_result):
    mgs_result['dnlink']['port'] = port

# Data conversion lambdas
hex2base64_str = lambda __hex_str__: base64.b64encode(bytearray.fromhex(__hex_str__)).decode('ASCII')
base642hex_str = lambda __base64_str__: base64.b64decode(__base64_str__).hex()

# global return value for HTTP Reponse
return_json = {}

# Azure serverless function. This function is both platform and LNS
# dependent. When using another LNS the message type and payload
# extraction must be adjusted to the new LNS.
async def main(req : func.HttpRequest)-> func.HttpResponse:

    global return_json

    try:
        req_body = req.get_json()
    except ValueError:
        logging.error("no json body found")
        return_json={"error":"no json body found"}
        return func.HttpResponse(json.dumps(return_json),status_code=400,mimetype="application/json")

    msg_payload = json.dumps(req_body)
    msg_json = req_body
    msg_type = {"msgType":"raw"}
    msg_json.update(msg_type)

    if parse_payload(msg_payload) == False:
        logging.info("Error processing LNS event")
        return_json={"error":"LNS processing failed"}
        return func.HttpResponse(json.dumps(return_json),status_code=400,mimetype="application/json")
    
    return func.HttpResponse(json.dumps(return_json),status_code=200,mimetype="application/json")
# Main end

# Azure serverless function. This function is both platform and LNS
# dependent. When using another LNS the message type and payload
# extraction must be adjusted to the new LNS.
def parse_payload(lns_payload):
    # Received JSON payload. Process payload
    deveui = ""
    ttn_device_id = ""

    if 'identifiers' in lns_payload:
        deveui = lns_payload['identifiers'][1]['dev_eui']
    elif 'end_device_ids' in lns_payload:
        deveui = lns_payload['end_device_ids']['dev_eui']
        ttn_device_id = lns_payload['end_device_ids']['device_id']

    # Get device eui.
    # loracloud expects the deveui as 8 pairs of hex digits separated by
    # dashes, e.g. 01-23-45-67-89-ab-cd-ef.
    deveui = "-".join(deveui[i:i+2] for i in range(0,len(deveui),2))

    # Build the device data dictionary. This dictionary has two fields:
    # mgs_data: This field is a dictionary that contains the following:
    #   mgs_deveui: The device EUI formatted as required by the MGS.
    #   mgs_payload: The MGS payload.
    # lns_plat_data: This field contains data required by the chosen LNS
    # or platform.
    dev_data = {
        'mgs_data': {
            'mgs_deveui': deveui,
            'mgs_payload': ''
        },
        'lns_plat_data': {
            'device_id': ttn_device_id
        }
    }
    logging.info(f'Parsing message: device: {deveui}')

    # Build MGS message payload and send MGS request. This is dependant
    # on the selected LNS. The criteria for composing the MGS message is
    # the following:
    # 1) Given that the frame counter is a required field in the MGS, if
    # there isn't an f_cnt field present in the TTN3 message then no further
    # processing is required.
    # 2) If the port number is not in MGS_PORTS or if there is no port number
    # then the payload does not need to be included. In this case the message
    # is sent to the MGS solely to provide a downlink opportunity as specified
    # in the LoRa Cloud documentation.
    # 3) If the port number is 197, 198, or 199 the payload must be forwarded
    # to the MGS.
    mgs_payload = {}
    if 'uplink_message' in lns_payload:
        logging.info('Parsing message: uplink found')
        mgs_payload['msgtype'] = "updf"
        if 'f_cnt' in lns_payload['uplink_message']:
            mgs_payload['fcnt'] = lns_payload['uplink_message']['f_cnt']
            if 'f_port' in lns_payload['uplink_message']:
                mgs_payload['port'] = lns_payload['uplink_message']['f_port']
                if mgs_payload['port'] in MGS_PORTS:
                    mgs_payload['payload'] = base642hex_str(lns_payload['uplink_message']['frm_payload'])
            dev_data['mgs_data']['mgs_payload'] = mgs_payload
            mgs_request(dev_data)
    elif 'join_accept' in lns_payload:
        logging.info('Parsing message: join found')
        mgs_payload['msgtype'] = "joining"
        dev_data['mgs_data']['mgs_payload'] = mgs_payload
        mgs_request(dev_data)

# Make a MGS request.
def mgs_request(dev_data):
    # Build MGS request
    mgs_request = {
        'deveui': dev_data['mgs_data']['mgs_deveui'],
        'uplink': dev_data['mgs_data']['mgs_payload']
    }

    logging.info(f'MGS Request: {mgs_request}')
    # Make MGS request
    r = requests.post(DASURI, headers=DAS_TOKEN_HEADER, json=mgs_request)
    if r.status_code != 200:
        logging.error(f"MGS request failed with status code {r.status_code}")
        return

    # Get MGS response
    mgs_resp = r.json()
    logging.info(f'MGS Response: {mgs_resp}')

    # Check for MGS errors
    if has_mgs_errors(mgs_resp):
        logging.error(f"MGS returned errors: {get_mgs_errors(mgs_resp)}")
        return

    # Get MGS result
    mgs_result = get_mgs_result(mgs_resp)
    logging.info(mgs_result)

    # If response has downlink then process downlink
    if has_mgs_dnlink(mgs_result):
        logging.info('mgs_request: downlink found')
        proc_dnlink(mgs_result, dev_data)

    # If response has stream records process stream records
    if has_mgs_strm_rec(mgs_result):
        logging.info('mgs_request: stream found')
        proc_strm_rec(mgs_result, dev_data)

    # If response has position solution process position solution
    if has_mgs_pos_sol(mgs_result):
        logging.info('mgs_request: position found')
        proc_pos_sol(mgs_result, dev_data)

    # If response has log messages process log messages
    if has_mgs_log_msgs(mgs_result):
        logging.info('mgs_request: log messages found')
        proc_log_mes(mgs_result, dev_data)

    # If response has pending requests process pending requests
    if has_mgs_pnd_req(mgs_result):
        logging.info('mgs_request: pending requests found')
        proc_pnd_req(mgs_result, dev_data)

# Process pending requests
def proc_pnd_req(mgs_result, dev_data):
    pass

# Process log messages
def proc_log_mes(mgs_result, dev_data):
    for i in range(num_mgs_log_msgs(mgs_result)):
        logging.info("Log message:")
        logging.info(f"Level: {get_mgs_log_msgs_lvl(i, mgs_result)}")
        logging.info(f"Timestamp: {get_mgs_log_msgs_tstmp(i, mgs_result)}")
        logging.info(f"Message: {get_mgs_log_msgs_lgmsg(i, mgs_result)}")

# Process position solution
def proc_pos_sol(mgs_result, dev_data):
    position_solution = get_mgs_pos_sol(mgs_result)
    latitude = get_mgs_pos_sol_lat(position_solution)
    longitude = get_mgs_pos_sol_lon(position_solution)
    altitude = get_mgs_pos_sol_alt(position_solution)
    algorithm = get_mgs_pos_sol_algrm(position_solution)
    uplinkTime = time.time()

    logging.info("Position solution:")
    logging.info(f"algorithm: {algorithm}")
    logging.info(f"Latitude: {latitude}")
    logging.info(f"Longitude: {longitude}")
    logging.info(f"Altitude: {get_mgs_pos_sol_alt(position_solution)}")

    global return_json
    return_json = {'algorithm':algorithm,'latitude':latitude,'longitude':longitude,'altitude':altitude,'msgType':'pos','epochTime':uplinkTime}


# Process stream records. This function is application dependent.
# This is the LoRa Edge Tracker version of the function.
def proc_strm_rec(mgs_result, dev_data):
    # Loop through stream records and process
    for rec in range(num_mgs_strm_rec(mgs_result)):
        # Get stream record data
        data = get_mgs_strm_rec_data(rec, mgs_result)

        # Process data according to tag
        start = 0
        end = 0
        while len(data) > end+1:
            tag = data[start:start+2]
            start = start + 2
            length = data[start:start+2]
            start = start + 2
            end = start + 2 * int(length, base=16)
            value = data[start:end]
            start = end

            # Process payload
            if tag == "06" or tag == "07":
                logging.info("GNSS Scan")
                payload = {
                    "msgtype": "gnss",
                    "payload": value
                }
                dev_data = {
                    'mgs_data': {
                        'mgs_deveui': dev_data['mgs_data']['mgs_deveui'],
                        'mgs_payload': payload
                    },
                    'lns_plat_data': dev_data['lns_plat_data']
                }
                mgs_request(dev_data)

            if tag == "08":
                logging.info("Wi-Fi Scan")
                payload = {
                    "msgtype": "wifi",
                    "payload": "01" + value
                }
                dev_data = {
                    'mgs_data': {
                        'mgs_deveui': dev_data['mgs_data']['mgs_deveui'],
                        'mgs_payload': payload
                    },
                    'lns_plat_data': dev_data['lns_plat_data']
                }
                mgs_request(dev_data)

            if tag == "09":
                logging.info(f"Move history: 0x{value[:2]}")
                logging.info(f"X: 0x{value[2:6]}")
                logging.info(f"Y: 0x{value[6:10]}")
                logging.info(f"Z: 0x{value[10:14]}")

                logging.info(f"Temp: 0x{value[14:18]}")
            if tag == "0a":
                logging.info(f"Modem charge: 0x{value}")
            if tag == "0b":
                logging.info(f"Modem charge: 0x{value}")
            if tag == "0c":
                logging.info(f"Host reset: 0x{value[:4]}")
                logging.info(f"Host reset: 0x{value[4:8]}")
                logging.info(f"Host reset itself: 0x{value[8:12]}")
            if tag == "0e":
                logging.info("WiFi Scan")
                payload = {
                    "msgtype": "wifi",
                    "payload": "01" + value[10:]
                }
                dev_data = {
                    'mgs_data': {
                        'mgs_deveui': dev_data['mgs_data']['mgs_deveui'],
                        'mgs_payload': payload
                    },
                    'lns_plat_data': dev_data['lns_plat_data']
                }
                mgs_request(dev_data)
            if tag == "46":
                logging.info(f"Tracker current date: 0x{value}")
            if tag == "4c":
                logging.info(f"Tracker settings: 0x{value}")

# Process downlink. This function is application dependent.
# This is the LR1110 EVK/Tracker version of the function.
def proc_dnlink(mgs_result, dev_data):
    # Get port
    port =  get_mgs_dnlink_port(mgs_result)

    # If port is 0 then change to 150. These messages contain
    # a push solver payload. The port is changed to 150 so
    # that the application firmware sends the payload to the
    # Modem-E.
    port = 150 if 0 == port else port
    set_mgs_dnlink_port(port, mgs_result)

    # Send downlink
    lns_downlink(mgs_result, dev_data)

# Send downlink to LNS.
# This is the TTN3 version of the function.
def lns_downlink(mgs_result, dev_data):
    # Get device port, payload, and device id
    port = get_mgs_dnlink_port(mgs_result)
    payload = get_mgs_dnlink_payload(mgs_result)
    device_id = dev_data['lns_plat_data']['device_id']

    # Build decoded payload for IoT Hub desired properties.
    # This step is dependent on the application defined on TTN.
    # It will use "payload decoders" defined for the specific device.
    # For more information please check IoT Hub integration documentation on
    # TTN.
    decoded_payload = {
        "decodedPayload": {
            "frm_payload": payload,
            "f_port": port
        }
    }

    iothub_registry_manager = IoTHubRegistryManager(IOTHUB_CONNECTION_STRING)
    twin = iothub_registry_manager.get_twin(device_id)
    twin_patch = Twin(properties= TwinProperties(desired=decoded_payload))
    twin = iothub_registry_manager.update_twin(device_id, twin_patch, twin.etag)

    logging.info("Enqueueing downlink")
    logging.info(f"Enqueueing downlink: {decoded_payload}")
