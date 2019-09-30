#!/usr/bin/python
"""
coresendmsg: utility for generating CORE messages
"""

import optparse
import os
import socket
import sys

from core.api.tlv import coreapi
from core.emulator.enumerations import CORE_API_PORT
from core.emulator.enumerations import MessageFlags
from core.emulator.enumerations import MessageTypes
from core.emulator.enumerations import SessionTlvs

import shlex

def print_available_tlvs(t, tlv_class):
    """
    Print a TLV list.
    """
    print("TLVs available for %s message:" % t)
    for tlv in sorted([tlv for tlv in tlv_class.tlv_type_map], key=lambda x: x.name):
        print("%s:%s" % (tlv.value, tlv.name))


def print_examples(name):
    """
    Print example usage of this script.
    """
    examples = [
        ("link n1number=2 n2number=3 delay=15000",
         "set a 15ms delay on the link between n2 and n3"),
        ("link n1number=2 n2number=3 guiattr=\"color=blue\"",
         "change the color of the link between n2 and n3"),
        ("node number=3 xpos=125 ypos=525",
         "move node number 3 to x,y=(125,525)"),
        ("node number=4 icon=/usr/local/share/core/icons/normal/router_red.gif",
         "change node number 4\"s icon to red"),
        ("node flags=add number=5 type=0 name=\"n5\" xpos=500 ypos=500",
         "add a new router node n5"),
        ("link flags=add n1number=4 n2number=5 if1ip4=\"10.0.3.2\" " \
         "if1ip4mask=24 if2ip4=\"10.0.3.1\" if2ip4mask=24",
         "link node n5 with n4 using the given interface addresses"),
        ("exec flags=str,txt node=1 num=1000 cmd=\"uname -a\" -l",
         "run a command on node 1 and wait for the result"),
        ("exec node=2 num=1001 cmd=\"killall ospfd\"",
         "run a command on node 2 and ignore the result"),
        ("file flags=add node=1 name=\"/var/log/test.log\" data=\"Hello World.\"",
         "write a test.log file on node 1 with the given contents"),
        ("file flags=add node=2 name=\"test.log\" " \
         "srcname=\"./test.log\"",
         "move a test.log file from host to node 2"),
    ]
    print("Example %s invocations:" % name)
    for cmd, descr in examples:
        print("  %s %s\n\t\t%s" % (name, cmd, descr))


def receive_message(sock):
    """
    Retrieve a message from a socket and return the CoreMessage object or
    None upon disconnect. Socket data beyond the first message is dropped.
    """
    try:
        # large receive buffer used for UDP sockets, instead of just receiving
        # the 4-byte header
        data = sock.recv(4096)
        msghdr = data[:coreapi.CoreMessage.header_len]
    except KeyboardInterrupt:
        print("CTRL+C pressed")
        sys.exit(1)

    if len(msghdr) == 0:
        return None

    msgdata = None
    msgtype, msgflags, msglen = coreapi.CoreMessage.unpack_header(msghdr)

    if msglen:
        msgdata = data[coreapi.CoreMessage.header_len:]
    try:
        msgcls = coreapi.CLASS_MAP[msgtype]
    except KeyError:
        msg = coreapi.CoreMessage(msgflags, msghdr, msgdata)
        msg.message_type = msgtype
        print("unimplemented CORE message type: %s" % msg.type_str())
        return msg
    if len(data) > msglen + coreapi.CoreMessage.header_len:
        print("received a message of type %d, dropping %d bytes of extra data" \
              % (msgtype, len(data) - (msglen + coreapi.CoreMessage.header_len)))
    return msgcls(msgflags, msghdr, msgdata)


def connect_to_session(sock, requested):
    """
    Use Session Messages to retrieve the current list of sessions and
    connect to the first one.
    """
    # request the session list
    tlvdata = coreapi.CoreSessionTlv.pack(SessionTlvs.NUMBER.value, "")
    flags = MessageFlags.STRING.value
    smsg = coreapi.CoreSessionMessage.pack(flags, tlvdata)
    sock.sendall(smsg)

    print("waiting for session list...")
    smsgreply = receive_message(sock)
    if smsgreply is None:
        print("disconnected")
        return False

    sessstr = smsgreply.get_tlv(SessionTlvs.NUMBER.value)
    if sessstr is None:
        print("missing session numbers")
        return False

    # join the first session (that is not our own connection)
    tmp, localport = sock.getsockname()
    sessions = sessstr.split("|")
    sessions.remove(str(localport))
    if len(sessions) == 0:
        print("no sessions to join")
        return False

    if not requested:
        session = sessions[0]
    elif requested in sessions:
        session = requested
    else:
        print("requested session not found!")
        return False

    print("joining session: %s" % session)
    tlvdata = coreapi.CoreSessionTlv.pack(SessionTlvs.NUMBER.value, session)
    flags = MessageFlags.ADD.value
    smsg = coreapi.CoreSessionMessage.pack(flags, tlvdata)
    sock.sendall(smsg)
    return True


def receive_response(sock, opt):
    """
    Receive and print a CORE message from the given socket.
    """
    print("waiting for response...")
    msg = receive_message(sock)
    if msg is None:
        print("disconnected from %s:%s" % (opt.address, opt.port))
        sys.exit(0)
    print("received message: %s" % msg)


def send_command(cmd):
    """
    Parse command-line arguments to build and send a CORE message.
    """
    types = [message_type.name for message_type in MessageTypes]
    flags = [flag.name for flag in MessageFlags]
    usagestr = "usage: %prog [-h|-H] [options] [message-type] [flags=flags] "
    usagestr += "[message-TLVs]\n\n"
    usagestr += "Supported message types:\n  %s\n" % types
    usagestr += "Supported message flags (flags=f1,f2,...):\n  %s" % flags
    parser = optparse.OptionParser(usage=usagestr)
    parser.set_defaults(
        port=CORE_API_PORT,
        address="localhost",
        session=None,
        listen=False,
        examples=False,
        tlvs=False,
        tcp=False
    )

    parser.add_option("-H", dest="examples", action="store_true",
                      help="show example usage help message and exit")
    parser.add_option("-p", "--port", dest="port", type=int,
                      help="TCP port to connect to, default: %d" % \
                           parser.defaults["port"])
    parser.add_option("-a", "--address", dest="address", type=str,
                      help="Address to connect to, default: %s" % \
                           parser.defaults["address"])
    parser.add_option("-s", "--session", dest="session", type=str,
                      help="Session to join, default: %s" % \
                           parser.defaults["session"])
    parser.add_option("-l", "--listen", dest="listen", action="store_true",
                      help="Listen for a response message and print it.")
    parser.add_option("-t", "--list-tlvs", dest="tlvs", action="store_true",
                      help="List TLVs for the specified message type.")
    parser.add_option("--tcp", dest="tcp", action="store_true",
                      help="Use TCP instead of UDP and connect to a session default: %s" % parser.defaults["tcp"])

    def usage(msg=None, err=0):
        sys.stdout.write("\n")
        if msg:
            sys.stdout.write(msg + "\n\n")
        parser.print_help()
        sys.exit(err)

    # parse command line opt
    opt, args = parser.parse_args(shlex.split(cmd))
    if opt.examples:
        print_examples(os.path.basename(sys.argv[0]))
        sys.exit(0)
    if len(args) == 0:
        usage("Please specify a message type to send.")

    # given a message type t, determine the message and TLV classes
    t = args.pop(0)
    if t not in types:
        usage("Unknown message type requested: %s" % t)
    message_type = MessageTypes[t]
    msg_cls = coreapi.CLASS_MAP[message_type.value]
    tlv_cls = msg_cls.tlv_class

    # list TLV types for this message type
    if opt.tlvs:
        print_available_tlvs(t, tlv_cls)
        sys.exit(0)

    # build a message consisting of TLVs from "type=value" arguments
    flagstr = ""
    tlvdata = b""
    for a in args:
        typevalue = a.split("=")
        if len(typevalue) < 2:
            usage("Use \"type=value\" syntax instead of \"%s\"." % a)
        tlv_typestr = typevalue[0]
        tlv_valstr = "=".join(typevalue[1:])
        if tlv_typestr == "flags":
            flagstr = tlv_valstr
            continue

        tlv_name = tlv_typestr
        try:
            tlv_type = tlv_cls.tlv_type_map[tlv_name]
            tlvdata += tlv_cls.pack_string(tlv_type.value, tlv_valstr)
        except KeyError:
            usage("Unknown TLV: \"%s\"" % tlv_name)

    flags = 0
    for f in flagstr.split(","):
        if f == "":
            continue

        try:
            flag_enum = MessageFlags[f]
            n = flag_enum.value
            flags |= n
        except KeyError:
            usage("Invalid flag \"%s\"." % f)

    msg = msg_cls.pack(flags, tlvdata)

    if opt.tcp:
        protocol = socket.SOCK_STREAM
    else:
        protocol = socket.SOCK_DGRAM

    sock = socket.socket(socket.AF_INET, protocol)
    sock.setblocking(True)

    try:
        sock.connect((opt.address, opt.port))
    except Exception as e:
        print("Error connecting to %s:%s:\n\t%s" % (opt.address, opt.port, e))
        sys.exit(1)

    if opt.tcp and not connect_to_session(sock, opt.session):
        print("warning: continuing without joining a session!")

    sock.sendall(msg)
    if opt.listen:
        receive_response(sock, opt)
    if opt.tcp:
        sock.shutdown(socket.SHUT_RDWR)
    sock.close()
#    sys.exit(0)


if __name__ == "__main__":
    main()
