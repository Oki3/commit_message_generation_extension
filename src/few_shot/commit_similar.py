from git import Repo, Commit as GitCommit

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
    author: str
    date: str
    message: str
    insertions: int
    deletions: int

    def __init__(self, hash: str, author: str, date: str, message: str, insertions: int = 0, deletions: int = 0):
        self.hash = hash
        self.author = author
        self.date = date
        self.message = message
        self.insertions = insertions
        self.deletions = deletions

    @property
    def short_hash(self):
        return self.hash[:7]

    def __str__(self):
        return f'{self.short_hash} ({self.message}) by {self.author}'
    
    @property
    def size(self):
        return self.insertions + self.deletions

class CommitOverlap:
    commit: Commit
    insertions: int
    deletions: int

    def __init__(self, commit: Commit, insertions: int = 0, deletions: int = 0):
        self.commit = commit
        self.insertions = insertions
        self.deletions = deletions

    def __str__(self):
        return f'{self.commit} overlaps {self.insertions} insertion(s) and {self.deletions} deletion(s)'
    
    @property
    def size(self):
        return self.insertions + self.deletions
    
class CommitScore:
    commit: Commit
    score: float

    def __init__(self, commit: Commit, score: float):
        self.commit = commit
        self.score = score

    def __str__(self):
        return f'{self.commit} with score {self.score}'

class SimilarCommitSearch:
    repo: Repo
    commits: dict[str, GitCommit]

    def __init__(self, path: str):
        self.repo = Repo(path)
        self.commits = {}

    def parse_diff_range(self, range_text: str):
        lines = range_text.replace('-', '').split(',')

        index = int(lines[0])
        num_changed = int(lines[1]) if len(lines) > 1 else 1

        return Range(index, index + max(0, num_changed - 1))
    
    def parse_change_block(self, file: str, lines: list[str]):
        range_texts = lines[0].split(' ')[1:3]
        range_a = self.parse_diff_range(range_texts[0])
        range_b = self.parse_diff_range(range_texts[1])

        text = lines[1:]

        return ChangeBlock(file, range_a, range_b, text)

    def get_changes(self, diff_from: GitCommit, diff_to: GitCommit|None = None, only_staged: bool = True):
        changes: list[ChangeBlock] = []

        if only_staged:
            index = diff_from.diff(diff_to, staged=True, create_patch=True, unified=0)
        else:
            index = diff_from.diff(diff_to, create_patch=True, unified=0)

        # Get exact diffs for changes that are staged but not committed, only for modified files
        for diff_item in index.iter_change_type("M"):
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
                changes.append(self.parse_change_block(diff_item.b_path, change_text))

        return changes
    
    def parse_log_commit(self, lines: list[str]):
        hash = lines[0].split(' ')[1].strip()
        author = lines[1].split(' ')[1].strip()
        date = lines[2].split(' ')[1].strip()
        insertions = 0
        deletions = 0

        message = ""
        in_message = True

        for line in lines[3:]:
            if in_message and line.startswith('diff --git'):
                in_message = False
            if in_message:
                message += line.strip() + ' '

            if line.startswith('-') and not line.startswith('--'):
                deletions += 1
            
            if line.startswith('+') and not line.startswith('++'):
                insertions += 1
        
        message = message.strip()

        commit = self.get__or_create_commit(hash, date, author, message)

        return CommitOverlap(commit, insertions, deletions)
    
    def get__or_create_commit(self, hash: str, date: str, author: str, message: str):
        if hash not in self.commits:
            commit = self.repo.commit(hash)
            
            insertions = commit.stats.total['insertions']
            deletions = commit.stats.total['deletions']

            self.commits[hash] = Commit(hash, date, author, message, insertions, deletions)
        
        return self.commits[hash]
    
    def get_commit_overlaps(self, filename: str, range: Range, diff_to: str):
        # when the commit only contains additions, the range is empty
        if range.empty():
            return []

        log = self.repo.git.log(f'-L {range.git_range()}:{filename}', '--patch', f"{diff_to}")

        log_text = log.decode('utf-8', errors='replace') if isinstance(log, bytes) else log
        log_lines = log_text.splitlines()

        commit_texts: list[list[str]] = []

        # Split commits
        for line in log_lines:
            if line.startswith('commit '):
                commit_texts.append([])

            commit_texts[-1].append(line)

        commit_overlaps: list[CommitOverlap] = []
        
        # Parse commits
        for commit_text in commit_texts:
            commit_overlap = self.parse_log_commit(commit_text)

            print(f"|> Found commit {commit_overlap.commit.short_hash} with {commit_overlap.insertions} insertions and {commit_overlap.deletions} deletions")
            commit_overlaps.append(commit_overlap)

        return commit_overlaps
    
    def sort_and_merge_commit_scores(self, commit_overlaps: list[CommitOverlap]) -> list[CommitScore]:
        commit_map: dict[str, CommitScore] = {}

        # Count the score for each commit, and keep track of the total size of the commit
        for commit_overlap in commit_overlaps:
            hash = commit_overlap.commit.hash

            if hash not in commit_map:
                commit_map[hash] = CommitScore(commit_overlap.commit, 0)
            
            commit_map[hash].score += commit_overlap.size
        
        # Divide the score by the total size of the commit
        for hash, commit_score in commit_map.items():
            commit_score.score = commit_score.score / commit_score.commit.size

        # Sort the commits by overlap
        sorted_commit_scores = []
        for hash, commit_score in sorted(commit_map.items(), key=lambda x: x[1].score, reverse=True):
            sorted_commit_scores.append(commit_score)

        return sorted_commit_scores
    
    def search(self, diff_from: str|None = None, diff_to: GitCommit|str|None = None, only_staged: bool = True) -> list[CommitScore]:
        if diff_to is not None and only_staged:
            raise ValueError('Cannot use both diff_to and only_staged options at the same time')
        
        diff_from = self.repo.index if diff_from is None else self.repo.commit(diff_from)
        diff_to = diff_to
        only_staged = only_staged

        changes = self.get_changes(diff_from, diff_to, only_staged)
        commit_overlaps = []

        for change in changes:
            print(f"Checking changes in {change.file} from line {change.range_a.start} to {change.range_a.end}")
            commit_overlaps += self.get_commit_overlaps(change.file, change.range_a, diff_to)
        
        return self.sort_and_merge_commit_scores(commit_overlaps)