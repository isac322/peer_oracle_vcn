from __future__ import annotations

import argparse
from collections.abc import Mapping
from enum import Enum
from os import PathLike
from pathlib import Path
from typing import Any

from oci import config

from connect_oracle_vcn import commands

OCI_CONFIG = Mapping[str, Any]


class SubCommand(str, Enum):
    INTER_TENANCIES = 'inter_tenant'
    INTRA_TENANT = 'intra_tenant'
    LIST_GROUP = 'list_group'
    LIST_VCN = 'list_vcn'
    LIST_ROUTE_TABLE = 'list_route_table'


def _get_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    sub_cmd = parser.add_subparsers(title='Sub Command', dest='cmd', required=True)

    same_tenancy = sub_cmd.add_parser(SubCommand.INTRA_TENANT)
    _add_common_arguments(same_tenancy)
    _add_common_connect_arguments(same_tenancy)
    same_tenancy.add_argument(
        '--profile',
        type=str,
        default=config.DEFAULT_PROFILE,
    )

    diff_tenancies = sub_cmd.add_parser(SubCommand.INTER_TENANCIES)
    _add_common_arguments(diff_tenancies)
    _add_common_connect_arguments(diff_tenancies)
    diff_tenancies.add_argument(
        '--requestor-profile',
        type=str,
        required=True,
    )
    diff_tenancies.add_argument(
        '--acceptor-profile',
        type=str,
        required=True,
    )

    list_vcn = sub_cmd.add_parser(SubCommand.LIST_VCN)
    _add_common_arguments(list_vcn)
    list_vcn.add_argument(
        '--profile',
        type=str,
        default=config.DEFAULT_PROFILE,
    )

    list_group = sub_cmd.add_parser(SubCommand.LIST_GROUP)
    _add_common_arguments(list_group)
    list_group.add_argument(
        '--profile',
        type=str,
        default=config.DEFAULT_PROFILE,
    )

    list_route_table = sub_cmd.add_parser(SubCommand.LIST_ROUTE_TABLE)
    _add_common_arguments(list_route_table)
    list_route_table.add_argument(
        '--profile',
        type=str,
        default=config.DEFAULT_PROFILE,
    )
    list_route_table.add_argument(
        '--vcn-ocid',
        type=str,
        default=None,
    )

    return parser


def _validate_file_path(p: PathLike) -> Path:
    try:
        path = Path(p).expanduser()
    except Exception:
        raise argparse.ArgumentTypeError(f'{p} is not a file')

    if not path.is_file():
        raise argparse.ArgumentTypeError(f'{p} is not a file')

    return path


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        '--api-config-file',
        help='OCI API config file path',
        type=_validate_file_path,
        default=config.DEFAULT_LOCATION,
    )

    parser.add_argument(
        '--verbose',
        help='increase output verbosity',
        action='store_true',
        default=False,
    )


def _add_common_connect_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        '--requestor-vcn-ocid',
        help='VCN OCID of requestor',
        type=str,
        default=None,
    )
    parser.add_argument(
        '--acceptor-vcn-ocid',
        help='VCN OCID of acceptor',
        type=str,
        default=None,
    )
    parser.add_argument(
        '--requestor-group-ocid',
        help='Group OCID of requestor',
        type=str,
        default=None,
    )
    parser.add_argument(
        '--requestor-route-table-ocid',
        help='Route Table OCID of requestor to register LGP',
        type=str,
        default=None,
    )
    parser.add_argument(
        '--acceptor-route-table-ocid',
        help='Route Table OCID of acceptor to register LGP',
        type=str,
        default=None,
    )
    parser.add_argument(
        '--requestor-cidr',
        help='CIDR of requestor to add acceptor\'s Route Table',
        type=str,
        required=True,
    )
    parser.add_argument(
        '--acceptor-cidr',
        help='CIDR of acceptor to add requestor\'s Route Table',
        type=str,
        required=True,
    )


def load_command() -> commands.Command:
    parser = _get_arg_parser()
    args = parser.parse_args()

    if args.cmd == SubCommand.INTRA_TENANT:
        return commands.PeerWithinTenant(
            oci_config=config.from_file(
                file_location=args.api_config_file,
                profile_name=args.profile,
            ),
            requestor_vcn=args.requestor_vcn_ocid,
            acceptor_vcn=args.acceptor_vcn_ocid,
            requestor_group=args.requestor_group_ocid,
            requestor_route_table=args.requestor_route_table_ocid,
            acceptor_route_table=args.acceptor_route_table_ocid,
            requestor_cidr=args.requestor_cidr,
            acceptor_cidr=args.acceptor_cidr,
        )
    elif args.cmd == SubCommand.INTER_TENANCIES:
        return commands.PeerInterTenancies(
            requestor_oci_config=config.from_file(
                file_location=args.api_config_file,
                profile_name=args.requestor_profile,
            ),
            acceptor_oci_config=config.from_file(
                file_location=args.api_config_file,
                profile_name=args.acceptor_profile,
            ),
            requestor_vcn=args.requestor_vcn_ocid,
            acceptor_vcn=args.acceptor_vcn_ocid,
            requestor_group=args.requestor_group_ocid,
            requestor_route_table=args.requestor_route_table_ocid,
            acceptor_route_table=args.acceptor_route_table_ocid,
            requestor_cidr=args.requestor_cidr,
            acceptor_cidr=args.acceptor_cidr,
        )
    elif args.cmd == SubCommand.LIST_VCN:
        return commands.ListVCNs(
            oci_config=config.from_file(
                file_location=args.api_config_file,
                profile_name=args.profile,
            ),
        )
    elif args.cmd == SubCommand.LIST_GROUP:
        return commands.ListGroups(
            oci_config=config.from_file(
                file_location=args.api_config_file,
                profile_name=args.profile,
            ),
        )
    elif args.cmd == SubCommand.LIST_ROUTE_TABLE:
        return commands.ListRouteTables(
            oci_config=config.from_file(
                file_location=args.api_config_file,
                profile_name=args.profile,
            ),
            vcn_ocid=args.vcn_ocid,
        )
    else:
        raise ValueError(f'Unknown command: {args.cmd}')