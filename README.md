# Semtech LoRa Edge Tracker and Azure IoT Integration

The LR1110 LoRa Edge tracker is Semtech's new base design tracker technology. It is battery operated, leverages LoRa connectivity, and it doesn't require a GPS because it scans for geolocation signals such as WiFi and GNSS to compute its location in the cloud, making it very cost effective.
The payload coming from the tracker needs to be decoded, which you can do by leveraging Semtech's open source library that interacts with their LoRa Cloud geolocation service.

This project takes Semtech's decoder to the next level by integrating it with Azure IoT Hub and making it easy to deploy to your Azure subscription via an Azure Resource Manager (ARM) template and leverage Azure services to implement your business applications. Because there is code that is depedent on the LoRaWAN Network Server (LNS) implementation being used, we provide support for 3 popular LNS providers as an example: Actility, Helium, and The Things Industries. Users of this code are welcome to extend it to support additional LNS providers.

## Features

This project framework provides the following features:

* Feature 1
* Feature 2
* ...

## Getting Started

### Prerequisites

(ideally very short, if any)

- OS
- Library version
- ...

### Installation

(ideally very short)

- npm install [package name]
- mvn install
- ...

### Quickstart
(Add steps to get up and running quickly)

1. git clone [repository clone url]
2. cd [respository name]
3. ...


## Demo

A demo app is included to show how to use the project.

To run the demo, follow these steps:

(Add steps to start up the demo)

1.
2.
3.

## Resources

(Any additional resources or related projects)

- Link to supporting information
- Link to similar sample
- ...
