import { microAlgos } from '@algorandfoundation/algokit-utils'
import { useWallet } from '@txnlab/use-wallet'
import { getApplicationAddress } from 'algosdk'
import { useSnackbar } from 'notistack'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ValidatorAd } from '../interfaces/contract-specs'
import { useGlobalState } from '../providers/GlobalStateProvider'
import { MAX_LINK_LENGTH, MAX_NAME_LENGTH, MBR_VALIDATOR_AD_CREATION, MBR_VALIDATOR_AD_INIT } from '../utils/constants'
import { stringToUint8ArrayWithLength } from '../utils/encodeFunctions'
import { checkUserOptedInApp } from '../utils/getFromBlockchain'
import ValidatorAdTemplate from './ValidatorAdTemplate'

interface SignValidatorAdInterface {
  openModal: boolean
  setModalState: (value: boolean) => void
  createNew: boolean
  validatorAd: ValidatorAd
}

const SignValidatorAd: React.FC<SignValidatorAdInterface> = ({ openModal, setModalState, createNew, validatorAd }) => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState<boolean>(false)

  const { userProfile, setUserProfile, algorandClient, noticeboardApp } = useGlobalState()

  const algodClient = algorandClient.client.algod

  const { enqueueSnackbar } = useSnackbar()

  const { signer, activeAddress, signTransactions, sendTransactions } = useWallet()

  const handleSubmitValidatorAd = async () => {
    if (!signer || !activeAddress) {
      enqueueSnackbar('Please connect wallet first', { variant: 'warning' })
      return
    }

    const sP = await algodClient.getTransactionParams().do()

    let valAppId = validatorAd.appId

    if (createNew) {
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

      setLoading(true)
      try {
        enqueueSnackbar('Creating new validator ad...', { variant: 'info' })
        const noticeboardAppAddress = getApplicationAddress(noticeboardApp.appId)

        const globalState = await noticeboardApp.client.getGlobalState()
        const valFactoryAppId = globalState.valFactoryAppId!.asNumber()
        const valFactoryAppAddress = getApplicationAddress(valFactoryAppId)

        const deposit = await algorandClient.transactions.payment({
          sender: activeAddress,
          receiver: noticeboardAppAddress,
          amount: microAlgos(Number(validatorAd.deposit)),
          extraFee: microAlgos(3 * sP.minFee),
          signer: signer,
        })

        const mbrFactory = await algorandClient.transactions.payment({
          sender: activeAddress,
          receiver: valFactoryAppAddress,
          amount: microAlgos(MBR_VALIDATOR_AD_CREATION),
          signer: signer,
        })

        const mbrVal = await algorandClient.transactions.payment({
          sender: activeAddress,
          receiver: noticeboardAppAddress,
          amount: microAlgos(MBR_VALIDATOR_AD_INIT),
          signer: signer,
        })

        const result = await noticeboardApp.client.createValidatorAd(
          {
            deposit: deposit,
            mbrFactory: mbrFactory,
            mbrVal: mbrVal,
          },
          {
            sender: {
              addr: activeAddress,
              signer: signer,
            },
            apps: [valFactoryAppId],
            boxes: [{ appId: noticeboardApp.appId, name: 'val_list' }],
          },
        )

        enqueueSnackbar(`Transaction sent: ${result.transactions[0].txID()}`, { variant: 'success' })

        const localState = await noticeboardApp.client.getLocalState(activeAddress)
        valAppId = localState.valAppId!.asBigInt()
        const delAppId = localState.delAppId!.asBigInt()

        // If it was successful, change userProfile
        setUserProfile({ ...userProfile, new_user: false, validator: true, valAppId: valAppId, delAppId: delAppId })
      } catch (e) {
        enqueueSnackbar(`Failed to create validator app: ${e}`, { variant: 'error' })
        console.error('Failed to create validator app: %s', e)
        setLoading(false)
        return
      }
      setLoading(false)
    }

    setLoading(true)
    try {
      enqueueSnackbar('Setting validator ad...', { variant: 'info' })
      // Set validator ad
      const valConfigMan = [
        validatorAd.valConfigMan.hwCat,
        validatorAd.valConfigMan.minAmt,
        validatorAd.valConfigMan.maxAmt,
        validatorAd.valConfigMan.feeSetup,
        validatorAd.valConfigMan.feeRound,
        validatorAd.valConfigMan.deposit,
        validatorAd.valConfigMan.setupRounds,
        validatorAd.valConfigMan.confirmationRounds,
        validatorAd.valConfigMan.maxBreach,
        validatorAd.valConfigMan.breachRounds,
        validatorAd.valConfigMan.uptimeGar,
      ] as [bigint, bigint, bigint, bigint, bigint, bigint, bigint, bigint, bigint, bigint, bigint]

      const valConfigExtra = [
        stringToUint8ArrayWithLength(validatorAd.valConfigExtra.name, MAX_NAME_LENGTH),
        stringToUint8ArrayWithLength(validatorAd.valConfigExtra.link, MAX_LINK_LENGTH),
      ] as [Uint8Array, Uint8Array]

      const gtxn = await noticeboardApp.client
        .compose()
        .setValidatorAdMandatory(
          {
            valConfigMan: valConfigMan,
            live: validatorAd.live,
            manager: validatorAd.manager,
            maxDelCnt: validatorAd.maxDelCnt,
          },
          {
            sender: {
              addr: activeAddress,
              signer: signer,
            },
            apps: [Number(valAppId)],
            sendParams: { fee: microAlgos(2 * sP.minFee) },
          },
        )
        .setValidatorAdExtra(
          {
            valConfigExtra: valConfigExtra,
          },
          {
            sender: {
              addr: activeAddress,
              signer: signer,
            },
            apps: [Number(valAppId)],
            sendParams: { fee: microAlgos(2 * sP.minFee) },
          },
        )
        .execute()

      enqueueSnackbar(`Transaction sent: ${gtxn.transactions[0].txID()}`, { variant: 'success' })
    } catch (e) {
      enqueueSnackbar(`Failed to set validator app ${e}`, { variant: 'error' })
      console.error('Failed to set validator app: %s', e)
      setLoading(false)
      return
    }

    setLoading(false)

    // Close the popup
    setModalState(!openModal)
    // Navigate to the created validator
    navigate(`/validators/${valAppId.toString()}`)
  }

  return (
    <dialog id="transact_modal" className={`modal ${openModal ? 'modal-open' : ''} bg-slate-200`}>
      <form method="dialog" className="modal-box">
        <h3 className="font-bold text-lg">Please read and agree with the terms below to finalize your ad.</h3>
        <ValidatorAdTemplate validatorAd={validatorAd} />
        <div className="modal-action ">
          <button className="btn" onClick={() => setModalState(!openModal)}>
            Close
          </button>
          <button data-test-id="send-algo" className={`btn lo`} onClick={handleSubmitValidatorAd}>
            {loading ? <span className="loading loading-spinner" /> : 'Sign'}
          </button>
        </div>
      </form>
    </dialog>
  )
}

export default SignValidatorAd
