import sys
import os

# 添加父目录为sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print(sys.path)

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
