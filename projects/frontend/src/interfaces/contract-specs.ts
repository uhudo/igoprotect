export interface ValConfigMan {
  /** ----- Mandatory information of validator ad ----- */
  /** Number denoting the category of hardware */
  hwCat: bigint
  /** Minimum amount that user must keep in one’s account */
  minAmt: bigint
  /** Maximum amount that user can keep in one’s account */
  maxAmt: bigint
  /** Fee charged for setting up the node (i.e. generating keys) */
  feeSetup: bigint
  /** Fee charged for operation per round */
  feeRound: bigint
  /** Deposit made by user to Noticeboard */
  deposit: bigint
  /** Maximum number of rounds the validator promises to respond to generate the keys for the user */
  setupRounds: bigint
  /** Maximum number of round the validator is willing to wait for user to confirm the generated keys */
  confirmationRounds: bigint
  /** Maximum number of contract breaches allowed */
  maxBreach: bigint
  /** Minimum number of rounds between two contract breaches to consider them separate events */
  breachRounds: bigint
  /** Guaranteed uptime for the node by the validator (0-1) */
  uptimeGar: bigint
}

export interface ValConfigExtra {
  /** ----- Extra information of validator ad ----- */
  /** Name of validator */
  name: string
  /** Link to more info about valdiator */
  link: string
}

export interface ValidatorAd {
  /** ----- All information of validator ad ----- */
  /** App ID */
  appId: bigint
  delCnt: bigint
  live: boolean
  manager: string
  maxDelCnt: bigint
  noticeboardAppId: bigint
  owner: string
  deposit: bigint | undefined
  earnFactor: bigint | undefined
  earnings: bigint
  valConfigMan: ValConfigMan
  valConfigExtra: ValConfigExtra
  delegators: (DelegatorContractInfo | undefined)[]
}

export interface DelegatorContractInfo {
  appId: bigint
  /** Marks whether contract has been breaches (sufficient number of times) */
  contractBreached: boolean
  /** Address of the delegator account */
  delAcc: string | undefined
  /** Whether the user has signed the generated keys */
  keysConfirmed: boolean
  /** Round number of last breach */
  lastBreachRound: bigint
  /** App ID of noticeboard */
  noticeboardAppId: bigint
  /** Current number of contract breaches (must be smaller or equal to maxBreach) */
  numBreach: bigint
  /** Marks whether keys have been deposited */
  partKeysDeposited: boolean
  /** Last round that the contract is valid */
  roundEnd: bigint
  /** First round that the contract is valid */
  roundStart: bigint
  /** Selection key generated for the user */
  selKey: Uint8Array | undefined //bytes[32]
  /** State proof key dilution generated for the user */
  stateProofKey: Uint8Array | undefined //bytes[64]
  /** App ID of validator ad contract */
  valAppId: bigint
  /** Mandatory part of configuration of validator ad contract at time of delegator contract conclusion */
  valConfigMan: ValConfigMan | undefined
  /** Extra part of configuration of validator ad contract at time of delegator contract conclusion */
  valConfigExtra: ValConfigExtra | undefined
  /** Vote key generated for the user */
  voteKey: Uint8Array | undefined //bytes[32]
  /** Vote key dilution generated for the user */
  voteKeyDilution: bigint | undefined
}

export interface NoticeboardInfo {
  blockedAmt: bigint
  depositDelMin: bigint
  depositValMin: bigint
  manager: string
  valEarnFactor: bigint
  valFactoryAppId: bigint
}
