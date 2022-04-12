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

### Setup Guide

This is a step by step guide to setup the infrastructure an deploy the code to ingest, compute and visualise the LoRa Edge tracker data.

For now the process is semi-automated. Certain steps need to be done manually.

### Setup Prerequisites

The following tools and extension are necessary to build and deploy the sources and projects.
Please make sure to have the prerequisites ready before starting the setup.

* [Visual Studio Code](https://code.visualstudio.com/)
* [Visual Studio Code Azure Functions Extension](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azurefunctions)
* [Visual Studio Code SQL Extension](https://marketplace.visualstudio.com/items?itemName=ms-mssql.mssql)
* [Visual Studio Code Stream Analytics Extension](https://marketplace.visualstudio.com/items?itemName=ms-bigdatatools.vscode-asa)
* [Azure Functions Core Tools](https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local?tabs=v4%2Cwindows%2Ccsharp%2Cportal%2Cbash)
* [\.NET 6.0 SDK](https://dotnet.microsoft.com/en-us/download/dotnet/thank-you/sdk-6.0.201-windows-x64-installer)
* [Python Version 3.9 or higher](https://www.python.org/downloads/) 

### Deployment of the Azure services

The following button deploys the core infrastructure into your chosen subscription.

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fyaens%2Farm-templates%2Fmaster%2Farm-test%2FazuredeployBasic.json)

For the custom deployment, the following parameters need to be defined:
- Region: Select your designated Azure Region, make sure to pick a region which supports the necessary components
- Unique Solution Prefix: Pick a unique string for your solution, please only use alphanumerical characters and dashes ("-"), special characters are not supported
- Sql Administrator Login: pick an username for your SQL administrator
- Sql Administrator Login Password: define a strong password for your SQL administrator. It has to include small letters, capital letters, a number and a special character
- Sql Firewall Start IP: Add the public IP of your computer to this field, for testing purposes you can use ```1.1.1.1```
- Sql Firewall End IP: Add the public IP of your computer to this field, for testing purposes you can use ```255.255.255.255```

The template includes the following components
- IoT Hub
- Azure Function
- SQL DB
- EventHub
- StreamAnalytics

If you would like to deploy the ARM template manually you can find the code in the ```/arm``` directory.

### Source code deployment

This chapter describes how to deploy the source code into the created Azure components in step before.

Before starting with the deployment, please make sure that the Azure services have been deployed and the necessary tool prerequisites have been installed on your local machine.

Clone this github repository to your local computer:

```git clone https://github.com/Azure-Samples/semtech-lr1110-azureiot-integration```

### Azure SQL DB Deployment

1. Open the ```SensorDataSQLDB``` Projekt with Visual Studio Code
2. Make sure to establish the connection to the previously created DB with the Visual Studio Code SQL extension
3. Open the ```signal_position.sql``` file in the project folder
4. Click the execture button in the top right corner and make sure to pick the previously created connection
5. The query should be successfully executed

### Azure Stream Analytics deployment

1. Open the ```DataPipelineASA``` Projekt with Visual Studio Code
2. The Azure Stream Analytics Visual Code extension should recognize the project
3. Open the ```decoder-input.json``` file in the Inputs folder
4. Use the Azure Stream Analytics extension and the offered wizard to add the previously created Azure EventHub as input
5. Open the ```output.json`` file in the Outputs folder
6. Use the Azure Stream Analytics extension and the offered wizard to add the previously created Azure SQLDB as output
    1. Make sure to use the same User and Password as defined in the deployment
    2. Use the wizard to set the password in the file to store it in the secure configuration manager
    3. The SQL output table has the name ```signal_position```
7. Open the file ```loraedge-ASA.asaql``` and use the Visual Studio Code Command Palette (Ctrl-Shift-P) to run the following command: ```ASA: Submit to Azure```
8. Follow the wizard to deploy your Job to the previously deployed ASA instance on Azure


### Router Function deployment

### Decoder Function deployment

### Function configuration



 
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
