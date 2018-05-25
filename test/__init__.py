from test.integrationtests.skills.skill_tester import SkillTest

import mock


def test_runner(skill, example, emitter, loader):

    ha_data = {'entity_id': 'light.kitchen_lights'}

    s = [s for s in loader.skills if s and s.root_dir == skill]
    s[0].homeassistant = mock.MagicMock()
    s[0].homeassistant.ha.execute_service("homeassistant", "turn_on", ha_data)
    return SkillTest(skill, example, emitter).run(loader)
