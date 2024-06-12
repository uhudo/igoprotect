import { microAlgos } from '@algorandfoundation/algokit-utils'
import { useWallet } from '@txnlab/use-wallet'
import { useSnackbar } from 'notistack'
import { useState } from 'react'
import { useGlobalState } from '../providers/GlobalStateProvider'

interface ClearStateInterface {}

const ClearState: React.FC<ClearStateInterface> = () => {
  const [loading, setLoading] = useState<boolean>(false)

  const { userProfile, setUserProfile, algorandClient, noticeboardApp } = useGlobalState()

  const algodClient = algorandClient.client.algod

  const { enqueueSnackbar } = useSnackbar()

  const { signer, activeAddress } = useWallet()

  const handleSubmitClearState = async () => {
    if (!signer || !activeAddress) {
      enqueueSnackbar('Please connect wallet first', { variant: 'warning' })
      return
    }

    const sP = await algodClient.getTransactionParams().do()

    // For testing
    setLoading(true)
    try {
      enqueueSnackbar('Clearing app state...', { variant: 'info' })
      const result = await noticeboardApp.client.clearState({
        sender: { addr: activeAddress, signer: signer },
        sendParams: { fee: microAlgos(sP.minFee) },
      })
      enqueueSnackbar(`Transaction sent: ${result.transactions[0].txID()}`, { variant: 'success' })

      setUserProfile({ ...userProfile, new_user: true, validator: undefined, delAppId: undefined, valAppId: undefined })
    } catch (e) {
      enqueueSnackbar(`Failed to clear state: ${e}`, { variant: 'error' })
      console.error('Failed to clear state: %s', e)
    }
    setLoading(false)
    ////////
  }

  return (
    <button data-test-id="send-algo" className={`btn lo text-red-600 text-2xl`} onClick={handleSubmitClearState}>
      {loading ? <span className="loading loading-spinner" /> : 'Clear State'}
    </button>
  )
}

export default ClearState
