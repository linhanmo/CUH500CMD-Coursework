import sys
import os

PARTICIPANTS = ["Li Wei", "Chen", "Mei", "Hua", "Jin", "Xiao Yu"]

FAMILY = {
    "Li Wei": {"Chen"},
    "Chen": {"Li Wei"},
    "Mei": {"Xiao Yu"},
    "Xiao Yu": {"Mei"},
    "Hua": set(),
    "Jin": set(),
}

LAST_YEAR = {
    "Li Wei": "Hua",
    "Chen": "Mei",
    "Mei": "Jin",
    "Hua": "Chen",
    "Jin": "Li Wei",
    "Xiao Yu": "Mei",
}


def is_reverse(giver, recipient):
    return LAST_YEAR.get(recipient) == giver


def is_valid_static(giver, recipient, used):
    # Check all rules
    if recipient == giver:
        return False
    if recipient in FAMILY.get(giver, set()):
        return False
    if LAST_YEAR.get(giver) == recipient:
        return False
    # Rule 4
    if LAST_YEAR.get(recipient) == giver:
        return False
    if recipient in used:
        return False
    return True


def init_domains(participants, used):
    domains = {}
    for giver in participants:
        dom = set()
        for recipient in participants:
            if is_valid_static(giver, recipient, used):
                dom.add(recipient)
        domains[giver] = dom
    return domains


def propagate(assignments, used, domains, flag):
    while True:
        # Check empty
        for giver, dom in domains.items():
            if len(dom) == 0:
                return None

        # Find a forced assignment
        forced_giver = None
        for giver, dom in domains.items():
            if len(dom) == 1:
                forced_giver = giver
                break

        if forced_giver is None:
            break

        recipient = next(iter(domains[forced_giver]))
        assignments[forced_giver] = recipient
        used.add(recipient)
        flag = flag or (not is_reverse(forced_giver, recipient))

        del domains[forced_giver]

        for g in domains:
            domains[g].discard(recipient)

    return assignments, used, domains, flag


def search(assignments, used, domains, flag):
    result = propagate(assignments, used, domains, flag)
    if result is None:
        return None
    assignments, used, domains, flag = result

    # Check global flag
    if not domains:
        if flag:
            return assignments
        else:
            return None

    # MRV
    giver = min(domains.keys(), key=lambda g: len(domains[g]))

    for recipient in list(domains[giver]):
        # Create copies
        new_assignments = assignments.copy()
        new_used = used.copy()
        new_domains = {g: set(d) for g, d in domains.items()}
        new_flag = flag or (not is_reverse(giver, recipient))

        new_assignments[giver] = recipient
        new_used.add(recipient)
        del new_domains[giver]
        for g in new_domains:
            new_domains[g].discard(recipient)

        # Recurse
        solution = search(new_assignments, new_used, new_domains, new_flag)
        if solution is not None:
            return solution

    return None


def validate_solution(assignments):
    if len(assignments) != len(PARTICIPANTS):
        return False
    recipients = set(assignments.values())
    if len(recipients) != len(PARTICIPANTS):
        return False
    for giver, recipient in assignments.items():
        if not is_valid_static(giver, recipient, set()):
            return False
    if all(is_reverse(g, r) for g, r in assignments.items()):
        return False
    return True


def main():
    assignments = {}
    used = set()
    domains = init_domains(PARTICIPANTS, used)
    flag = False

    solution = search(assignments, used, domains, flag)

    if solution is not None and validate_solution(solution):
        for giver in PARTICIPANTS:
            print(f"{giver} → {solution[giver]}")
    else:
        print("No valid Chinese New Year gift-exchange arrangement found.")


if __name__ == "__main__":
    main()
