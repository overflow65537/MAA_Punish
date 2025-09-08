from maa.agent.agent_server import AgentServer
from action.basics.CenterCamera import CenterCamera
from action.basics.Identify import Identify
from action.basics.IdentifyRoles import IdentifyRoles
from action.basics.MultiplayerAutoBattle import MultiplayerAutoBattle
from action.basics.ResetIdentify import ResetIdentify
from action.basics.ScreenShot import ScreenShot
from action.basics.SetTower import SetTower
from action.basics.Count import Count
from action.basics.PPOverride import PPOverride
from action.basics.ChainLoopCircuit import ChainLoopCircuit


from action.exclusives.CrimsonWeave import CrimsonWeave
from action.exclusives.LostLullaby import LostLullaby
from action.exclusives.Oblivion import Oblivion
from action.exclusives.Pyroath import Pyroath
from action.exclusives.Stigmata import Stigmata
from action.exclusives.Shukra import Shukra
from action.exclusives.Hyperreal import Hyperreal
from action.exclusives.Crepuscule import Crepuscule
from action.exclusives.GeneralFight import   GeneralFight


from recognition.exclusives.CalculateScore import CalculateScore
from recognition.exclusives.IDFMembers import IDFMembers
from recognition.exclusives.IDFscore import IDFscore
from recognition.exclusives.IDFMasteryLevel import IDFMasteryLevel
from recognition.exclusives.LogicalOperators import LOp
from recognition.exclusives.CheckResolution import CheckResolution
from recognition.exclusives.AutoCounter import AutoCounter


@AgentServer.custom_action("GeneralFight")
class Agent_GeneralFight(GeneralFight):
    pass

@AgentServer.custom_action("Hyperreal")
class Agent_Hyperreal(Hyperreal):
    pass

@AgentServer.custom_action("Crepuscule")
class Agent_Crepuscule(Crepuscule):
    pass

@AgentServer.custom_recognition("AutoCounter")
class Agent_AutoCounter(AutoCounter):
    pass

@AgentServer.custom_recognition("CheckResolution")
class Agent_CheckResolution(CheckResolution):
    pass

@AgentServer.custom_recognition("LOp")
class Agent_LOp(LOp):
    pass


@AgentServer.custom_action("ChainLoopCircuit")
class Agent_ChainLoopCircuit(ChainLoopCircuit):
    pass


@AgentServer.custom_action("Shukra")
class Agent_Shukra(Shukra):
    pass


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
