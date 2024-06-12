import * as algokit from '@algorandfoundation/algokit-utils'
import { microAlgos } from '@algorandfoundation/algokit-utils'
import { useWallet } from '@txnlab/use-wallet'
import { useSnackbar } from 'notistack'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ValidatorAd } from '../interfaces/contract-specs'
import { useGlobalState } from '../providers/GlobalStateProvider'
import { getAlgodConfigFromViteEnvironment } from '../utils/network/getAlgoClientConfigs'

interface DeleteValidatorAdInterface {
  openModal: boolean
  setModalState: (value: boolean) => void
  validatorAd: ValidatorAd
}

const DeleteValidatorAd = ({ openModal, setModalState, validatorAd }: DeleteValidatorAdInterface) => {
  const navigate = useNavigate()

  const [loading, setLoading] = useState<boolean>(false)

  const { userProfile, setUserProfile, algorandClient, noticeboardApp } = useGlobalState()

  const algodConfig = getAlgodConfigFromViteEnvironment()
  const algodClient = algokit.getAlgoClient({
    server: algodConfig.server,
    port: algodConfig.port,
    token: algodConfig.token,
  })

  const { enqueueSnackbar } = useSnackbar()

  const { signer, activeAddress, signTransactions, sendTransactions } = useWallet()

  const handleDeleteValidatorAd = async () => {
    if (!signer || !activeAddress) {
      enqueueSnackbar('Please connect wallet first', { variant: 'warning' })
      return
    }

    setLoading(true)
    try {
      enqueueSnackbar('Deleting validator ad...', { variant: 'info' })
      const sP = await algodClient.getTransactionParams().do()

      const result = await noticeboardApp.client.endValidatorAd(
        {},
        {
          sender: {
            addr: activeAddress,
            signer: signer,
          },
          apps: [Number(validatorAd.appId)],
          boxes: [{ appId: noticeboardApp.appId, name: 'val_list' }],
          sendParams: { fee: microAlgos(2 * sP.minFee) },
        },
      )

      enqueueSnackbar(`Transaction sent: ${result.transaction.txID()}`, { variant: 'success' })

      // If it was successful, change userProfile
      setUserProfile({ ...userProfile, new_user: true, validator: false })
    } catch (e) {
      enqueueSnackbar(`Failed to delete validator app: ${e}`, { variant: 'error' })
      console.error('Failed to delete validator app: %s', e)
      return
    }
    setLoading(false)

    // Close the popup
    setModalState(!openModal)
    // Navigate to the created validator
    navigate(`/validators`)
  }

  return (
    <dialog id="transact_modal" className={`modal ${openModal ? 'modal-open' : ''} bg-slate-200`}>
      <form method="dialog" className="modal-box">
        <h3 className="font-bold text-lg">Are you sure you want to proceed?</h3>
        <div className="modal-action ">
          <button className="btn" onClick={() => setModalState(!openModal)}>
            Back
          </button>
          <button data-test-id="send-algo" className={`btn lo`} onClick={handleDeleteValidatorAd}>
            {loading ? <span className="loading loading-spinner" /> : 'Delete ad'}
          </button>
        </div>
      </form>
    </dialog>
  )
}

export default DeleteValidatorAd
