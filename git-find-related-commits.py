#!/usr/bin/env python3

"""
https://stackoverflow.com/questions/66731069/how-to-find-pairs-groups-of-most-related-commits
"""

from __future__ import annotations
from typing import List, Optional, Tuple
import git
import contextlib
import sys
import better_exchook


_TmpBranchName = "tmp-find-related-commits"


class GitHelper:
  def __init__(self, repo_dir: str):
    self.repo = git.Repo(repo_dir)
    self.main_branch = "origin/master"
    self.local_branch = self.repo.active_branch
    assert self.local_branch.name != _TmpBranchName

  def get_base_commit(self) -> git.Commit:
    """
    Returns:
    On some branch, return the base commit which is in the main branch (e.g. origin/master).
    """
    return self.repo.merge_base(self.main_branch, self.local_branch)[0]

  def get_commit_list(self) -> List[git.Commit]:
    """
    Returns:
    All the commits starting from the main branch.
    """
    return list(reversed(list(self.repo.iter_commits(f"{self.get_base_commit()}..{self.local_branch}"))))

  def score_commit_pair_squash(self, commits: List[git.Commit]) -> Tuple[Optional[int], Optional[int], List[str]]:
    commit0 = commits[0]
    assert len(commit0.parents) == 1  # not implemented otherwise...
    commit0 = commit0.parents[0]
    # print(f"Start at {_format_commit(commit0)}")
    diffs = []
    diff_counts = []
    rel_diff_c = None
    with self.in_tmp_branch(commit0):
      for commit in commits:
        # print(f"Apply {_format_commit(commit)}")
        try:
          self.repo.git.cherry_pick(commit, "--keep-redundant-commits")
        except git.GitCommandError:
          return None, None, diffs
        diff_str = self.repo.git.diff(f"{commit0}..HEAD")
        c = _count_changed_lines(diff_str)
        if diff_counts:
          commit_diff_str = self.repo.git.show(commit)
          cc = _count_changed_lines(commit_diff_str)
          rel_diff = c - diff_counts[-1]
          rel_diff_c = rel_diff - cc
          if rel_diff_c >= 0:  # this commit has no influence on the prev commit. so skip this whole proposed squash
            return None, None, diffs
        diffs.append(diff_str)
        diff_counts.append(c)
    rel_diff = diff_counts[-1] - diff_counts[0]
    return rel_diff, rel_diff_c, diffs

  def test(self):
    commits = self.get_commit_list()
    print("All commits:")
    for commit in commits:
      print(f"  {_format_commit(commit)}")
    print("Iterate...")
    results = []
    for i in range(len(commits)):
      for j in range(i + 1, len(commits)):
        commit_pair = [commits[i], commits[j]]
        c, c_, diffs = self.score_commit_pair_squash(commit_pair)
        print("Commits:", [_format_commit(commit) for commit in commit_pair], "relative diff count:", c)
        if c is not None:
          results.append((c_, c, commit_pair, diffs))

    print("Done. Results:")
    results.sort(key=lambda x: x[0])
    for c_, c, commit_pair, diffs in results:
      print("***", c_, c, "commits:", [_format_commit(commit) for commit in commit_pair])

  @contextlib.contextmanager
  def in_tmp_branch(self, commit: git.Commit) -> git.Head:
    repo = self.repo
    prev_active_branch = repo.active_branch
    tmp_branch = repo.create_head(_TmpBranchName, commit.hexsha, force=True)
    repo.git.checkout(tmp_branch)
    try:
      yield tmp_branch
    except git.GitCommandError as exc:
      print("Git exception occurred. Current git status:")
      print(repo.git.status())
      raise exc
    finally:
      repo.git.reset("--hard")
      repo.git.checkout(prev_active_branch)


def _format_commit(commit: git.Commit) -> str:
  return f"{commit} ({commit.message.splitlines()[0]})"


def _count_changed_lines(s: str) -> int:
  c = 0
  for line in s.splitlines():
    if line.startswith("+ ") or line.startswith("- "):
      c += 1
  return c


def main():
  helper = GitHelper(".")
  helper.test()
  # better_exchook.debug_shell(locals(), globals())


if __name__ == '__main__':
  better_exchook.install()
  try:
    main()
  except KeyboardInterrupt:
    print("KeyboardInterrupt")
    sys.exit(1)
