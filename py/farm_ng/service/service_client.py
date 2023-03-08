# Copyright (c) farm-ng, inc.
#
# Licensed under the Amiga Development Kit License (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://github.com/farm-ng/amiga-dev-kit/blob/main/LICENSE
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
from dataclasses import dataclass

import grpc
from farm_ng.service import service_pb2
from farm_ng.service import service_pb2_grpc


@dataclass
class ClientConfig:
    """Client configuration.

    Attributes:
        port (int): the port to connect to the server.
        address (str): the address to connect to the server.
    """

    port: int  # the port of the server address
    address: str = "localhost"  # the address name of the server


class ServiceState:
    """Generic service state.

    Possible state values:
        - UNKNOWN: undefined state.
        - RUNNING: the service is up AND streaming.
        - IDLE: the service is up AND NOT streaming.
        - UNAVAILABLE: the service is not available.
        - ERROR: the service is an error state.

    Args:
        proto (service_pb2.ServiceState): protobuf message containing the service state.
    """

    def __init__(self, proto: service_pb2.ServiceState = None) -> None:
        self._proto = service_pb2.ServiceState.UNAVAILABLE
        if proto is not None:
            self._proto = proto

    @property
    def value(self) -> int:
        """Returns the state enum value."""
        return self._proto

    @property
    def name(self) -> str:
        """Return the state name."""
        return service_pb2.ServiceState.DESCRIPTOR.values[self.value].name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: ({self.value}, {self.name})"


class ServiceClient:
    """Generic client.

    Generic client class to connect with the Amiga brain services.
    Internally implements an `asyncio` gRPC channel.
    Designed to be imported by service specific clients.

    Args:
        config (ClientConfig): the grpc configuration data structure.
    """

    def __init__(self, config: ClientConfig) -> None:
        self.config = config

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f"Config in ServiceClient: {config}")

        # create an async connection with the server
        self.channel = grpc.aio.insecure_channel(self.server_address)
        self.state_stub = service_pb2_grpc.ServiceBaseStub(self.channel)

    @property
    def server_address(self) -> str:
        """Returns the composed address and port."""
        return f"{self.config.address}:{self.config.port}"

    async def get_state(self) -> ServiceState:
        state: ServiceState

        # check if the channel is in a transient failure state
        state_ch = self.channel.get_state()
        if state_ch == grpc.ChannelConnectivity.TRANSIENT_FAILURE:
            state = ServiceState()
            self.logger.debug(f" {self.__class__.__name__} on port: %s state is: %s", self.config.port, state.name)
            return state

        # get the service state
        try:
            response: service_pb2.GetServiceStateReply = await self.state_stub.getServiceState(
                service_pb2.GetServiceStateRequest()
            )
            state = ServiceState(response.state)
        except grpc.RpcError:
            state = ServiceState()

        self.logger.debug(f" {self.__class__.__name__} on port: %s state is: %s", self.config.port, state.name)
        return state
