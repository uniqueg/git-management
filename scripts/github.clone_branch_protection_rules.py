#!/usr/bin/env python3

"""Clones branch protection rules from source to destination repository for
the specified target branches.

A personal GitHub access token with write access to source and destination
repositories is required to be defined in environment variable 'GITHUB_TOKEN'.

Users and teams have to have access to a project in order for their specific
permissions to be successfully cloned. Otherwise these will be silently
omitted.
"""

__version__ = '0.1.0'

import argparse
import logging
import os
import sys

from github import Github
from github.GithubException import (GithubException, UnknownObjectException)
from github.GithubObject import NotSet

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
        '--branch-source',
        type=str,
        action='store',
        default='master',
        help="name of template branch in source repository",
        metavar='STR',
    )
    parser.add_argument(
        '--branch-dest',
        type=str,
        action='store',
        default='master',
        help="name of target branch in destination repository",
        metavar='STR',
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
        '--no-status-checks',
        action='store_true',
        default=False,
        help="do not clone status checks settings",
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

    # Get branches
    try:
        branch_source = repo_source.get_branch(args.branch_source)
    except GithubException:
        logger.error(
            f"Could not find branch '{args.branch_source}' in repo "
            f"'{args.source}' at user/org '{org_source.login}'."
        )
        raise
    try:
        branch_dest = repo_dest.get_branch(args.branch_dest)
    except GithubException:
        logger.error(
            f"Could not find branch '{args.branch_dest}' in repo "
            f"'{args.dest}' at user/org '{org_dest.login}'."
        )
        raise

    # Clone branch protection config
    try:
        # Get source branch protection config
        conf = branch_source.get_protection()
        # Get team & user push restrictions
        team_push_restrictions = conf.get_team_push_restrictions()
        if team_push_restrictions:
            team_push_restrictions = [t.slug for t in team_push_restrictions]
        else:
            team_push_restrictions = []
        user_push_restrictions = conf.get_user_push_restrictions()
        if user_push_restrictions:
            user_push_restrictions = [u.login for u in user_push_restrictions]
        else:
            user_push_restrictions = []
        # Get team & user PR dismissal restrictions
        dismissal_teams = conf.required_pull_request_reviews.dismissal_teams
        if dismissal_teams:
            dismissal_teams = [t.slug for t in dismissal_teams]
        else:
            dismissal_teams = []
        dismissal_users = conf.required_pull_request_reviews.dismissal_users
        if dismissal_users:
            dismissal_users = [u.login for u in dismissal_users]
        else:
            dismissal_users = []
        # Get status check settings
        if args.no_status_checks:
            strict = NotSet
            contexts = NotSet
        else:
            strict = conf.required_status_checks.strict
            contexts = conf.required_status_checks.contexts
        # Update destination branch settings
        branch_dest.edit_protection(
            strict=strict,
            contexts=contexts,
            enforce_admins=conf.enforce_admins,
            dismissal_users=dismissal_users,
            dismissal_teams=dismissal_teams,
            dismiss_stale_reviews=conf.
            required_pull_request_reviews.dismiss_stale_reviews,
            require_code_owner_reviews=conf.
            required_pull_request_reviews.require_code_owner_reviews,
            required_approving_review_count=conf.
            required_pull_request_reviews.required_approving_review_count,
            user_push_restrictions=user_push_restrictions,
            team_push_restrictions=team_push_restrictions,
        )
    except GithubException as e:
        if e.data['message'] == "Branch not protected":
            logger.info(
                f"No protection rules set for branch '{args.branch_dest}' "
                f"in repo '{args.dest}' at user/org '{org_dest.login}'. "
                f"Removing protection rules for destination branch "
                f"'{args.branch_dest}' in repo '{args.dest}' at user/org "
                f"'{org_dest.login}'."
            )
            branch_dest.remove_protection()
        else:
            logger.error(
                f"Could not get protection rules for branch "
                f"'{args.branch_dest}' in repo '{args.dest}' at user/org "
                f"'{org_dest.login}'."
            )
            raise


if __name__ == '__main__':
    try:
        main()
    except Exception:
        sys.exit(1)
