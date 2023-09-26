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
from __future__ import annotations

import argparse
from typing import Optional

from farm_ng.canbus import canbus_pb2
from farm_ng.canbus.packet import AmigaTpdo1
from farm_ng.canbus.packet import parse_amiga_tpdo1_proto
from farm_ng.core.events_file_reader import build_events_dict
from farm_ng.core.events_file_reader import EventLogPosition
from farm_ng.core.events_file_reader import EventsFileReader


def main(file_name: str, can_interface: str) -> None:
    # create the file reader
    reader = EventsFileReader(file_name)
    success: bool = reader.open()
    if not success:
        raise RuntimeError(f"Failed to open events file: {file_name}")

    # get the index of the events file
    events_index: list[EventLogPosition] = reader.get_index()

    # structure the index as a dictionary of lists of events
    events_dict: dict[str, list[EventLogPosition]] = build_events_dict(events_index)
    print(f"All available topics: {sorted(events_dict.keys())}")

    can_events = events_dict["/canbus/raw_messages"]
    print(f"Found {len(can_events)} packets of canbus_pb2.RawCanbusMessages")

    for event_log in can_events:

        # parse the message
        sample: canbus_pb2.RawCanbusMessages = event_log.read_message()

        msg: canbus_pb2.RawCanbusMessage
        for msg in sample.messages:
            tpdo1: Optional[AmigaTpdo1] = parse_amiga_tpdo1_proto(msg)
            if tpdo1 is not None:
                print(tpdo1)

    assert reader.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="Event file reader example for parsing CAN messages.")
    parser.add_argument("--file-name", type=str, required=True, help="Path to the `events.bin` file.")
    parser.add_argument(
        "--can-interface", type=str, default="can0", help="The name of the can interface to read. Default: oak0."
    )
    args = parser.parse_args()
    main(args.file_name, args.can_interface)
