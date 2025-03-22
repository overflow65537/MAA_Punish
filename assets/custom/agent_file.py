from maa.agent.agent_server import AgentServer
from action.basics.CenterCamera import CenterCamera
from action.basics.CombatActions import CombatActions
from action.basics.Identify import Identify
from action.basics.IdentifyRoles import IdentifyRoles
from action.basics.MultiplayerAutoBattle import MultiplayerAutoBattle
from action.basics.ResetIdentify import ResetIdentify
from action.basics.ScreenShot import ScreenShot
from action.basics.SelectCharacter import SelectCharacter
from action.basics.SetTower import SetTower
from action.basics.Count import Count
from action.basics.PPOverride import PPOverride


from action.exclusives.CrimsonWeave import CrimsonWeave
from action.exclusives.LostLullaby import LostLullaby
from action.exclusives.Oblivion import Oblivion
from action.exclusives.Pyroath import Pyroath
from action.exclusives.Stigmata import Stigmata


from recognition.exclusives.CalculateScore import CalculateScore
from recognition.exclusives.IDFMembers import IDFMembers
from recognition.exclusives.IDFscore import IDFscore
from recognition.exclusives.IDFMasteryLevel import IDFMasteryLevel


@AgentServer.custom_action("PPOverride")
class Agent_PPOverride(PPOverride):
    pass


@AgentServer.custom_action("Count")
class Agent_Count(Count):
    pass

@AgentServer.custom_recognition("IDFMasteryLevel")
class Agent_IDFMasteryLevel(IDFMasteryLevel):
    pass


@AgentServer.custom_action("SetTower")
class Agent_SetTower(SetTower):
    pass


@AgentServer.custom_action("CenterCamera")
class Agent_CenterCamera(CenterCamera):
    pass


@AgentServer.custom_action("CombatActions")
class Agent_CombatActions(CombatActions):
    pass


@AgentServer.custom_action("Identify")
class Agent_Identify(Identify):
    pass


@AgentServer.custom_action("IdentifyRoles")
class Agent_IdentifyRoles(IdentifyRoles):
    pass


@AgentServer.custom_action("MultiplayerAutoBattle")
class Agent_MultiplayerAutoBattle(MultiplayerAutoBattle):
    pass


@AgentServer.custom_action("ResetIdentify")
class Agent_ResetIdentify(ResetIdentify):
    pass


@AgentServer.custom_action("ScreenShot")
class Agent_ScreenShot(ScreenShot):
    pass


@AgentServer.custom_action("SelectCharacter")
class Agent_SelectCharacter(SelectCharacter):
    pass


@AgentServer.custom_recognition("CalculateScore")
class Agent_CalculateScore(CalculateScore):
    pass


@AgentServer.custom_recognition("IDFMembers")
class Agent_IDFMembers(IDFMembers):
    pass


@AgentServer.custom_recognition("IDFscore")
class Agent_IDFscore(IDFscore):
    pass


@AgentServer.custom_action("CrimsonWeave")
class Agent_CrimsonWeave(CrimsonWeave):
    pass


@AgentServer.custom_action("LostLullaby")
class Agent_LostLullaby(LostLullaby):
    pass


@AgentServer.custom_action("Oblivion")
class Agent_Oblivion(Oblivion):
    pass


@AgentServer.custom_action("Pyroath")
class Agent_Pyroath(Pyroath):
    pass


@AgentServer.custom_action("Stigmata")
class Agent_Stigmata(Stigmata):
    pass
