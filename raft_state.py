class RaftState:

    def __init__(self):

        self.current_term = 0

        self.election_timeout = 0

        self.role = "FOLLOWER"

        self.voted_for = None

    def become_candidate(self):

        self.current_term += 1

        self.role = "CANDIDATE"

        self.voted_for = "self"

        print()

        print("=" * 35)

        print(
            f"Current Term = "
            f"{self.current_term}"
        )

        print(
            "Role -> Candidate"
        )

        print(
            "Vote from self"
        )

        print("=" * 35)

    def become_leader(self):

        self.role = "LEADER"

        self.voted_for = None

        print()

        print("=" * 35)

        print(
            f"Term {self.current_term}"
        )

        print(
            "Role -> LEADER"
        )

        print("=" * 35)

    def become_follower(self):

        self.role = "Follower"

        self.voted_for = None

        print(

            f"Role -> FOLLOWER "
            f"(Term {self.current_term})"

        )

    def vote(self, term):

        if term < self.current_term:
            return "NO"

        if (
            self.voted_for is None
            or self.voted_for == "self"
        ):

            self.current_term = term

            self.voted_for = "candidate"

            return "YES"

        return "NO"

    def set_timeout(self, timeout):

        self.election_timeout = timeout

    def get_timeout(self):

        return self.election_timeout

    def get_term(self):

        return self.current_term

    def set_term(self, term):

        if term > self.current_term:

            self.current_term = term

    def get_role(self):

        return self.role


raft_state = RaftState()