"""
Command line utility for accessing SKA SDP configuration.

Usage:
  sdpcfg [options] (get|watch) <path>
  sdpcfg [options] [watch] (ls|list) [values] <path>
  sdpcfg [options] delete <path>
  sdpcfg [options] (create|update) <path> <value>
  sdpcfg [options] create_pb <workflow>
  sdpcfg --help

Options:
  -q, --quiet          Cut back on unneccesary output

Environment Variables:
  SDP_CONFIG_BACKEND   Database backend (default etcd3)
  SDP_CONFIG_HOST      Database host address (default 127.0.0.1)
  SDP_CONFIG_PORT      Database port (default 2379)
  SDP_CONFIG_PROTOCOL  Database access protocol (default http)
  SDP_CONFIG_CERT      Client certificate
  SDP_CONFIG_USERNAME  User name
  SDP_CONFIG_PASSWORD  User password
"""

# pylint: disable=E1111,R0912

import sys
import re
import docopt
from ska_sdp_config import entity


def cmd_get(txn, path, args):
    """Get raw value from database."""
    val = txn.raw.get(path)
    if args['--quiet']:
        print(val)
    else:
        print("{} = {}".format(path, val))


def cmd_list(txn, path, args):
    """List raw keys/values from database."""
    keys = txn.raw.list_keys(path)
    if args['--quiet']:
        if args['values']:
            values = [txn.raw.get(key) for key in keys]
            print(", ".join(values))
        else:
            print(", ".join(keys))
    else:
        if args['values']:
            print("Keys with {} prefix:".format(path))
            for key in keys:
                value = txn.raw.get(key)
                print("{} = {}".format(key, value))
        else:
            print("Keys with {} prefix: {}".format(path, ", ".join(keys)))


def cmd_create(txn, path, value, _args):
    """Create raw key."""
    txn.raw.create(path, value)


def cmd_update(txn, path, value, _args):
    """Update raw key value."""
    txn.raw.update(path, value)


def cmd_delete(txn, path, _args):
    """Delete a key."""
    txn.raw.delete(path)


def cmd_create_pb(txn, workflow, _args):
    """Create a processing block."""
    pb_id = txn.new_processing_block_id(workflow['type'])
    txn.create_processing_block(entity.ProcessingBlock(pb_id, None, workflow))
    return pb_id


def main(argv):
    """Command line interface implementation."""
    args = docopt.docopt(__doc__, argv=argv)

    # Validate
    path = args["<path>"]
    success = True
    if path is not None:
        if path[0] != '/':
            print("Path must start with '/'!", file=sys.stderr)
            success = False
        if args['list'] is None and path[-1] == '/':
            print("Key path must not end with '/'!", file=sys.stderr)
            success = False
        if not re.match('^[a-zA-Z0-9_\\-/]*$', path):
            print("Path contains non-permissable characters!", file=sys.stderr)
            success = False
    workflow = args['<workflow>']
    if workflow is not None:
        workflow = workflow.split(':')
        if len(workflow) != 3:
            print("Please specify workflow as 'type:name:version'!",
                  file=sys.stderr)
            success = False
        else:
            workflow = {
                'type': workflow[0],
                'name': workflow[1],
                'version': workflow[2]
            }

    # Input can be taken from stdin
    value = args["<value>"]
    if value == '-':
        value = sys.stdin.read()
    if not success:
        print(__doc__, file=sys.stderr)
        exit(1)

    # Get configuration client, start transaction
    import ska_sdp_config
    cfg = ska_sdp_config.Config()
    try:
        for txn in cfg.txn():
            if args['ls'] or args['list']:
                cmd_list(txn, path, args)
            elif args['watch'] or args['get']:
                cmd_get(txn, path, args)
            elif args['create']:
                cmd_create(txn, path, value, args)
            elif args['update']:
                cmd_update(txn, path, value, args)
            elif args['delete']:
                cmd_delete(txn, path, args)
            elif args['create_pb']:
                pb_id = cmd_create_pb(txn, workflow, args)
            if args['watch']:
                txn.loop(wait=True)

        # Possibly give feedback after transaction has concluded
        if not args['--quiet']:
            if args['create'] or args['update'] or args['delete']:
                print("OK")
            if args['create_pb']:
                print("OK, pb_id = {}".format(pb_id))

    except KeyboardInterrupt:
        if not args['watch']:
            raise
