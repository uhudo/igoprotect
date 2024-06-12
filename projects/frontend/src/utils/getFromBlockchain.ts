import { ABIAddressType } from 'algosdk'
import AlgodClient from 'algosdk/dist/types/client/v2/algod/algod'
import { DelegatorContractClient } from '../contracts/DelegatorContract'
import { GeneralValidatorAdClient } from '../contracts/GeneralValidatorAd'
import { NoticeboardClient } from '../contracts/Noticeboard'
import { DelegatorContractInfo, NoticeboardInfo, ValidatorAd } from '../interfaces/contract-specs'
import { NoticeboardApp, UserProfile } from '../types/types'
import { decodeUint64List, decodeValConfigExtra, decodeValConfigMan } from './decodeFunctions'

// Fetches info from blockchain about noticeboard
export const getNoticeboardInfo = async (noticeboardClient: NoticeboardClient): Promise<NoticeboardInfo | undefined> => {
  try {
    const globalState = await noticeboardClient.getGlobalState()

    return {
      blockedAmt: globalState.blockedAmt!.asBigInt(),
      depositDelMin: globalState.depositDelMin!.asBigInt(),
      depositValMin: globalState.depositValMin!.asBigInt(),
      manager: new ABIAddressType().decode(globalState.manager!.asByteArray()),
      valEarnFactor: globalState.valEarnFactor!.asBigInt(),
      valFactoryAppId: globalState.valEarnFactor!.asBigInt(),
    }
  } catch (err) {
    console.error('Could not get info of noticeboard. %s', err)
    return undefined
  }
}

export const getValidatorIDs = async (algodClient: AlgodClient, noticeboardAppID: bigint): Promise<bigint[]> => {
  try {
    const boxContent = await algodClient.getApplicationBoxByName(Number(noticeboardAppID), new TextEncoder().encode('val_list')).do()

    const valListAll = decodeUint64List(boxContent.value)

    const valList = valListAll.filter((item) => item !== 0n)

    return valList
  } catch (err) {
    console.error("Could not get validators' app IDs: ", err)

    return []
  }
}

// Fetches info from blockchain for a validator
export const getValidatorAd = async (algodClient: AlgodClient, valAppID: bigint): Promise<ValidatorAd | undefined> => {
  try {
    const valClient = new GeneralValidatorAdClient(
      {
        resolveBy: 'id',
        id: valAppID,
      },
      algodClient,
    )

    const globalState = await valClient.getGlobalState()
    const valConfigMan = decodeValConfigMan(globalState.valConfigMan!.asByteArray())
    const valConfigExtra = decodeValConfigExtra(globalState.valConfigExtra!.asByteArray())

    // Get all its delegators
    const delegators = await getAllDelegatorsInfo(algodClient, valAppID)

    return {
      appId: valAppID,
      delCnt: globalState.delCnt!.asBigInt(),
      live: Boolean(globalState.live!.asBigInt()),
      manager: new ABIAddressType().decode(globalState.manager!.asByteArray()),
      maxDelCnt: globalState.maxDelCnt!.asBigInt(),
      noticeboardAppId: globalState.delCnt!.asBigInt(),
      owner: new ABIAddressType().decode(globalState.owner!.asByteArray()),
      deposit: globalState.valDeposit!.asBigInt(),
      earnFactor: globalState.valEarnFactor!.asBigInt(),
      earnings: globalState.valEarnings!.asBigInt(),
      valConfigMan: valConfigMan,
      valConfigExtra: valConfigExtra,
      delegators: delegators,
    }
  } catch (err) {
    console.error('Could not get info of validator with app ID: %d. %s', valAppID, err)
    return undefined
  }
}

export const getDelegatorIDs = async (algodClient: AlgodClient, valAppID: bigint): Promise<bigint[]> => {
  try {
    const valClient = new GeneralValidatorAdClient(
      {
        resolveBy: 'id',
        id: valAppID,
      },
      algodClient,
    )

    const globalState = await valClient.getGlobalState()
    const delListAll = decodeUint64List(globalState.delContracts!.asByteArray())

    const delList = delListAll.filter((item) => item !== 0n)

    return delList
  } catch (err) {
    console.error("Could not get delegators' app IDs: ", err)

    return []
  }
}

// Fetches info from blockchain for a validator
export const getDelegatorContractInfo = async (algodClient: AlgodClient, delAppID: bigint): Promise<DelegatorContractInfo | undefined> => {
  try {
    const delClient = new DelegatorContractClient(
      {
        resolveBy: 'id',
        id: delAppID,
      },
      algodClient,
    )

    const globalState = await delClient.getGlobalState()
    const valConfigMan = decodeValConfigMan(globalState.valConfigMan!.asByteArray())
    const valConfigExtra = decodeValConfigExtra(globalState.valConfigExtra!.asByteArray())
    // const selKey = decodeStaticByteArray2String(globalState.selKey!.asByteArray(), 32)
    // const voteKey = decodeStaticByteArray2String(globalState.voteKey!.asByteArray(), 32)
    // const stateProofKey = decodeStaticByteArray2String(globalState.stateProofKey!.asByteArray(), 64)

    const selKey = globalState.selKey!.asByteArray()
    const voteKey = globalState.voteKey!.asByteArray()
    const stateProofKey = globalState.stateProofKey!.asByteArray()

    return {
      appId: delAppID,

      contractBreached: Boolean(globalState.contractBreached!.asBigInt()),
      delAcc: new ABIAddressType().decode(globalState.delAcc!.asByteArray()),
      keysConfirmed: Boolean(globalState.keysConfirmed!.asBigInt()),
      lastBreachRound: globalState.lastBreachRound!.asBigInt(),
      noticeboardAppId: globalState.noticeboardAppId!.asBigInt(),
      numBreach: globalState.numBreach!.asBigInt(),
      partKeysDeposited: Boolean(globalState.partKeysDeposited!.asBigInt()),
      roundEnd: globalState.roundEnd!.asBigInt(),
      roundStart: globalState.roundStart!.asBigInt(),
      selKey: selKey,
      stateProofKey: stateProofKey,
      valAppId: globalState.valAppId!.asBigInt(),
      valConfigMan: valConfigMan,
      valConfigExtra: valConfigExtra,
      voteKey: voteKey,
      voteKeyDilution: globalState.voteKeyDilution!.asBigInt(),
    }
  } catch (err) {
    console.error('Could not get info of delegator with app ID %d. %s', delAppID, err)
    return undefined
  }
}

export const getAllDelegatorsInfo = async (algodClient: AlgodClient, valAppID: bigint): Promise<(DelegatorContractInfo | undefined)[]> => {
  try {
    if (!valAppID) {
      // Contract does not exist, thus there are no delegators yet.
      return []
    }

    const fetchedDelegatorList = await getDelegatorIDs(algodClient, valAppID)

    const fetchedDelegators = await Promise.all(
      fetchedDelegatorList.map(async (delegatorId) => {
        try {
          const delInfo = await getDelegatorContractInfo(algodClient, delegatorId)
          return delInfo
        } catch (error) {
          console.error(`Failed to fetch info for delegator ID ${delegatorId}:`, error)
          return undefined
        }
      }),
    )

    return fetchedDelegators
  } catch (error) {
    console.error('Failed to fetch delegators:', error)
    return []
  }
}

// Fetches info from blockchain for a validator
export const checkUserOptedInApp = async (algodClient: AlgodClient, address: string, appId: number): Promise<boolean> => {
  if (!address) {
    return false
  }

  try {
    const accountInfo = await algodClient.accountInformation(address).do()
    return accountInfo['apps-local-state'].some((app: { id: number }) => app.id === appId)
  } catch (err) {
    console.log('Account %s is not yet opted-in with app ID %d. %s', address, appId, err)
    return false
  }
}

interface configUserProfileFromAddressInterface {
  address: string
  userProfile: UserProfile
  setUserProfile: React.Dispatch<React.SetStateAction<UserProfile>>
  algodClient: AlgodClient
  noticeboardApp: NoticeboardApp
}

export const configUserProfileFromAddress = async ({
  address,
  noticeboardApp,
  algodClient,
  userProfile,
  setUserProfile,
}: configUserProfileFromAddressInterface): Promise<void> => {
  try {
    const userOptedIn = await checkUserOptedInApp(algodClient, address, noticeboardApp.appId)

    if (userOptedIn) {
      const localState = noticeboardApp.client.getLocalState(address)
      const delAppId = (await localState).delAppId?.asBigInt()
      const valAppId = (await localState).valAppId?.asBigInt()

      console.log('User is opted-in the noticeboard with delegator App ID: %d and validator App ID: %d', delAppId, valAppId)

      if (delAppId === 0n && valAppId === 0n) {
        // New user
        setUserProfile({ ...userProfile, new_user: true, validator: undefined, delAppId: undefined, valAppId: undefined })
      } else if (delAppId !== 0n && valAppId !== 0n) {
        // Existing delegator
        setUserProfile({ ...userProfile, new_user: false, validator: false, delAppId: delAppId, valAppId: valAppId })
      } else if (delAppId === 0n && valAppId !== 0n) {
        // Existing validator
        setUserProfile({ ...userProfile, new_user: false, validator: true, delAppId: delAppId, valAppId: valAppId })
      }
    } else {
      console.log('User is not opted-in the noticeboard')
      setUserProfile({ ...userProfile, new_user: true, validator: undefined, delAppId: undefined, valAppId: undefined })
    }
  } catch (e) {
    console.error('Could not config user profile based on address: %s', e)
  }
}
