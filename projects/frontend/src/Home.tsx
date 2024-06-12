// src/components/Home.tsx
import { useWallet } from '@txnlab/use-wallet'
import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import logo from './assets/Logo.png'
import ConnectWallet from './components/ConnectWallet'
import WebsiteHeader from './components/WebsiteHeader'
import { useGlobalState } from './providers/GlobalStateProvider'

const benefitStyle = 'bg-gray-100 p-4 rounded-lg shadow-md text-3xl'
const futureBenefitStyle = 'bg-teal-100 p-4 rounded-lg shadow-md max-w-4xl text-3xl'
const buttonStyle = 'btn bg-gray-200 text-black p-2 rounded'
const buttonConnectWalletStyle = 'btn bg-gray-200 text-black p-2 rounded font-bold'
const hoverStyle = 'hover-message absolute left-0 top-full bg-gray-800 text-white text-xs p-2 rounded hidden group-hover:block'
const hoverFutureBenefitStyle = 'absolute left-0 bottom-full bg-teal-800 text-white text-xs p-2 rounded hidden group-hover:block'
const userQuestionsDividerStyle = 'text-center rounded-lg p-6 max-w-md bg-white mx-auto shadow-md'

interface PlatformBenefitsProps {}

const PlatformBenefits: React.FC<PlatformBenefitsProps> = () => {
  return (
    <div className="flex flex-col items-center text-center py-8 px-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl mb-4">
        <div className={benefitStyle}>
          <h1 className="font-semibold italic relative group">
            Secure{' '}
            <span className={hoverStyle}>
              Your ALGO never leaves your wallet and can be transferred at any time. No information or access is shared.
            </span>
          </h1>
        </div>
        <div className={benefitStyle}>
          <h1 className="font-semibold italic relative group">
            Decentralized <span className={hoverStyle}>Direct delegation to node operators, no stake pooling.</span>
          </h1>
        </div>
        <div className={benefitStyle}>
          <h1 className="font-semibold italic relative group">
            Transparent{' '}
            <span className={hoverStyle}>
              Participation fees are known in advance and fixed, enabling improved financial planning for users and node operators.
            </span>
          </h1>
        </div>
      </div>
      <div className={futureBenefitStyle}>
        <h1 className="font-semibold italic text-black relative group">
          Future: Rewards{' '}
          <span className={hoverFutureBenefitStyle}>
            With Algorand moving to rewarding block producers, you will be getting rewards directly to your wallet.
          </span>
        </h1>
      </div>
    </div>
  )
}

interface PlatformBannerProps {}

const PlatformBanner: React.FC<PlatformBannerProps> = () => {
  return (
    <div className="flex flex-col items-center text-center pt-8 px-4">
      <h1 className="text-2xl font-bold mb-4">Welcome to</h1>
      <img src={logo} alt="IgoProtect" className="h-24 mb-4" />
      <h1 className="text-xl font-semibold mb-2 max-w-4xl">Decentralized Peer-to-Peer Consensus Delegation Platform</h1>
      <h2 className="mb-6 max-w-4xl">
        Via this platform you can help to protect <span className="font-bold">Algorand</span> and your assets on it by participating in
        blockchain consensus, i.e. by{' '}
        <a
          href="https://algorandtechnologies.com/news/proof-of-stake-vs-pure-proof-of-stake-consensus"
          target="_blank"
          className="relative group italic text-blue-500"
        >
          staking
          <span className={hoverStyle}>Click here to learn what staking is and why it's important for you!</span>
        </a>{' '}
        ALGO. Join a worldwide network of consensus nodes operators now!
      </h2>
    </div>
  )
}

interface HomeProps {}

const Home: React.FC<HomeProps> = () => {
  const navigate = useNavigate()
  const [openWalletModal, setOpenWalletModal] = useState<boolean>(false)
  const { activeAddress, signer } = useWallet()

  const { userProfile, algorandClient, setUserProfile, noticeboardApp } = useGlobalState()

  const toggleWalletModal = () => {
    setOpenWalletModal(!openWalletModal)
  }

  const goToValidators = () => {
    setUserProfile({ new_user: true, validator: false, delAppId: undefined, valAppId: undefined })
    navigate(`/validators/`)
  }

  const goToPresetupValidator = () => {
    setUserProfile({ ...userProfile, validator: true })
    navigate(`/validators/presetup`)
  }

  const goToLearn = () => {
    navigate(`/learn`)
  }

  const [secondQuestion, setSecondQuestion] = useState<boolean>(false)

  useEffect(() => {
    if (userProfile.new_user !== undefined && userProfile.new_user === false) {
      // Redirect user to their validator ad or delegator contract webpage
      if (userProfile.validator) {
        navigate(`/validators/${userProfile.valAppId!.toString()}`)
      } else {
        navigate(`/contract/${userProfile.delAppId!.toString()}`)
      }
    }
  }, [userProfile])

  if (userProfile.new_user === undefined || userProfile.new_user === true) {
    // User is undefined or is a new user, thus need to figure out its role
    return (
      <div className="main-website">
        <WebsiteHeader />
        <PlatformBanner />
        <div className="">
          {!activeAddress && (
            <div className={userQuestionsDividerStyle}>
              <div className="max-w-md">
                <div className="grid">
                  <div className="divider">
                    <div> To start please connect your wallet. </div>
                    <button data-test-id="connect-wallet" className={buttonConnectWalletStyle} onClick={toggleWalletModal}>
                      Connect Wallet
                    </button>
                  </div>
                </div>
                <ConnectWallet openModal={openWalletModal} closeModal={toggleWalletModal} />
              </div>
            </div>
          )}

          {activeAddress && (
            <div className={userQuestionsDividerStyle}>
              <div className="max-w-md">
                <div className="grid">
                  {!secondQuestion && (
                    <div className="flex flex-col space-y-2">
                      <div>To help you get started, do you want to participate by...</div>
                      <div className="flex justify-center space-x-2 mt-4">
                        <button className={buttonStyle} onClick={() => setSecondQuestion(true)}>
                          Operating your own node?
                        </button>
                        <button className={buttonStyle} onClick={goToValidators}>
                          Staking your ALGO?
                        </button>
                      </div>
                    </div>
                  )}
                  {secondQuestion && (
                    <div className="flex flex-col space-y-2">
                      <div>Great that you want to be a node operator! Do you...</div>
                      <div className="flex justify-center space-x-2 mt-4">
                        <button className={buttonStyle} onClick={goToPresetupValidator}>
                          Already operate a node?
                        </button>
                        <button className={buttonStyle} onClick={goToLearn}>
                          Want to learn to operate one?
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
        <PlatformBenefits />
      </div>
    )
  } else {
    return
  }
}

export default Home
