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
import logging

import azure.functions as func
import os
import base64
import requests
import json
import time

from azure.iot.hub import IoTHubRegistryManager

# DAS data
DASURI = os.environ["dasLoRaCloudURI"]
DAS_AUTH_TOKEN =  os.environ["dasAuthToken"]
DAS_TOKEN_HEADER =  {'Authorization': '%s'%DAS_AUTH_TOKEN}

# IOT HUB INFO
IOTHUB_CONNECTION_STRING = os.environ["iotHubConnectionString"] 

# DAS lambdas
# DAS errors
has_das_errors = lambda __das_response__: True if 'errors' in __das_response__ else False
get_das_errors = lambda __das_response__: __das_response__['errors']

# DAS result
has_das_result = lambda __das_response__: True if 'result' in __das_response__ else False
get_das_result = lambda __das_response__: __das_response__['result']

# DAS lambdas
get_das_usage = lambda __das_result__: __das_result__['usage']
get_das_info_flds = lambda __das_result__: __das_result__['info_fields']
get_das_fports = lambda __das_result__: __das_result__['fports']
get_das_ful_req = lambda __das_result__: __das_result__['fulfilled_requests']
get_das_file = lambda __das_result__: __das_result__['file']

# DAS pending requests lambdas
get_das_pnd_req = lambda __das_result__: __das_result__['pending_requests']
has_das_pnd_req = lambda __das_result__: True if __das_result__['pending_requests'] else False

# DAS log messages lambdas
has_das_log_msgs = lambda __das_result__: True if __das_result__['log_messages'] else False
get_das_log_msgs = lambda __das_result__: __das_result__['log_messages']
num_das_log_msgs = lambda __das_result__: len(__das_result__['log_messages']) if __das_result__['log_messages'] else 0
get_das_log_msgs_lvl = lambda __index__, __das_result__: __das_result__['log_messages'][__index__]['level'] if num_das_log_msgs(__das_result__) > __index__ else None
get_das_log_msgs_tstmp = lambda __index__, __das_result__: __das_result__['log_messages'][__index__]['timestamp'] if num_das_log_msgs(__das_result__) > __index__ else None
get_das_log_msgs_lgmsg = lambda __index__, __das_result__: __das_result__['log_messages'][__index__]['logmsg'] if num_das_log_msgs(__das_result__) > __index__ else None

# DAS position solution lambdas
get_das_pos_sol = lambda __das_result__:__das_result__['position_solution']
has_das_pos_sol = lambda __das_result__: True if __das_result__['position_solution'] else False
get_das_pos_sol_algrm = lambda __das_result__:__das_result__['algorithm_type']
get_das_pos_sol_lat = lambda __das_result__:__das_result__['llh'][0]
get_das_pos_sol_lon = lambda __das_result__:__das_result__['llh'][1]
get_das_pos_sol_alt = lambda __das_result__:__das_result__['llh'][2]

# DAS stream records lambdas
has_das_strm_rec = lambda __das_result__: True if __das_result__['stream_records'] else False
num_das_strm_rec = lambda __das_result__: len(__das_result__['stream_records']) if __das_result__['stream_records'] else 0
get_das_strm_rec = lambda __das_result__: __das_result__['stream_records']
get_das_strm_rec_ofst = lambda __index__, __das_result__: __das_result__['stream_records'][__index__][0] if num_das_strm_rec(__das_result__) > __index__ else None
get_das_strm_rec_data = lambda __index__, __das_result__: __das_result__['stream_records'][__index__][1] if num_das_strm_rec(__das_result__) > __index__ else None

# DAS downlink lambdas
get_das_dnlink = lambda __das_result__: __das_result__['dnlink']
has_das_dnlink = lambda __das_result__: True if __das_result__['dnlink'] else False
get_das_dnlink_port = lambda __das_result__: __das_result__['dnlink']['port'] if __das_result__['dnlink'] else None
get_das_dnlink_payload = lambda __das_result__: __das_result__['dnlink']['payload'] if __das_result__['dnlink'] else None

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
    except Exception as ex:
        logging.error("no json body found")
        return_json = {'epochTime':time.time(),'level':"error",'logMessage':str(ex),'msgType':'log'}
        return func.HttpResponse(json.dumps(return_json),status_code=400,mimetype="application/json")

    msg_payload = json.dumps(req_body)
    msg_json = req_body
    msg_type = {"msgType":"raw"}
    msg_json.update(msg_type)

    if proc_lns_event(msg_payload) == False:
        logging.info("Error processing LNS event")
        return func.HttpResponse(json.dumps(return_json),status_code=500,mimetype="application/json")
    
    return func.HttpResponse(json.dumps(return_json),status_code=200,mimetype="application/json")
# Main end

# Process LNS event. This is an LNS dependent function.
def proc_lns_event(msg_payload):
    # Get device eui.
    # loracloud expects the deveui as 8 pairs of hex digits separated by
    # dashes, e.g. 01-23-45-67-89-ab-cd-ef.
    logging.info("============msg_payload - json=================")
    json_payload = json.loads(msg_payload)
    logging.info(json.dumps(json_payload, indent = 4, sort_keys=True))

    # Build DAS message payload and send DAS request. This is dependant
    # on the selected LNS. If the message type is not join or up then 
    # nothing else to do.
    das_payload = {}
    if 'DevEUI_uplink' in msg_payload:
        if 'rawJoinRequest' in msg_payload:
            # not sure what to do for this one, so ignoring for now
            das_payload = None
            das_result = True
        else:
            deveui = json_payload['DevEUI_uplink']['DevEUI']
            das_deveui = "-".join(deveui[i:i+2] for i in range(0,len(deveui),2))
            das_payload['msgtype'] = "updf"
            das_payload['fcnt'] = json_payload['DevEUI_uplink']['FCntUp']
            das_payload['port'] = json_payload['DevEUI_uplink']['FPort']
            if 'payload_hex' in msg_payload:
                das_payload['payload'] = json_payload['DevEUI_uplink']['payload_hex']
            #das_payload['timestamp'] = json_payload['DevEUI_uplink']['Time']
            das_result = das_request(das_deveui, das_payload)
    elif 'DevEUI_notification' in msg_payload and 'join' in msg_payload:
        deveui = json_payload['DevEUI_notification']['DevEUI']
        das_deveui = "-".join(deveui[i:i+2] for i in range(0,len(deveui),2))
        das_payload['msgtype'] = "joining"
        das_result = das_request(das_deveui, das_payload)
    else:
        das_payload = None
        das_result = True

    # Success
    return das_result
# proc_lns_event end.

# Make a DAS request. This is a platform and lns independent function.
def das_request(das_deveui, das_payload):
    # Initialize success flag
    das_success = True
    global return_json

    # Build DAS request
    das_request = {
        'deveui': das_deveui,
        'uplink': das_payload
    }
    logging.info(f"DAS request: {das_request}")

    # Make DAS request
    r = requests.post(DASURI, headers = DAS_TOKEN_HEADER, json = das_request)
    if r.status_code != 200:
        logging.info(f"DAS request failed with status code {r.status_code}")
        return_json = {'epochTime':time.time(),'level':"error",'logMessage':str(r.status_code),'msgType':'log'}
        return False
    
    # Check for DAS errors
    das_resp = r.json()
    logging.info(f"DAS response: {das_resp}")
    return_json = {'DAS response':das_resp}

    # Check for DAS errors.
    if has_das_errors(das_resp):
        logging.info(f"DAS returned errors: {get_das_errors(das_resp)}")
        return_json = {'epochTime':time.time(),'level':"error",'logMessage':str(get_das_errors(das_resp)),'msgType':'log'}
        return False

    # Get DAS result
    das_result = get_das_result(das_resp)
    
    # If response has downlink then process downlink
    if has_das_dnlink(das_result):
        if not proc_dnlink(das_deveui, get_das_dnlink_port(das_result), get_das_dnlink_payload(das_result)):
            logging.info("Downlink processing error")
            return_json = {'epochTime':time.time(),'level':"error",'logMessage':str("Downlink processing error"),'msgType':'log'}
            das_success = False

    # If response has stream records process stream records
    if has_das_strm_rec(das_result):
        for rec in range(num_das_strm_rec(das_result)):
            proc_strm_rec(das_deveui, get_das_strm_rec_ofst(rec, das_result), get_das_strm_rec_data(rec, das_result))
    
    # If response has position solution process position solution
    if has_das_pos_sol(das_result):
        proc_pos_sol(get_das_pos_sol(das_result),das_deveui)

    # If response has log messages process log messages
    if has_das_log_msgs(das_result):
        for i in range(num_das_log_msgs(das_result)):
            proc_log_mes(get_das_log_msgs_lvl(i, das_result), get_das_log_msgs_tstmp(i, das_result), get_das_log_msgs_lgmsg(i, das_result))

    if has_das_pnd_req(das_result):
        proc_pnd_req(get_das_pnd_req)

    # Event processing completed
    return True

# proc_lns_event end

# Process pending requests
def proc_pnd_req(pend_req):
    pass

# Process log messages
def proc_log_mes(level, timestamp, log_message):
    logging.info(f"Level: {level}")
    logging.info(f"Timestamp: {timestamp}")
    logging.info(f"Message: {log_message}")

# proc_log_mes end

# Process position solution
def proc_pos_sol(position_solution,das_deveui):
    algorithm = get_das_pos_sol_algrm(position_solution)
    latitude = get_das_pos_sol_lat(position_solution)
    longitude = get_das_pos_sol_lon(position_solution)
    altitude = get_das_pos_sol_alt(position_solution)
    uplinkTime = time.time()

    logging.info("Position solution.")
    logging.info(f"Algorithm: {get_das_pos_sol_algrm(position_solution)}")
    logging.info(f"Latitude: {latitude}")
    logging.info(f"Longitude: {longitude}")
    logging.info(f"Altitude: {get_das_pos_sol_alt(position_solution)}")
    logging.info(f"DevEUI: {das_deveui}")

    global return_json
    return_json = {'devEUI':das_deveui,'algorithm':algorithm,'latitude':latitude,'longitude':longitude,'altitude':altitude,'msgType':'pos','epochTime':uplinkTime}

# proc_pos_sol end

# Process stream records. This function is application dependent.
def proc_strm_rec(deveui, offset, data):
    # Get payload tag
    tag = data[:2]
    length = data[2:4]

    # Process data according to tag
    # Process stream record.
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
        if tag == "06":
            logging.info("GNSS Scan")
            payload = {
                "msgtype": "gnss",
                "payload": value
            }
            das_request(deveui, payload)
        if tag == "07":
            logging.info("GNSS Scan")
            payload = {
                "msgtype": "gnss",
                "payload": value
            }
            das_request(deveui, payload)
        if tag == "08":
            payload = {
                "msgtype": "wifi",
                "payload": "01" + value
            }
            das_request(deveui, payload)
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
        if tag == "0d":
            logging.info(f"Sensor data: 0x{value}")
        if tag == "0e":
            payload = {
                "msgtype": "wifi",
                "payload": "01" + value[10:]
            }
            das_request(deveui, payload)
        if tag == "46":
            logging.info(f"Tracker current date: 0x{value}")
        if tag == "4c":
            logging.info(f"Tracker settings: 0x{value}")
    # Return result
    return True

# proc_strm_rec end

# Process downlink. This function is application dependent.
# This is the LR1110 EVK/Tracker version of the function.
def proc_dnlink(deveui, port, payload):
    # If port is 0 change to 150
    port = 150 if 0 == port else port

    # Send downlink
    return lns_downlink(deveui, port, payload)

# proc_downlink end.

# Send downlink to LNS.
# This is the Chirpstack version of the function.
def lns_downlink(deveui, port, payload):
    global return_json

    deveui= deveui.replace('-', '')

    # Build downlink
    dnlink_dict = {
        "downlinks":[{
            "frm_payload": hex2base64_str(payload),
            "f_port": port,
            "priority":"NORMAL"
        }]
    }

    # Send C2D message
    try:
        # Create IoTHubRegistryManager
        registry_manager = IoTHubRegistryManager(IOTHUB_CONNECTION_STRING)
        registry_manager.send_c2d_message(deveui, dnlink_dict, properties={})
        logging.info("DAS C2D message sent to IoT Hub")

    except Exception as ex:
        logging.info( "Unexpected error {0}" % ex )
        return_json = {'epochTime':time.time(),'level':"error",'logMessage':ex,'msgType':'log'}
        return False

    # Success
    return True

# lns_downlink end





