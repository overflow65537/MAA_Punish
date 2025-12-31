from maa.agent.agent_server import AgentServer
from action.basics.IdentifyRoles import IdentifyRoles
from action.basics.MultiplayerAutoBattle import MultiplayerAutoBattle
from action.basics.ScreenShot import ScreenShot
from action.basics.SetTower import SetTower
from action.basics.Count import Count
from action.basics.PPOverride import PPOverride
from action.basics.ChainLoopCircuit import ChainLoopCircuit
from action.basics.RoleSelection import RoleSelection
from action.basics.RecognitionRole import RecognitionRole
from action.basics.Post_Stop import PostStop
from action.basics.Notice import Notice
from action.basics.RoleSelectionType import RoleSelectionType


from action.exclusives.CrimsonWeave import CrimsonWeave
from action.exclusives.LostLullaby import LostLullaby
from action.exclusives.Oblivion import Oblivion
from action.exclusives.Pyroath import Pyroath
from action.exclusives.Stigmata import Stigmata
from action.exclusives.Shukra import Shukra
from action.exclusives.Hyperreal import Hyperreal
from action.exclusives.Crepuscule import Crepuscule
from action.exclusives.Aegis import Aegis
from action.exclusives.Limpidity import Limpidity
from action.exclusives.GeneralFight import GeneralFight
from action.exclusives.Pianissimo import Pianissimo
from action.exclusives.Spectre import Spectre


from recognition.exclusives.CalculateScore import CalculateScore
from recognition.exclusives.IDFMembers import IDFMembers
from recognition.exclusives.IDFscore import IDFscore
from recognition.exclusives.LogicalOperators import LOp
from recognition.exclusives.CheckResolution import CheckResolution
from recognition.exclusives.AutoCounter import AutoCounter
from recognition.exclusives.NextStageRecognition import NextStageRecognition

        
@AgentServer.custom_action("RoleSelectionType")
class Agent_RoleSelectionType(RoleSelectionType):
    pass


@AgentServer.custom_action("Notice")
class Agent_Notice(Notice):
    pass


@AgentServer.custom_action("Pianissimo")
class Agent_Pianissimo(Pianissimo):
    pass


@AgentServer.custom_action("Spectre")
class Agent_Spectre(Spectre):
    pass


@AgentServer.custom_action("PostStop")
class Agent_PostStop(PostStop):
    pass


@AgentServer.custom_action("Limpidity")
class Agent_Limpidity(Limpidity):
    pass


@AgentServer.custom_recognition("NextStageRecognition")
class Agent_NextStageRecognition(NextStageRecognition):
    pass


@AgentServer.custom_action("Aegis")
class Agent_Aegis(Aegis):
    pass


@AgentServer.custom_action("RecognitionRole")
class Agent_RecognitionRole(RecognitionRole):
    pass


@AgentServer.custom_action("RoleSelection")
class Agent_RoleSelection(RoleSelection):
    pass


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



@AgentServer.custom_action("SetTower")
class Agent_SetTower(SetTower):
    pass


@AgentServer.custom_action("IdentifyRoles")
class Agent_IdentifyRoles(IdentifyRoles):
    pass


@AgentServer.custom_action("MultiplayerAutoBattle")
class Agent_MultiplayerAutoBattle(MultiplayerAutoBattle):
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
