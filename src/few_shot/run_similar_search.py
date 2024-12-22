from commit_similar import SimilarCommitSearch

sim = SimilarCommitSearch('./')
overlaps = sim.search(diff_from=None, diff_to=None, only_staged=False)
print([str(commit_overlap) for commit_overlap in overlaps] if len(overlaps) > 0 else 'No commits found')