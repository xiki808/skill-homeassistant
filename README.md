# Home Assistant Skill for Mycroft

This skill was orphaned and then adopted by the [United Skill Writers](https://community.mycroft.ai/t/united-skill-writers-draft) team

originally created by [BongoEADGC6](https://github.com/BongoEADGC6/mycroft-home-assistant) and then forked by [btotharye](https://github.com/btotharye)

## About 
Home Assistant is a open source project that lets you control all your smart devices in a single easy to use UI.  This skill talks to Home Assistant's REST API and controls devices and entities you have configured.  Control your lights, garage door, thermostats and more.

This is a skill to add [Home Assistant](https://home-assistant.io) support to [Mycroft](https://mycroft.ai). Currently is supports turning on and off several entity types (`light`, `switch`, `scene`, `climate`, `groups` and `input_boolean`).


## Examples 
* "Hey Mycroft, turn on office light"
* "Hey Mycroft, turn off bedroom lights"
* "Hey Mycroft, turn on the AC (AC is a switch object in Home Assistant)"


## Installation
Should be able to install this now via just saying `Hey Mycroft, install skill home assistant` it will then confirm if you want to install it and say yes and you are good to go.

Can also be installed via `msm install https://github.com/JarbasAl/mycroft-homeassistant` or `msm install home assistant`

## Configuration
This skill utilizes the skillsettings.json file which allows you to configure this skill via home.mycroft.ai after a few minutes of having the skill installed you should see something like below in the https://home.mycroft.ai/#/skill location:

Fill this out with your appropriate home assistant information and hit save.

You create the Long-Lived Access Token on the user profile page

![Screenshot](screenshot.JPG?raw=true)

###  Enabling using the conversation component as Fallback

Home-Assistant [supports basic speech based communication](https://www.home-assistant.io/components/conversation/).
When enabling the setting `Enable conversation component as fallback` on home.mycroft.ai, sentences that were not parsed
by any skill before (based on matching keywords) will be passed to this conversation component at the local Home-Assistant server.
Like this, Mycroft will answer default and custom sentences specified in Home-Assistant.

## Usage

Say something like "Hey Mycroft, turn on living room lights". Currently available commands
are "turn on" and "turn off". Matching to Home Assistant entity names is done by scanning
the HA API and looking for the closest matching friendly name. The matching is fuzzy (thanks
to the `fuzzywuzzy` module) so it should find the right entity most of the time, even if Mycroft
didn't quite get what you said.  I have further expanded this to also look at groups as well as lights.  This way if you say turn on the office light, it will do the group and not just 1 light, this can easily be modified to your preference by just removing group's from the fuzzy logic in the code.


Example Code:
So in the code in this section you can just remove group, etc to your liking for the lighting.  I will eventually set this up as variables you set in your config file soon.

```
def handle_lighting_intent(self, message):
        entity = message.data["Entity"]
        action = message.data["Action"]
        LOGGER.debug("Entity: %s" % entity)
        LOGGER.debug("Action: %s" % action)
        ha_entity = self.ha.find_entity(entity, ['group','light', 'switch', 'scene', 'input_boolean'])
        if ha_entity is None:
            #self.speak("Sorry, I can't find the Home Assistant entity %s" % entity)
            self.speak_dialog('homeassistant.device.unknown', data={"dev_name": ha_entity['dev_name']})
            return
        ha_data = {'entity_id': ha_entity['id']}
```

## TODO
 * Increasing and Decreasing Climate controls
 * Script intents processing
 * New intent for opening/closing cover entities
 * New intent for locking/unlocking lock entities (with added security?)
 * New intent for thermostat values, raising, etc.
 * New intent to handle multimedia/kodi

## Contributing

All contributions welcome:

 * Fork
 * Write code
 * Submit merge request

## Credits 
@BongoEADGC6
@btotharye

## Category
**IoT**

## Tags
#homeautomation
#iot
#homeassistant
#smarthome
#hue
#smartbulb
#light
#lighting
#lights
#nest
#temperature
#thermostat
#lifx

## Licence

See [`LICENCE`](https://gitlab.com/robconnolly/mycroft-home-assistant/blob/master/LICENSE).
