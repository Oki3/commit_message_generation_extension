from git import Repo

class Range:
    start: int
    end: int

    def __init__(self, start: int, end: int):
        self.start = start
        self.end = end

    def git_range(self):
        return f'{self.start},{self.end}'
    
    def empty(self):
        return self.start > self.end

class ChangeBlock:
    file: str
    range_a: Range
    range_b: Range
    text: list[str]

    def __init__(self, file: str, range_a: Range, range_b: Range, text: list[str]):
        self.file = file
        self.range_a = range_a
        self.range_b = range_b
        self.text = text

    def __str__(self):
        return f'{self.file} a/{self.range_a.start}:{self.range_a.end} b/{self.range_b.start}:{self.range_b.end}'

class Commit:
    hash: str
    overlap: int

    def __init__(self, hash: str, overlap: int):
        self.hash = hash
        self.overlap = overlap

    def __str__(self):
        return f'{self.hash} overlaps {self.overlap} line(s)'

class CommitSimilarity:
    repo: Repo
    other = None

    def __init__(self, path: str):
        self.repo = Repo(path)

    def parse_diff_range(self, range_text: str):
        lines = range_text.replace('-', '').split(',')

        index = int(lines[0])
        num_changed = int(lines[1]) if len(lines) > 1 else 1

        return Range(index, index + num_changed - 1)
    
    def parse_change_block(self, file: str, lines: list[str]):
        range_texts = lines[0].split(' ')[1:3]
        range_a = self.parse_diff_range(range_texts[0])
        range_b = self.parse_diff_range(range_texts[1])

        text = lines[1:]

        return ChangeBlock(file, range_a, range_b, text)

    def get_changes(self):
        changes: list[ChangeBlock] = []

        # Get exact diffs for changes that are staged but not committed, only for modified files
        for diff_item in self.repo.index.diff(self.other, cached=True, create_patch=True, unified=0).iter_change_type("M"):
            diff_text = diff_item.diff.decode('utf-8', errors='replace') if isinstance(diff_item.diff, bytes) else diff_item.diff
            diff_lines = diff_text.splitlines()

            change_texts: list[list[str]] = []

            # Split change blocks
            for line in diff_lines:
                if line.startswith('@@'):
                    change_texts.append([])

                change_texts[-1].append(line)

            # Parse change blocks
            for change_text in change_texts:
                changes.append(self.parse_change_block(diff_item.a_path, change_text))

        return changes
    
    def parse_log_commit(self, lines: list[str]):
        hash = lines[0].split(' ')[1]
        overlap = 0

        for line in lines:
            if line.startswith('@@'):
                words = line.split(' ')
                size_a = words[1].split(',')[1]
                size_b = words[2].split(',')[1]
                overlap += max(0, int(size_b) - int(size_a))

        return Commit(hash, overlap)
    
    def get_overlapping_commits(self, filename: str, range: Range):
        # when the commit only contains additions, the range is empty
        if range.empty():
            return []

        log = self.repo.git.log(f'-L {range.git_range()}:{filename}', '--patch')

        log_text = log.decode('utf-8', errors='replace') if isinstance(log, bytes) else log
        log_lines = log_text.splitlines()

        commit_texts: list[list[str]] = []

        # Split commits
        for line in log_lines:
            if line.startswith('commit '):
                commit_texts.append([])

            commit_texts[-1].append(line)

        commits: list[Commit] = []
        
        # Parse commits
        for commit_text in commit_texts:
            commits.append(self.parse_log_commit(commit_text))

        return commits
    
    def sort_and_merge_commits_by_overlap(self, commits: list[Commit]):
        commit_map: dict[str, int] = {}

        for commit in commits:
            if commit.hash not in commit_map:
                commit_map[commit.hash] = 0
            
            commit_map[commit.hash] += commit.overlap

        sorted_commits = [Commit(x[0], x[1]) for x in sorted(commit_map.items(), key=lambda x: x[1], reverse=True)]

        return sorted_commits

sim = CommitSimilarity('./')
changes = sim.get_changes()
commits = []
for change in changes:
    print(change)
    commits += sim.get_overlapping_commits(change.file, change.range_a)
sorted_commits = sim.sort_and_merge_commits_by_overlap(commits)
print(str(sorted_commits[0]) if len(sorted_commits) > 0 else 'No commits found')