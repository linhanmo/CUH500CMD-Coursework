# ASSESSED STANDARD TASK 1: Chinese New Year Gift-Exchange — Recursive Matching Assignment

A group of friends is organising a Chinese New Year gift-exchange using a simple draw-a-name system.
Everyone will secretly give a gift to one other person, but the group has agreed on a few rules to keep things fair.

You are given the list of participants:

- Li Wei
- Chen
- Mei
- Hua
- Jin
- Xiao Yu

## The gift-exchange must follow these rules

- 🔴 No one can give a gift to themselves.
- 🔴 Close family members cannot give to each other.

### The family pairs are

- Li Wei ↔ Chen
- Mei ↔ Xiao Yu

- 🔴 No one can give to the same person they gave to last year.

### Last year's assignments were

| Giver | Recipient |
|---|---|
| Li Wei | Hua |
| Chen | Mei |
| Mei | Jin |
| Hua | Chen |
| Jin | Li Wei |
| Xiao Yu | Mei |

- 🔴 Each recipient can only be assigned once.

## Your task

Write a recursive backtracking function that attempts to assign each participant a valid recipient by:

- ⭕ checking all rules for each possible recipient
- ⭕ assigning a recipient if valid
- ⭕ recursively moving to the next participant
- ⭕ backtracking if a later assignment becomes impossible
- ⭕ Ensuring if a participant has only one valid possible recipient left, that assignment must be forced immediately (dynamic constraint propagation).
- ⭕ Ensuring that at least one assignment must differ in direction from last year's cycle (to avoid simply rotating the same loop).

If a complete valid assignment is found, print the final gift-exchange list in the format:

```text
Li Wei → ?
Chen → ?
Mei → ?
Hua → ?
Jin → ?
Xiao Yu → ?
```

If no valid arrangement exists, print:

```text
No valid Chinese New Year gift-exchange arrangement found.
```

## Chinese New Year Gift-Exchange: Recursive Backtracking Pseudocode

```text
FUNCTION assignGifts(participants, familyPairs, lastYear, assignments, usedRecipients, index, globalFlag):

    IF index == length(participants):
        // globalFlag tracks whether at least one assignment is NOT just the reverse of last year's pairing
        RETURN globalFlag == True

    giver = participants[index]

    // Build a list of all possible recipients
    possibleRecipients = EMPTY LIST

    FOR each recipient IN participants:

        // Rule 1: cannot give to themselves
        IF recipient == giver:
            CONTINUE

        // Rule 2: cannot give to close family member
        IF familyPairs[giver] == recipient:
            CONTINUE

        // Rule 3: cannot repeat last year's recipient
        IF lastYear[giver] == recipient:
            CONTINUE

        // NEW Rule 4: cannot give to someone who gave to them last year
        IF lastYear[recipient] == giver:
            CONTINUE

        // Rule 5: recipient must not already be chosen
        IF recipient IN usedRecipients:
            CONTINUE

        ADD recipient TO possibleRecipients

    END FOR

    // Forced-choice pruning
    IF length(possibleRecipients) == 1:
        forcedRecipient = possibleRecipients[0]

        assignments[giver] = forcedRecipient
        add forcedRecipient to usedRecipients

        // Update globalFlag if this assignment reverses last year's direction
        newFlag = globalFlag OR (lastYear[forcedRecipient] != giver)

        IF assignGifts(participants, familyPairs, lastYear, assignments, usedRecipients, index + 1, newFlag):
            RETURN True

        // Backtrack
        remove forcedRecipient from usedRecipients
        assignments[giver] = NONE
        RETURN False

    // Otherwise try all possible recipients
    FOR each recipient IN possibleRecipients:

        assignments[giver] = recipient
        add recipient to usedRecipients

        newFlag = globalFlag OR (lastYear[recipient] != giver)

        IF assignGifts(participants, familyPairs, lastYear, assignments, usedRecipients, index + 1, newFlag):
            RETURN True

        // Backtrack
        remove recipient from usedRecipients
        assignments[giver] = NONE

    END FOR

    RETURN False
```

## Additional feature requirement

You should also add an additional feature that improves the approach by **changing the structure of the search itself**, not merely adding another rule; in other words, you must extend the recursive backtracking engine in a meaningful way. You may include your own idea, but you might consider the following:

- ⭕ **Dynamic participant ordering** that chooses the next giver with the smallest remaining set of valid recipients to reduce branching early.
- ⭕ **Forward-checking domain pruning** that updates all remaining participants' possible recipients after each assignment and backtracks immediately if any domain becomes empty.
- ⭕ **Symmetry-breaking ordering** that imposes a global ordering rule that prevents exploring equivalent permutations of the same cycle.
- ⭕ **Multi-solution exploration mode** that allows the algorithm to continue searching after the first solution and use earlier solutions to prune structurally similar branches.
