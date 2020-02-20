#!/usr/bin/env python3

"""Clones labels from source to destination repository.

A personal GitHub access token with write access to source and destination
repositories is required to be defined in environment variable 'GITHUB_TOKEN'.
"""

__version__ = '0.1.0'

import argparse
import logging
import os
import sys

from github import Github
from github.GithubException import UnknownObjectException

logger = logging.getLogger()


def parse_args():
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description=sys.modules[__name__].__doc__,
    )
    parser.add_argument(
        'source',
        type=str,
        action='store',
        help="name of the source repository",
        metavar='SOURCE',
    )
    parser.add_argument(
        'dest',
        type=str,
        action='store',
        help="name of the destination repository",
        metavar='DEST',
    )
    parser.add_argument(
        '--org-source',
        type=str,
        action='store',
        default=None,
        help=(
            "organization under which the source repository is hosted; if "
            "omitted, the user's repositories are searched"
        ),
        metavar='STR',
    )
    parser.add_argument(
        '--org-dest',
        type=str,
        action='store',
        default=None,
        help=(
            "organization under which the destination repository is hosted; "
            "omitted, the user's repositories are searched"
        ),
        metavar='STR',
    )
    parser.add_argument(
        '--overwrite',
        action='store_true',
        default=False,
        help="update existing labels",
    )
    parser.add_argument(
        '--delete-source-labels',
        action='store_true',
        default=False,
        help="delete all existing labels",
    )
    parser.add_argument(
        '--verbose', "-v",
        action='store_true',
        default=False,
        help="print logging messages to STDERR",
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        default=False,
        help="also print debugging messages to STDERR",
    )
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s {version}'.format(version=__version__),
        help="show version information and exit",
    )

    return parser.parse_args()


def setup_logging(
    logger: logging.Logger,
    verbose: bool = False,
    debug: bool = False,
):
    """Configure logging."""
    if debug:
        logger.setLevel(logging.DEBUG)
    elif verbose:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "[%(asctime)-15s: %(levelname)-8s @ %(funcName)s] %(message)s"
    ))
    logger.addHandler(handler)


def main():
    # Parse CLI arguments
    args = parse_args()

    # Set up logging
    setup_logging(
        logger=logger,
        verbose=args.verbose,
        debug=args.debug,
    )

    # Set up GitHub API client
    try:
        g = Github(os.environ['GITHUB_TOKEN'])
    except KeyError:
        logger.error("Environment variable 'GITHUB_TOKEN' not defined.")
        raise

    # Get repo owner
    try:
        if args.org_source:
            org_source = g.get_organization(args.org_source)
        else:
            org_source = g.get_user()
        if args.org_dest:
            org_dest = g.get_organization(args.org_dest)
        else:
            org_dest = g.get_user()
    except Exception as e:
        logger.error(f"Could not connect to GitHub. Error: {e}")
        raise

    # Get repos
    try:
        repo_source = org_source.get_repo(args.source)
    except UnknownObjectException:
        logger.error(
            f"Source repo '{args.source}' could not be found at user/org "
            f"'{org_source.login}'."
        )
        raise
    try:
        repo_dest = org_dest.get_repo(args.dest)
    except UnknownObjectException:
        logger.error(
            f"Destination repo '{args.dest}' could not be found at user/org "
            f"'{org_dest.login}'."
        )
        raise

    # Delete labels in destination, if requested
    if args.delete_source_labels:
        i = 1
        for label in repo_dest.get_labels():
            logger.info(f"Deleting source label {i}: '{label.name}'")
            label.delete()
            i += 1

    # Loop over labels in source
    i = 1
    for label in repo_source.get_labels():
        logger.info(f"Processing label {i}: '{label.name}'")

        # Handle existing labels in dest repo
        try:
            existing_label = repo_dest.get_label(name=label.name)
            if args.overwrite:
                logger.info(
                    f"Updating label '{label.name}' in "
                    f"'{org_dest.login}/{repo_dest.name}'"
                )
                existing_label.edit(
                    name=label.name,
                    color=label.color,
                    description=label.description,
                )
            else:
                logger.info(
                    f"Label exists in '{org_dest.login}/{repo_dest.name}'. "
                    "Skipped."
                )

        # Handle missing labels in dest repo
        except UnknownObjectException:
            logger.info(
                f"Creating label '{label.name}' in "
                f"'{org_dest.login}/{repo_dest.name}'"
            )
            repo_dest.create_label(
                name=label.name,
                color=label.color,
                description=label.description,
            )
        i += 1


if __name__ == '__main__':
    try:
        main()
    except Exception:
        sys.exit(1)
