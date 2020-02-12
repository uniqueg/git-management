#!/usr/bin/env python3

"""Creates a repository on GitHub.com.

A personal GitHub access token with write access to source and destination
repositories is required to be defined in environment variable 'GITHUB_TOKEN'.
"""

__version__ = '0.1.0'

import argparse
import logging
import os
import sys

from github import Github
from github.GithubObject import NotSet

logger = logging.getLogger()


def parse_args():
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description=sys.modules[__name__].__doc__,
    )
    parser.add_argument(
        'name',
        type=str,
        action='store',
        help="desired name of repository",
        metavar='NAME',
    )
    parser.add_argument(
        '--org',
        type=str,
        action='store',
        default=None,
        help=(
            "organization under which the repository shall be created; if "
            "omitted, the user's repositories are searched"
        ),
        metavar='STR',
    )
    parser.add_argument(
        '--description',
        type=str,
        action='store',
        default=NotSet,
        help="project description",
        metavar='STR',
    )
    parser.add_argument(
        '--homepage',
        type=str,
        action='store',
        default=NotSet,
        help="url with more info about project",
        metavar='STR',
    )
    parser.add_argument(
        '--private',
        action='store_true',
        default=False,
        help="whether the project is supposed to be private",
    )
    parser.add_argument(
        '--no-issues',
        dest='has_issues',
        action='store_false',
        default=True,
        help="disable issue tracker",
    )
    parser.add_argument(
        '--no-wiki',
        dest='has_wiki',
        action='store_false',
        default=True,
        help="disable wiki",
    )
    parser.add_argument(
        '--no-downloads',
        dest='has_downloads',
        action='store_false',
        default=True,
        help="disable downloads",
    )
    parser.add_argument(
        '--no-projects',
        dest='has_projects',
        action='store_false',
        default=True,
        help="disable project boards",
    )
    parser.add_argument(
        '--no-squash-merge',
        dest='allow_squash_merge',
        action='store_false',
        default=True,
        help="disable squash merges",
    )
    parser.add_argument(
        '--no-merge-commit',
        dest='allow_merge_commit',
        action='store_false',
        default=True,
        help="disable merge commits",
    )
    parser.add_argument(
        '--no-rebase-merge',
        dest='allow_rebase_merge',
        action='store_false',
        default=True,
        help="disable rebase merges",
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
        if args.org:
            org = g.get_organization(args.org)
        else:
            org = g.get_user()
    except Exception as e:
        logger.error(f"Could not connect to GitHub. Error: {e}")
        raise

    # Create repository
    try:
        org.create_repo(
            name=args.name,
            description=args.description,
            homepage=args.homepage,
            private=args.private,
            has_issues=args.has_issues,
            has_wiki=args.has_wiki,
            has_downloads=args.has_downloads,
            has_projects=args.has_projects,
            auto_init=False,
            allow_squash_merge=args.allow_squash_merge,
            allow_merge_commit=args.allow_merge_commit,
            allow_rebase_merge=args.allow_rebase_merge,
        )
    except Exception as e:
        logger.error(f"Could not create repository. Error: {e}")
        raise


if __name__ == '__main__':
    try:
        main()
    except Exception:
        sys.exit(1)
