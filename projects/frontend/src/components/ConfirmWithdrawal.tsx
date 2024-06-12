import { microAlgos } from '@algorandfoundation/algokit-utils'
import { useWallet } from '@txnlab/use-wallet'
import { makeKeyRegistrationTxnWithSuggestedParamsFromObject } from 'algosdk'
import { useSnackbar } from 'notistack'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useGlobalState } from '../providers/GlobalStateProvider'

interface ConfirmWithdrawalInterface {
  openModal: boolean
  setModalState: (value: boolean) => void
}

const ConfirmWithdrawal = ({ openModal, setModalState }: ConfirmWithdrawalInterface) => {
  const [loading, setLoading] = useState<boolean>(false)
  const navigate = useNavigate()

  const { userProfile, setUserProfile, algorandClient, noticeboardApp } = useGlobalState()

  const algodClient = algorandClient.client.algod

  const { enqueueSnackbar } = useSnackbar()

  const { signer, activeAddress, signTransactions, sendTransactions } = useWallet()

  const handleWithdraw = async () => {
    if (!signer || !activeAddress) {
      enqueueSnackbar('Please connect wallet first', { variant: 'warning' })
      return
    }

    setLoading(true)

    const sP = await algodClient.getTransactionParams().do()

    try {
      enqueueSnackbar('Withdrawing from contract ...', { variant: 'info' })

      // const noticeboardAppAddress = getApplicationAddress(noticeboardApp.appId)
      // const validatorAdAddress = getApplicationAddress(delegatorContractInfo.valAppId!)

      // Create key deregistration transaction
      const keyDeregTxn = makeKeyRegistrationTxnWithSuggestedParamsFromObject({
        from: activeAddress,
        suggestedParams: { ...sP, fee: 3 * sP.minFee },
      })

      const gtxn = await noticeboardApp.client
        .compose()
        .addTransaction({ txn: keyDeregTxn, signer: signer })
        .endActiveDelegatorContract(
          {
            keyregTxnIndex: 0,
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

      enqueueSnackbar(`Transaction sent: ${gtxn.transactions[0].txID()}`, { variant: 'success' })
    } catch (e) {
      enqueueSnackbar(`Failed to withdraw from contract ${e}`, { variant: 'error' })
      console.error('Failed to withdraw from contract: %s', e)
      setLoading(false)
      return
    }

    setLoading(true)
    try {
      enqueueSnackbar('Withdrawing balance from app ...', { variant: 'info' })
      const result = await noticeboardApp.client.withdrawBalance(
        {},
        {
          sender: { addr: activeAddress, signer: signer },
          sendParams: { fee: microAlgos(2 * sP.minFee) },
        },
      )
      enqueueSnackbar(`Transaction sent: ${result.transactions[0].txID()}`, { variant: 'success' })

      // If withdrawal was successful, change userProfile
      setUserProfile({ ...userProfile, new_user: true, validator: undefined, delAppId: undefined, valAppId: undefined })

      setLoading(false)
      // Close the popup
      setModalState(!openModal)
      // Navigate to home
      navigate('/')
    } catch (e) {
      enqueueSnackbar(`Failed to withdraw balance: ${e}`, { variant: 'error' })
      console.error('Failed to withdraw balance: %s', e)
    }
    setLoading(false)
  }

  return (
    <dialog id="transact_modal" className={`modal ${openModal ? 'modal-open' : ''} bg-slate-200`}>
      <form method="dialog" className="modal-box">
        <h3 className="font-bold text-lg">
          Do you really want to withdraw from contract and get refunded unused operational fee and deposit?
        </h3>
        <div className="modal-action ">
          <button className="btn" onClick={() => setModalState(!openModal)}>
            Close
          </button>
          <button data-test-id="send-algo" className={`btn lo`} onClick={handleWithdraw}>
            {loading ? <span className="loading loading-spinner" /> : 'Withdraw'}
          </button>
        </div>
      </form>
    </dialog>
  )
}

export default ConfirmWithdrawal
