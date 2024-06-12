import { microAlgos } from '@algorandfoundation/algokit-utils'
import { useWallet } from '@txnlab/use-wallet'
import { useSnackbar } from 'notistack'
import { useState } from 'react'
import { ValidatorAd } from '../interfaces/contract-specs'
import { useGlobalState } from '../providers/GlobalStateProvider'

interface WithdrawBalanceInterface {
  openModal: boolean
  setModalState: (value: boolean) => void
  validatorAd: ValidatorAd
  setValidatorAd: React.Dispatch<React.SetStateAction<ValidatorAd | undefined>>
}

const WithdrawBalance: React.FC<WithdrawBalanceInterface> = ({ openModal, setModalState, validatorAd, setValidatorAd }) => {
  const [loading, setLoading] = useState<boolean>(false)

  const { userProfile, setUserProfile, algorandClient, noticeboardApp } = useGlobalState()

  const algodClient = algorandClient.client.algod

  const { enqueueSnackbar } = useSnackbar()

  const { signer, activeAddress } = useWallet()

  const handleSubmitWithdrawBalance = async () => {
    if (!signer || !activeAddress) {
      enqueueSnackbar('Please connect wallet first', { variant: 'warning' })
      return
    }

    const sP = await algodClient.getTransactionParams().do()

    setLoading(true)
    try {
      enqueueSnackbar('Withdrawing earnings from app ...', { variant: 'info' })
      const result = await noticeboardApp.client.withdrawBalance(
        {},
        {
          sender: { addr: activeAddress, signer: signer },
          sendParams: { fee: microAlgos(2 * sP.minFee) },
        },
      )
      enqueueSnackbar(`Transaction sent: ${result.transactions[0].txID()}`, { variant: 'success' })

      // Mark reseting of validator earnings - without having to re-read from on-chain
      setValidatorAd({ ...validatorAd, earnings: 0n })
    } catch (e) {
      enqueueSnackbar(`Failed to withdraw earnings: ${e}`, { variant: 'error' })
      console.error('Failed to withdraw earnings: %s', e)
    }
    setLoading(false)

    // Close the popup
    setModalState(!openModal)
  }

  return (
    <dialog id="transact_modal" className={`modal ${openModal ? 'modal-open' : ''} bg-slate-200`}>
      <form method="dialog" className="modal-box">
        <h3 className="font-bold text-lg">Are you sure you want to proceed with withdrawal of your earnings?</h3>
        <div className="modal-action ">
          <button className="btn" onClick={() => setModalState(!openModal)}>
            Back
          </button>
          <button data-test-id="send-algo" className={`btn lo`} onClick={handleSubmitWithdrawBalance}>
            {loading ? <span className="loading loading-spinner" /> : 'Withdraw'}
          </button>
        </div>
      </form>
    </dialog>
  )
}

export default WithdrawBalance
