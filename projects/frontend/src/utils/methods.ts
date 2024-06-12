import { microAlgos } from '@algorandfoundation/algokit-utils'
import { useWallet } from '@txnlab/use-wallet'
import { getApplicationAddress, makeKeyRegistrationTxnWithSuggestedParamsFromObject } from 'algosdk'
import { useSnackbar } from 'notistack'
import { useGlobalState } from '../providers/GlobalStateProvider'

export const executeEndOrBreachedDelegatorContract = async () => {
  const { userProfile, setUserProfile, algorandClient, noticeboardApp } = useGlobalState()
  const { signer, activeAddress } = useWallet()
  const { enqueueSnackbar } = useSnackbar()

  const algodClient = algorandClient.client.algod

  if (!signer || !activeAddress) {
    enqueueSnackbar('Please connect wallet first', { variant: 'warning' })
    return
  }

  const sP = await algodClient.getTransactionParams().do()

  const result = await noticeboardApp.client.endExpiredOrBreachedDelegatorContract(
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

  enqueueSnackbar(`Transaction sent: ${result.transactions[0].txID()}`, { variant: 'success' })

  // If contract end was successful, change userProfile
  setUserProfile({ ...userProfile, new_user: true, validator: undefined, delAppId: undefined, valAppId: undefined })
}

export const executeKeysNotGenerated = async () => {
  const { userProfile, setUserProfile, algorandClient, noticeboardApp } = useGlobalState()
  const { signer, activeAddress } = useWallet()
  const { enqueueSnackbar } = useSnackbar()

  const algodClient = algorandClient.client.algod

  if (!signer || !activeAddress) {
    enqueueSnackbar('Please connect wallet first', { variant: 'warning' })
    return
  }

  const sP = await algodClient.getTransactionParams().do()

  const result = await noticeboardApp.client.keysNotGenerated(
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

  enqueueSnackbar(`Transaction sent: ${result.transactions[0].txID()}`, { variant: 'success' })

  // If contract end was successful, change userProfile
  setUserProfile({ ...userProfile, new_user: true, validator: undefined, delAppId: undefined, valAppId: undefined })
}

export const executeConfirmKeys = async (feeOperation: bigint) => {
  const { userProfile, algorandClient, noticeboardApp } = useGlobalState()
  const { signer, activeAddress } = useWallet()
  const { enqueueSnackbar } = useSnackbar()

  const algodClient = algorandClient.client.algod

  if (!signer || !activeAddress) {
    enqueueSnackbar('Please connect wallet first', { variant: 'warning' })
    return
  }

  const sP = await algodClient.getTransactionParams().do()

  const noticeboardAppAddress = getApplicationAddress(noticeboardApp.appId)

  // Create key deregistration transaction
  const keyDeregTxn = makeKeyRegistrationTxnWithSuggestedParamsFromObject({
    from: activeAddress,
    suggestedParams: { ...sP, fee: 3 * sP.minFee },
  })

  const feeOperationPaymentTxn = await algorandClient.transactions.payment({
    sender: activeAddress,
    receiver: noticeboardAppAddress,
    amount: microAlgos(Number(feeOperation)),
    extraFee: microAlgos(4 * sP.minFee),
    signer: signer,
  })

  const gtxn = await noticeboardApp.client
    .compose()
    .addTransaction({ txn: keyDeregTxn, signer: signer })
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

  enqueueSnackbar(`Transaction sent: ${gtxn.transactions[0].txID()}`, { variant: 'success' })
}
