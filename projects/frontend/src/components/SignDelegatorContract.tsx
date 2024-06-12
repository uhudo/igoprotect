import { microAlgos } from '@algorandfoundation/algokit-utils'
import { useWallet } from '@txnlab/use-wallet'
import { getApplicationAddress } from 'algosdk'
import { useSnackbar } from 'notistack'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { DelegatorContractInfo } from '../interfaces/contract-specs'
import { useGlobalState } from '../providers/GlobalStateProvider'
import { DEFAULT_DELEGATOR_CONTRACT_DURATION, MBR_DELEGATOR_CONTRACT_CREATION, START_ROUND_IN_FUTURE } from '../utils/constants'
import { checkUserOptedInApp } from '../utils/getFromBlockchain'
import DelegatorContractTemplate from './DelegatorContractTemplate'

interface SignDelegatorContractInterface {
  openModal: boolean
  setModalState: (value: boolean) => void
  delegatorContractInfo: DelegatorContractInfo
  setDelegatorContractInfo: React.Dispatch<React.SetStateAction<DelegatorContractInfo>>
}

const SignDelegatorContract: React.FC<SignDelegatorContractInterface> = ({
  openModal,
  setModalState,
  delegatorContractInfo,
  setDelegatorContractInfo,
}) => {
  const [loading, setLoading] = useState<boolean>(false)
  const navigate = useNavigate()

  const { userProfile, setUserProfile, algorandClient, noticeboardApp } = useGlobalState()

  const algodClient = algorandClient.client.algod

  const { enqueueSnackbar } = useSnackbar()

  const { signer, activeAddress, signTransactions, sendTransactions } = useWallet()

  const handleSubmitUserContract = async () => {
    if (!signer || !activeAddress) {
      enqueueSnackbar('Please connect wallet first', { variant: 'warning' })
      return
    } else {
      setDelegatorContractInfo({ ...delegatorContractInfo, delAcc: activeAddress })
    }

    const sP = await algodClient.getTransactionParams().do()
    let delAppId = 0n

    // Check if user-opted-in
    const isUserOptedIn = await checkUserOptedInApp(algodClient, activeAddress, noticeboardApp.appId)

    if (!isUserOptedIn) {
      setLoading(true)

      try {
        enqueueSnackbar('Opting into the app...', { variant: 'info' })
        const result = await noticeboardApp.client.optIn.userOptIn(
          {},
          { sender: { addr: activeAddress, signer: signer }, sendParams: { fee: microAlgos(sP.minFee) } },
        )
        enqueueSnackbar(`Transaction sent: ${result.transaction.txID()}`, { variant: 'success' })
      } catch (e) {
        enqueueSnackbar(`Failed to opt into the app: ${e}`, { variant: 'error' })
        console.error('Failed to opt into the app: %s', e)
      }

      setLoading(false)
    }

    try {
      enqueueSnackbar('Creating delegator contract ...', { variant: 'info' })

      const noticeboardAppAddress = getApplicationAddress(noticeboardApp.appId)
      const validatorAdAddress = getApplicationAddress(delegatorContractInfo.valAppId!)

      const depositPayment = await algorandClient.transactions.payment({
        sender: activeAddress,
        receiver: noticeboardAppAddress,
        amount: microAlgos(Number(delegatorContractInfo.valConfigMan!.deposit)),
        extraFee: microAlgos(5 * sP.minFee),
        signer: signer,
      })

      const feeSetupPayment = await algorandClient.transactions.payment({
        sender: activeAddress,
        receiver: noticeboardAppAddress,
        amount: microAlgos(Number(delegatorContractInfo.valConfigMan!.feeSetup)),
        signer: signer,
      })

      const mbrPayment = await algorandClient.transactions.payment({
        sender: activeAddress,
        receiver: validatorAdAddress,
        amount: microAlgos(MBR_DELEGATOR_CONTRACT_CREATION),
        signer: signer,
      })

      const result = await noticeboardApp.client.createDelegatorContract(
        {
          valAppId: delegatorContractInfo.valAppId!,
          depositPayment: depositPayment,
          feeSetupPayment: feeSetupPayment,
          mbr: mbrPayment,
          roundStart: delegatorContractInfo.roundStart!,
          roundEnd: delegatorContractInfo.roundEnd!,
        },
        {
          sender: {
            addr: activeAddress,
            signer: signer,
          },
          apps: [Number(delegatorContractInfo.valAppId!)],
        },
      )

      enqueueSnackbar(`Transaction sent: ${result.transactions[0].txID()}`, { variant: 'success' })

      const localState = await noticeboardApp.client.getLocalState(activeAddress)
      delAppId = localState.delAppId!.asBigInt()
    } catch (e) {
      enqueueSnackbar(`Failed to set validator app ${e}`, { variant: 'error' })
      console.error('Failed to set validator app: %s', e)
      return
    }

    setLoading(false)

    // Close the popup
    setModalState(!openModal)
    // Navigate to the created delegator
    if (delAppId !== 0n) {
      // If it was successful, change userProfile
      setUserProfile({ ...userProfile, new_user: false, validator: false, delAppId: delAppId, valAppId: delegatorContractInfo.valAppId })
      setDelegatorContractInfo({ ...delegatorContractInfo, appId: delAppId })
      // Navigate to user dashboard
      navigate(`/contract/${delAppId.toString()}`)
    } else {
      navigate(`/validators`)
    }
  }

  // Periodically update current round if user is new, i.e. ready to be come a validator
  const updateRounds = async () => {
    if (typeof setDelegatorContractInfo === 'function' && userProfile.new_user) {
      try {
        const algodStatus = await algorandClient.client.algod.status().do()
        const currentRound = BigInt(algodStatus['last-round'] + START_ROUND_IN_FUTURE)

        setDelegatorContractInfo((prevState) => ({
          ...prevState,
          roundStart: currentRound,
          roundEnd: currentRound + BigInt(DEFAULT_DELEGATOR_CONTRACT_DURATION),
        }))

        console.log('Fetched up-to-date round number.')
      } catch (e) {
        console.error('Failed to get current round number: %s', e)
      }
    }
  }
  useEffect(() => {
    // Set up the interval to call updateRounds every x/2*3_000 milliseconds = x/2 rounds
    const intervalId = setInterval(updateRounds, Number((3_000 * START_ROUND_IN_FUTURE) / 2))

    // Clean up the interval when the component is unmounted
    return () => clearInterval(intervalId)
  }, [])

  const handleRoundStartChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const inputValue = e.target.value
    // Ensure input is a valid number
    if (/^\d*$/.test(inputValue)) {
      let start = BigInt(inputValue)
      if (start < 0) {
        start = 0n
      }
      if (start > delegatorContractInfo.roundEnd!) {
        const end = delegatorContractInfo.roundStart! + BigInt(DEFAULT_DELEGATOR_CONTRACT_DURATION)

        setDelegatorContractInfo({ ...delegatorContractInfo, roundStart: start, roundEnd: end })
      } else {
        setDelegatorContractInfo({ ...delegatorContractInfo, roundStart: start })
      }
    }
  }

  const handleRoundEndChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const inputValue = e.target.value
    // Ensure input is a valid number
    if (/^\d*$/.test(inputValue)) {
      let end = BigInt(inputValue)
      if (end < 0) {
        end = 0n
      }
      // if (end < delegatorContractInfo.roundStart!) {
      //   end = delegatorContractInfo.roundStart! + BigInt(DEFAULT_DELEGATOR_CONTRACT_DURATION)
      // }
      setDelegatorContractInfo({ ...delegatorContractInfo, roundEnd: end })
    }
  }

  return (
    <dialog id="transact_modal" className={`modal ${openModal ? 'modal-open' : ''} bg-slate-200`}>
      <form method="dialog" className="modal-box">
        <div>
          <div className="border border-solid border-gray-300">
            {delegatorContractInfo.valConfigExtra !== undefined && (
              <p>Great that you trust {delegatorContractInfo.valConfigExtra.name} to protect the network for you!</p>
            )}
            <p>Fill your desired start and end date of the contract and read the protection agreement below.</p>

            <div className="border border-solid border-gray-500">
              Start round:{' '}
              <input
                type="number"
                id="round_start"
                value={delegatorContractInfo.roundStart!.toString()}
                onChange={handleRoundStartChange}
              />
            </div>
            <div className="border border-solid border-gray-500">
              End round:{' '}
              <input type="number" id="round_end" value={delegatorContractInfo.roundEnd!.toString()} onChange={handleRoundEndChange} />
            </div>
          </div>
          <h3 className="font-bold text-lg">Please read and agree with IgoProtect terms below to finalize your contract.</h3>
        </div>

        <DelegatorContractTemplate delegatorContractInfo={delegatorContractInfo} />

        <div className="modal-action ">
          <button className="btn" onClick={() => setModalState(!openModal)}>
            Close
          </button>
          <button data-test-id="send-algo" className={`btn lo`} onClick={handleSubmitUserContract}>
            {loading ? <span className="loading loading-spinner" /> : 'Sign'}
          </button>
        </div>
      </form>
    </dialog>
  )
}

export default SignDelegatorContract
