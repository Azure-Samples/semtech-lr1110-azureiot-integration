//Copyright(c) Microsoft Corporation.

//Permission is hereby granted, free of charge, to any person obtaining a copy
//of this software and associated documentation files (the "Software"), to deal
//in the Software without restriction, including without limitation the rights
//to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
//copies of the Software, and to permit persons to whom the Software is
//furnished to do so, subject to the following conditions:

//The above copyright notice and this permission notice shall be included in all
//copies or substantial portions of the Software.

//THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
//IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
//FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
//AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
//LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
//OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
//SOFTWARE


using IoTHubTrigger = Microsoft.Azure.WebJobs.EventHubTriggerAttribute;
using Microsoft.Azure.WebJobs;
using Microsoft.Azure.WebJobs.Host;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Text;
using Microsoft.Azure.Devices;
using System.Threading.Tasks;
using System.Runtime.Caching;
using System.Collections.Concurrent;
using Microsoft.Extensions.Logging;
using Microsoft.Azure.EventHubs;

namespace LR1110.Route
{
    public static class RouteFunction
    {
        /// <summary>
        /// random generator
        /// </summary>
        private static Random random = new Random();

        private static dynamic GetPayload(byte[] body)
        {
            var json = System.Text.Encoding.UTF8.GetString(body);
            return JObject.Parse(json);
        }

        /// <summary>
        /// Get the device id from the inbound message from the IoT Hub.
        /// </summary>
        /// <param name="message"></param>
        /// <returns></returns>
        private static string GetDeviceId(EventData message)
        {
            return message.SystemProperties["iothub-connection-device-id"].ToString();
        }

        /// <summary>
        /// Method contacting the Devices twins from the IoT Hub to get the medata and pass it in the payload.
        /// </summary>
        /// <param name="connectionString">Connection string of the IoT Hub</param>
        /// <param name="id">metadata Device Id</param>
        /// <returns></returns>
        public async static Task<dynamic> GetTags(string connectionString, string id)
        {
            RegistryManager registryManager = RegistryManager.CreateFromConnectionString(connectionString);
            var twin = await registryManager.GetTwinAsync(id);
            var result = JsonConvert.DeserializeObject(twin.Tags.ToJson());
            return result;
        }

        /// <summary>
        /// message describing the output of the function.
        /// </summary>
        public class ReturnMessage
        {
            public Guid messageGuid;
            public dynamic raw;
            public dynamic metadata;
            public dynamic decoded;
            public ReturnMessage()
            {
                messageGuid = Guid.NewGuid();
            }
        }

        [FunctionName("RouteFunction")]
        public async static Task Run([IoTHubTrigger("messages/events", Connection = "EVENT_HUB_ROUTER_INPUT")] EventData[] myEventHubMessageInput,
            [EventHub("outputEventHubMessage", Connection = "EVENT_HUB_ROUTER_OUTPUT")] IAsyncCollector<String> output,
              ILogger log)
        {
            foreach (var myEventHubMessage in myEventHubMessageInput)
            {
                //section to build up the metadata section
                var deviceId = GetDeviceId(myEventHubMessage);
                //retry logic to avoid the initial message rush to be declined by the IoT hub.
                string functionUrl = System.Environment.GetEnvironmentVariable("DECODER_URL");

                
                //section to build up the raw section
                var rawMessageSection = GetPayload(myEventHubMessage.Body.Array);
                //var rawMessageSection = JObject.Parse(myEventHubMessage.ToString());
                //routing
                //Case 1 route to a global specific function
                var decodedMessageContents = new Dictionary<string, string>();
                string decodedSection = null;
                if (string.IsNullOrEmpty(functionUrl))
                {
                    decodedMessageContents.Add("error", "Could not resolve decoder function URL");
                    decodedMessageContents.Add("details", $"rify that the device twin has been properly configured for deviceId {deviceId} ");
                }
                else
                {
                    //Section to build up the decoded section
                    HttpWebRequest req = (HttpWebRequest)WebRequest.Create(functionUrl);
                    req.Method = "POST";
                    req.ContentType = "application/json";
                    Stream stream = await req.GetRequestStreamAsync();

                    string json = JsonConvert.SerializeObject(rawMessageSection);
                    byte[] buffer = Encoding.UTF8.GetBytes(json);
                    await stream.WriteAsync(buffer, 0, buffer.Length);
                    try
                    {
                        var res = await req.GetResponseAsync();
                        using (var sr = new StreamReader(res.GetResponseStream()))
                        {
                            decodedSection = await sr.ReadToEndAsync();
                        }
                    }
                    catch (System.Net.WebException exception)
                    {
                        decodedMessageContents.Add("error", "The decoder method was not found");
                        decodedMessageContents.Add("details", exception.Message);
                        decodedMessageContents.Add(nameof(functionUrl), functionUrl);
                    }
                }

                //build the message outputed to the output eventHub
                ReturnMessage returnMessage = new ReturnMessage();
                if (decodedMessageContents.Count > 0)
                    returnMessage.decoded = decodedMessageContents;
                else if (!string.IsNullOrEmpty(decodedSection))
                    returnMessage.decoded = JsonConvert.DeserializeObject(decodedSection);
                returnMessage.raw = rawMessageSection;

                string returnString = JsonConvert.SerializeObject(returnMessage);
                log.LogInformation(returnString);
                await output.AddAsync(returnString);
            }
            await output.FlushAsync();
        }
    }
}