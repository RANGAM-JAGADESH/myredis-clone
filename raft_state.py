class RaftState:

    def __init__(self):

        self.current_term = 0

        self.role = "Follower"

        self.voted_for = None

    def become_candidate(self):

        self.current_term += 1

        self.role = "Candidate"

        self.voted_for = "self"

        print(
            f"Term {self.current_term}"
        )

        print(
            "Role -> Candidate"
        )

        print(
            "Voted for self"
        )

def get_term(self):

    return self.current_term

def get_role(self):

    return self.role

raft_state = RaftState()
