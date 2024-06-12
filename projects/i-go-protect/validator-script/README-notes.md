# Validator script


## Functionality

### Configuration

### Contract maintenance

#### Generate and deposit keys
- Generate partkey on the node.
- Deposit the partkey to the delegator contract.

#### Delete unconfirmed keys and delegator contracts
- Delete partkeys.
- Delete delegator contract.

#### Delete expired delegator contracts
- Delete expired contracts (try deleting partkeys).

#### Delete keys of withdrawn contracts
- Delete partkeys wihtout for the delegators who's contracts were withdrawn (deleted).
This point requires managing the state of the validator locally, hence will require storing the state in a local file(?) to use as a starting point upon re-running the script.


## To-Do

### Delegator contract breached

1. Check if breached
2. Take non-deletion action
3. Delete contract


### Delegator contract withdrawn

1. Check if each partkey has a delegator contract associated with the validator app.
2. Delete the keys that do not have a contract counterpart.

