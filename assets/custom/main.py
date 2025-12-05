import sys
from maa.agent.agent_server import AgentServer
from maa.toolkit import Toolkit

from agent_file import *


def main():
    Toolkit.init_option("./")
    if len(sys.argv) > 1:
        socket_id = sys.argv[-1]
    else:
        socket_id = "MAA_AGENT_SOCKET"
    AgentServer.start_up(socket_id)
    AgentServer.join()
    AgentServer.shut_down()


if __name__ == "__main__":
    main()
