"""Tests for Client class."""

import timeit

import mock
import pytest

import natnet
from natnet.comms import Connection
from natnet.protocol import MessageId


@pytest.fixture(scope='module')
def test_packets():
    server_info = open('tests/serverinfo_packet_v3.bin', 'rb').read()
    mocapframe = open('tests/mocapframe_packet_v3.bin', 'rb').read()
    return {MessageId.ServerInfo: server_info, MessageId.FrameOfData: mocapframe}


def test_client_calls_callback(test_packets):
    # Create client with fake connection
    conn = mock.Mock(Connection)
    server_info = natnet.protocol.deserialize(test_packets[MessageId.ServerInfo])
    client = natnet.Client(conn, server_info)

    # Set wait_for_packet_raw to return a FrameOfData packet the first time, then raise SystemExit the second time
    frame_packet = test_packets[MessageId.FrameOfData]
    received_time = timeit.default_timer()
    conn.wait_for_packet_raw.side_effect = [(frame_packet, received_time), SystemExit]
    # Re-attach wait_for_packet
    conn.wait_for_packet = lambda *args: Connection.wait_for_packet(conn, *args)

    # Run the Client main loop with an inspectable callback
    callback = mock.Mock()
    client.set_callback(callback)
    client.spin()

    # Check call arguments
    callback.assert_called_once()
    frame_message = natnet.protocol.deserialize(
        frame_packet)  # type: natnet.protocol.MocapFrameMessage
    (rigid_bodies, labelled_markers, timing), _ = callback.call_args
    assert rigid_bodies == frame_message.rigid_bodies
    assert labelled_markers == frame_message.labelled_markers
    # SampleClient says 5.5ms
    assert timing.system_latency == pytest.approx(0.005495071)
    # Not sure if its worth testing the other members of timing
