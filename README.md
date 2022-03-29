# Semtech LoRa Edge Tracker and Azure IoT Integration

The [LR1110](https://www.semtech.com/products/wireless-rf/lora-edge/lr1110trk1cks) LoRa Edge tracker is Semtech's new base design tracker technology. It is battery operated, leverages LoRa connectivity, and it doesn't require a GPS because it scans for geolocation signals such as WiFi and GNSS to compute its location in the cloud, making it very cost effective.
The payload coming from the tracker needs to be decoded, which you can do by leveraging Semtech's open source library that interacts with their LoRa Cloud geolocation service.

This project takes Semtech's decoder to the next level by integrating it with Azure IoT Hub and making it easy to deploy to your Azure subscription via an Azure Resource Manager (ARM) template and leverage Azure services to implement your business applications. Because there is code that is depedent on the LoRaWAN Network Server (LNS) implementation being used, we provide support for 3 popular LNS providers as an example: Actility, Helium, and The Things Industries. Users of this code are welcome to extend it to support additional LNS providers.

## Architecture and General Design

Here is the general architecture for this solution:
![](images/LoRaEdgeTracker_AzureIoTIntegration_Architecture.jpg)

Main components:

* LNS to Azure IoT Hub integration. This is a pre-requisite, since the LNS needs to be able to interact with Azure IoT Hub for both uplinks and downlinks.
* Router Azure Function. This function is responsible for getting the tracker payload, calling the LNS specific function to prepare the package required for using the LoRa Cloud APIs to decode the payload, and passing the resulting lat/long coordinates forward.
* LNS specific Azure Function. This project supports 3 LNS providers: Actility, Helium, and The Things Industries. Users are encourage to extend it to other LNS providers.
* Event Hub + Azure Stream Analytics. These components are used for routing the incoming data once decoded to the corresponding business application (e.g., storage, Power BI).
* Power BI dashboard using Azure Maps. We provide an example of a Power BI dashboard that's consuming data directly from an Azure SQL DB and displaying the lat/long coordinates using Azure Maps.

## Getting Started

Here is what you need to do if you would like to take advantage of this project to connect your LoRa Edge tracker to Azure:

* Deploy ARM template to your Azure subscription.
* Setup configuration paramters based on your specific deployment (e.g., Event Hub connection string, LNS to be used, etc.).
* Configure your LoRaWAN gateway to connect to your desired LNS provider.
* Configure your LNS via the corresponding console to listen to your gateway/tracker and to push data to the corresponding IoT Hub.
* Reset your tracker and make sure it wasn't connected to another LNS provider (and if it was, please make sure you remove it first before trying to connect it to a new one).

### Prerequisites

- LoRaWAN gateway to connect to the desired LoRaWAN network/LNS.
- LR1110 tracker.
- Azure subscription.

### Quickstart
The following button deploy the shown infrastructure into your chosen subscription

<a href="tbd" target="_blank">
    <img src="https://aka.ms/deploytoazurebutton"/>
</a>

The template includes the following components
- IoT Hub
- Azure Function
- SQL DB
- EventHub
- StreamAnalytics
 
### Installation Guide

### Quickstart

To start developing your solution locally follow these steps to build the code.

1. git clone [repository clone url]
2. cd [respository name]
3. ...


## Visualizing geolocation data using Power BI

An example of how to create a Power BI report to visualize the data generated by the tracker is included [here](docs/powerbi_report.md).

## Resources

- [LR1110](https://www.semtech.com/products/wireless-rf/lora-edge/lr1110trk1cks) documentation.
- [Dragino LPS8](https://www.dragino.com/products/lora-lorawan-gateway/item/148-lps8.html) gateway documentation.
- [Actility and Azure IoT Hub integration](https://docs.thingpark.com/thingpark-x/latest/Connector/AZURE/#creating-an-iot-hub) documentation.
- [Actlity and Azure IoT Hub integration](https://www.youtube.com/watch?v=J2ecr2rQq8Y) IoT Show episode.
- [Helium and Azure IoT Hub integration](https://docs.helium.com/use-the-network/console/integrations/azure/).
- [Helium Hacks episode - Azure IoT Hub integration](https://www.youtube.com/watch?v=pjPHVTFkbug).
- [The Things Industries and Azure IoT Hub integration](https://www.thethingsindustries.com/docs/integrations/cloud-integrations/azure-iot-hub/#:~:text=%20The%20key%20features%20of%20the%20Azure%20IoT,on%20the%20decoded%20payloads%2C%20and%20schedule...%20More%20).
