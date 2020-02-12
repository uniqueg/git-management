#!/usr/bin/env python3

"""Sets teams associated with a source repository for a destination
repository.

A personal GitHub access token with write access to source and destination
repositories is required to be defined in environment variable 'GITHUB_TOKEN'.

Source and destination repositories must be associated with an organization,
and the organization must be the same for both repositories. Note that all
team permissions are set to their default value.
"""

__version__ = '0.1.0'

import argparse
import logging
import os
import sys

from github import Github
from github.GithubException import (GithubException, UnknownObjectException)

logger = logging.getLogger()


def parse_args():
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description=sys.modules[__name__].__doc__,
    )
    parser.add_argument(
        'org',
        type=str,
        action='store',
        help=(
            "organization under which the source and destination "
            "repositories are hosted"
        ),
        metavar='STR',
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
        org = g.get_organization(args.org)
    except Exception as e:
        logger.error(f"Could not connect to GitHub. Error: {e}")
        raise

    # Get repos
    try:
        repo_source = org.get_repo(args.source)
    except UnknownObjectException:
        logger.error(
            f"Source repo '{args.source}' could not be found at org "
            f"'{org.slug}'."
        )
        raise
    try:
        repo_dest = org.get_repo(args.dest)
    except UnknownObjectException:
        logger.error(
            f"Destination repo '{args.dest}' could not be found at org "
            f"'{org.slug}'."
        )
        raise

    # Get source teams
    try:
        teams_source = repo_source.get_teams()
    except GithubException:
        logger.error(
                f"Could not get teams for repo '{args.source}' at org "
                f"'{org.slug}'."
        )
        raise

    # Add source teams to destination
    error = False
    for team in teams_source:
        try:
            logger.info(
                f"Adding team '{team.name}' to repo '{args.dest}' at org "
                f"'{org.login}'..."
            )
            team.add_to_repos(repo_dest)
        except Exception as e:
            logger.warning(
                f"Could not add team '{team.name}' to repo '{args.dest}' at "
                f"org '{org.login}'. Error: {e}"
            )
            error = e

    # Raise if errors occurred for any team
    if error:
        logger.error(
            f"One or more teams could not be added."
        )
        raise error


if __name__ == '__main__':
    try:
        main()
    except Exception:
        sys.exit(1)
