import { Provider, useWallet } from '@txnlab/use-wallet'
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useGlobalState } from '../providers/GlobalStateProvider'
import { DEFULAT_USER_PROFILE } from '../utils/constants'
import { checkUserOptedInApp, configUserProfileFromAddress } from '../utils/getFromBlockchain'
import Account from './Account'

interface ConnectWalletInterface {
  openModal: boolean
  closeModal: () => void
}

const ConnectWallet = ({ openModal, closeModal }: ConnectWalletInterface) => {
  const navigate = useNavigate()
  const { providers, activeAddress, activeAccount } = useWallet()
  const { userProfile, algorandClient, setUserProfile, noticeboardApp } = useGlobalState()

  const isKmd = (provider: Provider) => provider.metadata.name.toLowerCase() === 'kmd'

  useEffect(() => {
    const setUserProfileFromLocalState = async () => {
      if (activeAddress) {
        console.log('Active address: ', activeAddress)

        try {
          // Querry algod if user is already opted-in Noticeboard.
          const isUserOptedIn = await checkUserOptedInApp(algorandClient.client.algod, activeAddress, noticeboardApp.appId)

          if (isUserOptedIn) {
            // Based on user state, assign its roles
            configUserProfileFromAddress({
              address: activeAddress,
              noticeboardApp: noticeboardApp,
              algodClient: algorandClient.client.algod,
              userProfile: userProfile,
              setUserProfile: setUserProfile,
            })
          } else {
            setUserProfile({ ...DEFULAT_USER_PROFILE, new_user: true })
          }
        } catch (err) {
          console.log(err)
          setUserProfile(DEFULAT_USER_PROFILE)
        }
      }
    }

    setUserProfileFromLocalState()
  }, [activeAddress])

  useEffect(() => {
    console.log(userProfile)
  }, [userProfile])

  return (
    <dialog id="connect_wallet_modal" className={`modal ${openModal ? 'modal-open' : ''}`}>
      <form method="dialog" className="modal-box bg-white rounded-lg shadow-xl">
        <h3 className="font-bold text-2xl mb-4">Select Wallet Provider</h3>
        <div className="space-y-4">
          <Account />
        </div>
        <div className="space-y-4">
          {providers?.map((provider) => (
            <div key={provider.metadata.id} className="p-4 border rounded-lg shadow-sm">
              <h4 className="font-semibold flex items-center space-x-2">
                {!isKmd(provider) && (
                  <img
                    width={30}
                    height={30}
                    alt={`${provider.metadata.name} icon`}
                    src={provider.metadata.icon}
                    className="inline-block"
                  />
                )}
                {isKmd(provider) && <span>{provider.metadata.name}</span>}
                {provider.isActive && <span className="text-green-600">[active]</span>}
              </h4>

              <div className="mt-2 space-x-2">
                <button type="button" onClick={provider.connect} disabled={provider.isConnected} className="btn btn-primary">
                  Connect
                </button>
                <button type="button" onClick={provider.disconnect} disabled={!provider.isConnected} className="btn btn-secondary">
                  Disconnect
                </button>
                <button
                  type="button"
                  onClick={provider.setActiveProvider}
                  disabled={!provider.isConnected || provider.isActive}
                  className="btn btn-accent"
                >
                  Set Active
                </button>
              </div>

              {provider.isActive && provider.accounts.length > 0 && (
                <div className="mt-4">
                  <select
                    value={activeAccount?.address}
                    onChange={(e) => provider.setActiveAccount(e.target.value)}
                    className="select select-bordered w-full"
                  >
                    {provider.accounts.map((account) => (
                      <option key={account.address} value={account.address}>
                        {account.address}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="modal-action mt-4">
          <button
            data-test-id="close-wallet-modal"
            className="btn btn-outline"
            onClick={() => {
              closeModal()
            }}
          >
            Close
          </button>
          {activeAddress && (
            <button
              className="btn btn-warning"
              data-test-id="logout"
              onClick={() => {
                if (providers) {
                  setUserProfile(DEFULAT_USER_PROFILE)
                  const activeProvider = providers.find((p) => p.isActive)
                  if (activeProvider) {
                    activeProvider.disconnect()
                  } else {
                    // Required for logout/cleanup of inactive providers
                    // For instance, when you login to localnet wallet and switch network
                    // to testnet/mainnet or vice verse.
                    localStorage.removeItem('txnlab-use-wallet')
                    window.location.reload()
                  }
                  navigate('/')
                }
              }}
            >
              Logout
            </button>
          )}
        </div>
      </form>
    </dialog>
  )
}

export default ConnectWallet
