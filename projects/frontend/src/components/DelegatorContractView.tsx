import { useEffect, useState } from 'react'

import { getApplicationAddress, makeKeyRegistrationTxnWithSuggestedParamsFromObject } from 'algosdk'
import _ from 'lodash'
import { useSnackbar } from 'notistack'
import { Link, useParams } from 'react-router-dom'

import { microAlgos } from '@algorandfoundation/algokit-utils'
import { useWallet } from '@txnlab/use-wallet'

import { DelegatorContractInfo } from '../interfaces/contract-specs'
import { useGlobalState } from '../providers/GlobalStateProvider'
import { START_ROUND_IN_FUTURE, UNDEFINED_DELEGATOR_CONTRACT_INFO } from '../utils/constants'
import { ellipseAddress } from '../utils/ellipseAddress'
import { getDelegatorContractInfo } from '../utils/getFromBlockchain'
import ConfirmWithdrawal from './ConfirmWithdrawal'
import DelegatorContractTemplate from './DelegatorContractTemplate'
import WebsiteHeader from './WebsiteHeader'

const renderButton = (text: string, onClick: () => void, disabled: boolean = false, additionalClasses: string = '') => (
  <button className={`btn ${disabled ? 'btn-disabled' : ''} ${additionalClasses}`} onClick={onClick} disabled={disabled}>
    {text}
  </button>
)

const renderLoadingButton = (
  text: string,
  onClick: () => Promise<void>,
  disabled: boolean = false,
  additionalClasses: string = '',
  loading: boolean = false,
) => (
  <button className={`btn text-xl ${disabled ? 'btn-disabled' : ''} ${additionalClasses}`} onClick={onClick} disabled={disabled}>
    {loading ? <span className="loading loading-spinner" /> : text}
  </button>
)

const CONTRACT_ENDED = 'Ending contract'
const CONTRACT_LIVE = 'live'
const WAITING_DEPOSIT_KEYS = 'deposit-keys'
const WAITING_CONFIRM_KEYS = 'Confirming setup'
const KEYS_NOT_GENERATED = 'Refunding'

interface DelegatorContractViewProps {
  user: boolean
  new_contract: boolean
}

const DelegatorContractView: React.FC<DelegatorContractViewProps> = ({ user, new_contract }) => {
  const { delegatorContractAppID } = useParams()
  const { userProfile, setUserProfile, noticeboardApp, algorandClient } = useGlobalState()
  const [delegatorContractInfo, setDelegatorContractInfo] = useState<DelegatorContractInfo>(UNDEFINED_DELEGATOR_CONTRACT_INFO)
  const [contractExists, setContractExists] = useState<boolean>(false)
  const [openWithdrawModal, setOpenWithdrawModal] = useState<boolean>(false)
  const [currentRound, setCurrentRound] = useState<bigint>(0n)
  const [loading, setLoading] = useState<boolean>(true)
  const [contractStatusTxt, setContractStatusTxt] = useState<string>('N/A')
  const [contractStatus, setContractStatus] = useState<string | undefined>(undefined)
  const [contractOwner, setContractOwner] = useState<boolean>(false)
  const { enqueueSnackbar } = useSnackbar()
  const { signer, activeAddress } = useWallet()
  const [loadingButton, setLoadingButton] = useState<boolean>(false)

  const algodClient = algorandClient.client.algod

  const [openDelegatorContract, setOpenDelegatorContract] = useState<boolean>(false)

  const toggleModal = (setModalState: React.Dispatch<React.SetStateAction<boolean>>) => () => {
    setModalState((prev) => !prev)
  }

  const executeAction = async () => {
    if (!signer || !activeAddress) {
      enqueueSnackbar('Please connect wallet first', { variant: 'warning' })
      return
    }

    if (contractStatus) {
      setLoadingButton(true)
      try {
        const sP = await algodClient.getTransactionParams().do()

        let result = undefined
        enqueueSnackbar(`${contractStatus} ...`, { variant: 'info' })
        switch (contractStatus) {
          case CONTRACT_ENDED: {
            result = await noticeboardApp.client.endExpiredOrBreachedDelegatorContract(
              {
                delAcc: activeAddress,
              },
              {
                sender: {
                  addr: activeAddress,
                  signer: signer,
                },
                apps: [Number(userProfile.valAppId!), Number(userProfile.delAppId!)],
                sendParams: { fee: microAlgos(3 * sP.minFee) },
              },
            )

            // If contract end was successful, change userProfile
            setUserProfile({ ...userProfile, new_user: true, validator: undefined, delAppId: undefined, valAppId: undefined })

            break
          }
          case KEYS_NOT_GENERATED: {
            result = await noticeboardApp.client.keysNotGenerated(
              {
                delAcc: activeAddress,
              },
              {
                sender: {
                  addr: activeAddress,
                  signer: signer,
                },
                apps: [Number(userProfile.valAppId!), Number(userProfile.delAppId!)],
                accounts: [activeAddress],
                sendParams: { fee: microAlgos(4 * sP.minFee) },
              },
            )

            break
          }
          case WAITING_CONFIRM_KEYS: {
            const noticeboardAppAddress = getApplicationAddress(noticeboardApp.appId)
            const feeOperation =
              delegatorContractInfo.valConfigMan!.feeRound * (delegatorContractInfo.roundEnd - delegatorContractInfo.roundStart)

            const voteKey = delegatorContractInfo.voteKey!
            const selKey = delegatorContractInfo.selKey!
            const stateProofKey = delegatorContractInfo.stateProofKey!
            // Create key deregistration transaction
            const keyRegTxn = makeKeyRegistrationTxnWithSuggestedParamsFromObject({
              from: activeAddress,
              note: new Uint8Array(Buffer.from('', 'utf-8')),
              voteKey: voteKey,
              selectionKey: selKey,
              voteFirst: Number(delegatorContractInfo.roundStart),
              voteLast: Number(delegatorContractInfo.roundEnd),
              voteKeyDilution: Number(delegatorContractInfo.voteKeyDilution),
              stateProofKey: stateProofKey,
              suggestedParams: sP,
            })

            const feeOperationPaymentTxn = await algorandClient.transactions.payment({
              sender: activeAddress,
              receiver: noticeboardAppAddress,
              amount: microAlgos(Number(feeOperation)),
              extraFee: microAlgos(4 * sP.minFee),
              signer: signer,
            })

            result = await noticeboardApp.client
              .compose()
              .addTransaction({ txn: keyRegTxn, signer: signer })
              .confirmKeys(
                {
                  keyregTxnIndex: 0,
                  feeOperationPayment: feeOperationPaymentTxn,
                },
                {
                  sender: {
                    addr: activeAddress,
                    signer: signer,
                  },
                  apps: [Number(userProfile.valAppId!), Number(userProfile.delAppId!)],
                },
              )
              .execute()
            break
          }
        }

        enqueueSnackbar(`Transaction sent: ${result!.transactions[0].txID()}`, { variant: 'success' })
        updateDelegatorContract()
      } catch (err) {
        enqueueSnackbar(`Failed to ${contractStatus.toLowerCase()}. ${err}`, { variant: 'info' })
        console.error(`Failed to ${contractStatus.toLowerCase()}: %s`, err)
      }
      setLoadingButton(false)
    }
  }

  useEffect(() => {
    setContractOwner(userProfile.delAppId === BigInt(delegatorContractAppID!))
  }, [userProfile, delegatorContractAppID])

  const fetchDelegator = async () => {
    setLoading(true)

    try {
      // Check that delegatorContractAppID is unsigned int
      if (
        !delegatorContractAppID ||
        isNaN(Number(delegatorContractAppID)) ||
        Number(delegatorContractAppID) < 0 ||
        !Number.isInteger(Number(delegatorContractAppID))
      ) {
        setContractExists(false)
        return
      }

      if (BigInt(delegatorContractAppID) === 0n) {
        // setDelegatorContractInfo(DEFAULT_VALIDATOR_AD)
        setContractExists(false)
        return
      }

      // Get info about the delegator contract
      const delInfo = await getDelegatorContractInfo(algorandClient.client.algod, BigInt(delegatorContractAppID))

      if (delInfo) {
        // Fail if not part of noticeboard
        if (delInfo!.noticeboardAppId !== BigInt(noticeboardApp.appId)) {
          console.error(`Delegator ID ${delegatorContractAppID} is not part of IgoProtect ${noticeboardApp.appId}`)
          setContractExists(false)
          return
        }

        // Store selected delegator contract info
        setDelegatorContractInfo(delInfo)
        setContractExists(true)
      } else {
        setContractExists(false)
      }
    } catch (error) {
      console.error('Failed to fetch delegator: %s', delegatorContractAppID, error)
      setContractExists(false)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDelegator()
  }, [delegatorContractAppID, algorandClient, noticeboardApp.appId])

  // Periodically fetch delegator contract to detect changes
  const updateDelegatorContract = async () => {
    console.log('Trying to fetch update of delegator contract.')
    // Execute only if current delegator contract info isn't default
    if (!_.isEqual(delegatorContractInfo, UNDEFINED_DELEGATOR_CONTRACT_INFO)) {
      try {
        // Fetch info about the delegator contract
        const delInfo = await getDelegatorContractInfo(algorandClient.client.algod, delegatorContractInfo.appId)

        if (delInfo) {
          // Check if new info is different from current
          if (!_.isEqual(delegatorContractInfo, delInfo)) {
            // Store updated current delegator contract info
            setDelegatorContractInfo(delInfo)

            console.log('There is new information about delegator contract.')
          }
        }

        // Fetch also current round info
        const algodStatus = await algorandClient.client.algod.status().do()
        const cRound = BigInt(algodStatus['last-round'])

        setCurrentRound(cRound)
        updateContractStatus()
      } catch (error) {
        console.error('Failed to update delegator contract info: %s', delegatorContractAppID, error)
      }
    }
  }

  useEffect(() => {
    updateDelegatorContract()
  }, [])

  useEffect(() => {
    // Set up the interval to call updateDelegatorContract every x/2*3_000 milliseconds = x/2 rounds
    const intervalId = setInterval(updateDelegatorContract, Number((3_000 * START_ROUND_IN_FUTURE) / 2))

    // Clean up the interval when the component is unmounted
    return () => clearInterval(intervalId)
  }, [delegatorContractInfo])

  const updateContractStatus = () => {
    //Define status of delegator contract
    let keysNeedToBeConfirmedByRound = 2n ** 64n
    let keysNeedToBeGenerated = 0n
    if (delegatorContractInfo && delegatorContractInfo.valConfigMan) {
      keysNeedToBeConfirmedByRound =
        delegatorContractInfo.roundStart +
        delegatorContractInfo.valConfigMan!.confirmationRounds +
        delegatorContractInfo.valConfigMan!.setupRounds

      keysNeedToBeGenerated = delegatorContractInfo.roundStart + delegatorContractInfo.valConfigMan!.setupRounds
    }

    let newContractValue

    if (delegatorContractInfo) {
      if (delegatorContractInfo.partKeysDeposited) {
        if (delegatorContractInfo.keysConfirmed) {
          if (currentRound >= delegatorContractInfo.roundEnd) {
            newContractValue = CONTRACT_ENDED
          } else {
            newContractValue = CONTRACT_LIVE
          }
        } else {
          newContractValue = WAITING_CONFIRM_KEYS
        }
      } else {
        if (currentRound >= keysNeedToBeGenerated) {
          newContractValue = KEYS_NOT_GENERATED
        } else {
          newContractValue = WAITING_DEPOSIT_KEYS
        }
      }
    } else {
      newContractValue = undefined
    }
    setContractStatus(newContractValue)

    updateContractStatusText(newContractValue, keysNeedToBeConfirmedByRound, keysNeedToBeGenerated)
  }

  // // For testing
  // setContractStatus(WAITING_CONFIRM_KEYS)
  const updateContractStatusText = (
    newContractValue: string | undefined,
    keysNeedToBeConfirmedByRound: bigint,
    keysNeedToBeGenerated: bigint,
  ) => {
    let txt = ''
    switch (newContractValue) {
      case CONTRACT_ENDED: {
        txt = 'Contract has expired. Please end the contract.'
        break
      }
      case CONTRACT_LIVE: {
        txt = 'Contract is live.'
        break
      }
      case WAITING_DEPOSIT_KEYS: {
        txt = `Waiting for validator to setup the system at the latest by round ${keysNeedToBeGenerated}.`
        break
      }
      case WAITING_CONFIRM_KEYS: {
        if (contractOwner) {
          txt = `You must confirm the setup at the latest by round ${keysNeedToBeConfirmedByRound}!`
        } else {
          txt = `Waiting for delegator to confirm the generated setup by round ${keysNeedToBeConfirmedByRound}.`
        }
        break
      }
      case KEYS_NOT_GENERATED: {
        if (contractOwner) {
          txt = 'Validator did not setup the system for you in the promised time. You can initiate a full refund.'
        } else {
          txt = 'Validator did not setup the system in time.'
        }
        break
      }
      default: {
        txt = 'Error - contract undefined.'
        break
      }
    }
    setContractStatusTxt(txt)
  }

  useEffect(() => {
    updateContractStatus()
  }, [delegatorContractInfo, currentRound, contractOwner])

  if (loading) {
    return (
      <div className="main-website">
        <WebsiteHeader />
        <div className="main-body">
          <h1 className="text-xl font-bold">Loading delegator contract with ID '{delegatorContractAppID}'</h1>
          <button className="loading loading-spinner" />
        </div>
      </div>
    )
  } else {
    if (!contractExists) {
      return (
        <div className="main-website">
          <WebsiteHeader />
          <div className="main-body">
            <h1 className="text-xl font-bold text-red-600">Delegator with ID '{delegatorContractAppID}' can't be found on the platform.</h1>
          </div>
        </div>
      )
    } else {
      return (
        <div className="main-website">
          <WebsiteHeader />
          <div className="p-4">
            <h1 className="text-3xl font-bold text-center">Delegator contract ID: {delegatorContractAppID}</h1>
          </div>
          <div className="p-4 flex space-x-4 items-center">
            <h1 className="text-xl font-semibold text-left">Status: {contractStatusTxt}</h1>
            {contractOwner &&
              contractStatus === KEYS_NOT_GENERATED &&
              renderLoadingButton('Refund', executeAction, false, '', loadingButton)}
            {contractOwner &&
              contractStatus === WAITING_CONFIRM_KEYS &&
              renderLoadingButton('Confirm', executeAction, false, '', loadingButton)}
            {contractOwner && contractStatus === CONTRACT_ENDED && renderLoadingButton('End', executeAction, false, '', loadingButton)}
          </div>
          <div className="p-4 border">
            <div className="mb-4 text-lg">Contract is valid until round: {delegatorContractInfo.roundEnd!.toString()}</div>
            <div className="mb-4 text-lg">Contract has started at round: {delegatorContractInfo.roundStart!.toString()}</div>
            <div className="mb-4 text-lg">Delegator address: {ellipseAddress(delegatorContractInfo.delAcc)}</div>
            <div className="mb-4 text-lg">
              Validator ID:{' '}
              <Link to={`/validators/${delegatorContractInfo.valAppId!.toString()}`} className="text-blue-500 underline">
                {delegatorContractInfo.valAppId!.toString()}
              </Link>
            </div>
            <div className="mb-4 text-lg">
              Number of contract breaches: {delegatorContractInfo.numBreach!.toString()} (of maximum allowed{' '}
              {delegatorContractInfo.valConfigMan!.maxBreach.toString()})
            </div>
            {delegatorContractInfo.numBreach != 0n && (
              <div className="mb-4 text-lg">Last contract breach was at round: {delegatorContractInfo.lastBreachRound!.toString()}</div>
            )}
            <div className="space-x-4">
              {renderButton('Show full contract', toggleModal(setOpenDelegatorContract), false)}
              {openDelegatorContract && (
                <dialog id="transact_modal" className={`modal ${openDelegatorContract ? 'modal-open' : ''} bg-slate-200`}>
                  <form method="dialog" className="modal-box">
                    <DelegatorContractTemplate delegatorContractInfo={delegatorContractInfo} />
                    <div className="modal-action ">{renderButton('Close', toggleModal(setOpenDelegatorContract), false)}</div>
                  </form>
                </dialog>
              )}
            </div>
          </div>
          <div className="p-4">
            <div className="mb-4 text-lg">
              To monitor performance visit{' '}
              <a
                href="https://alerts.allo.info/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-indigo-600 hover:text-indigo-900"
              >
                allo.info
              </a>
            </div>
            <div className="space-x-4">
              {renderButton(
                'Withdraw from contract',
                toggleModal(setOpenWithdrawModal),
                contractStatus !== CONTRACT_LIVE,
                contractOwner ? '' : 'invisible',
              )}
              <ConfirmWithdrawal openModal={openWithdrawModal} setModalState={setOpenWithdrawModal} />
            </div>
          </div>
        </div>
      )
    }
  }
}

export default DelegatorContractView
