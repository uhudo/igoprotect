import { DelegatorContractInfo, ValConfigExtra, ValConfigMan, ValidatorAd } from '../interfaces/contract-specs'
import { noticeboardAppID } from '../noticeboardAppID'
import { UserProfile } from '../types/types'

export const MBR_VALIDATOR_AD_CREATION = 899_500
export const MBR_BOX_VAL_LIST_CREATION = 325_700
export const MBR_DELEGATOR_CONTRACT_CREATION = 785_000
export const MBR_VALIDATOR_AD_INIT = 100_000
export const DEFAULT_DELEGATOR_CONTRACT_DURATION = 1000

export const START_ROUND_IN_FUTURE = 20

export const DEL_MIN_AMT = 30_000
export const DEL_MAX_AMT = 100_000
export const FEE_SETUP = 1_000
export const FEE_ROUND = 100
export const MIN_DEL_DEPOSIT = 110_000
export const MIN_VAL_DEPOSIT = 400_000
export const SETUP_ROUNDS = 100
export const CONFIRMATION_ROUNDS = 100
export const MAX_BREACH = 3
export const BREACH_ROUNDS = 100
export const MAX_NAME_LENGTH = 30
export const MAX_LINK_LENGTH = 70
export const MIN_STAKE_RANGE = 999n
export const MAX_DEL_CNT = 4

export const DEFAULT_VAL_CONFIG_MAN: ValConfigMan = {
  hwCat: BigInt(0),
  minAmt: BigInt(DEL_MIN_AMT),
  maxAmt: BigInt(DEL_MAX_AMT),
  feeSetup: BigInt(FEE_SETUP),
  feeRound: BigInt(FEE_ROUND),
  deposit: BigInt(MIN_DEL_DEPOSIT),
  setupRounds: BigInt(SETUP_ROUNDS),
  confirmationRounds: BigInt(CONFIRMATION_ROUNDS),
  maxBreach: BigInt(MAX_BREACH),
  breachRounds: BigInt(BREACH_ROUNDS),
  uptimeGar: BigInt(0),
}
export const DEFAULT_VAL_CONFIG_EXTRA: ValConfigExtra = {
  name: 'Your name or pseudonym',
  link: 'Link to more info about you and your validator skills.',
}

export const DEFAULT_VALIDATOR_AD: ValidatorAd = {
  appId: BigInt(0),
  delCnt: BigInt(0),
  live: false,
  manager: 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ',
  maxDelCnt: BigInt(MAX_DEL_CNT),
  noticeboardAppId: BigInt(noticeboardAppID),
  owner: 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ',
  deposit: undefined,
  earnFactor: undefined,
  earnings: BigInt(0),
  valConfigMan: DEFAULT_VAL_CONFIG_MAN,
  valConfigExtra: DEFAULT_VAL_CONFIG_EXTRA,
  delegators: [],
}

export const UNDEFINED_DELEGATOR_CONTRACT_INFO: DelegatorContractInfo = {
  appId: 0n,
  contractBreached: false,
  delAcc: undefined,
  keysConfirmed: false,
  lastBreachRound: 0n,
  noticeboardAppId: 0n,
  numBreach: 0n,
  partKeysDeposited: false,
  roundEnd: 0n,
  roundStart: 0n,
  selKey: undefined,
  stateProofKey: undefined,
  valAppId: 0n,
  valConfigMan: undefined,
  valConfigExtra: undefined,
  voteKey: undefined,
  voteKeyDilution: 0n,
}

export const DEFULAT_USER_PROFILE: UserProfile = {
  validator: undefined,
  new_user: undefined,
  valAppId: undefined,
  delAppId: undefined,
}
