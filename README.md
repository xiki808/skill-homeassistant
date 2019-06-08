# <img src='https://raw.githack.com/FortAwesome/Font-Awesome/master/svgs/solid/home.svg' card_color='#000000' width='50' height='50' style='vertical-align:bottom'/> Home Assistant
Control Home Assistant devices

## About 
[Home Assistant](https://www.home-assistant.io/) lets you control all your smart devices in a single easy to use interface. This skill uses the open source Home Assistant's APIs to control devices and entities.

This skill leverages the CommonIoT framework, and depends on the [IoT Control Skill](https://github.com/MycroftAI/skill-iot-control)

## Examples 
* "Turn on the office light."
* "Set the heat to 72."
* "Where is my phone?"
* "Turn off the bedside outlet."
* "What is the living room temperature?"
* "Run SCRIPT."
* "Execute AUTOMATION."
* "Activate SCENE"

## Credits 
@BongoEADGC6
@btotharye
Mycroft AI (@mycroftai)

## Category
**IoT**

## Tags
#homeautomation
#iot
#homeassistant
#smarthome

###  Enabling using the conversation component as Fallback

Home-Assistant [supports basic speech based communication](https://www.home-assistant.io/components/conversation/).
When enabling the setting `Enable conversation component as fallback` on home.mycroft.ai, sentences that were not parsed
by any skill before (based on matching keywords) will be passed to this conversation component at the local Home-Assistant server.
Like this, Mycroft will answer default and custom sentences specified in Home-Assistant.
