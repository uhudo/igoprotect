import { useWallet } from '@txnlab/use-wallet'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import logo from '../assets/Logo.png'
import { ellipseAddress } from '../utils/ellipseAddress'
import ConnectWallet from './ConnectWallet'

interface WebsiteHeaderProps {}

const WebsiteHeader: React.FC<WebsiteHeaderProps> = () => {
  const navigate = useNavigate()
  const { activeAddress } = useWallet()

  const [openWalletModal, setOpenWalletModal] = useState<boolean>(false)
  const toggleWalletModal = () => {
    setOpenWalletModal(!openWalletModal)
  }

  const goToHome = () => {
    navigate(`/`)
  }

  const goToValidatrs = () => {
    navigate(`/validators/`)
  }

  const goToLearn = () => {
    navigate(`/learn/`)
  }

  return (
    <header className="flex items-center justify-between p-4 bg-white border-b border-gray-300">
      <div className="logo">
        <img src={logo} alt="IgoProtect" className="h-10" />
      </div>
      <nav className="flex space-x-6">
        <button className="text-black font-bold" onClick={goToHome}>
          Home
        </button>
        <button className="text-black font-bold" onClick={goToValidatrs}>
          Validators
        </button>
        <button className="text-black font-bold" onClick={goToLearn}>
          Run a node
        </button>
        <button
          className="text-black font-bold"
          onClick={() => window.open('https://github.com/uhudo/igoprotect/tree/main?tab=readme-ov-file#overview', '_blank')}
        >
          Docs
        </button>
        <button className="text-black font-bold" onClick={() => window.open('https://github.com/uhudo/igoprotect', '_blank')}>
          Github
        </button>
        <button className="text-black font-bold" onClick={() => window.open('https://x.com/IgoProtect', '_blank')}>
          Socials
        </button>
        {/* <ClearState />
        <CurrentRound /> */}
      </nav>
      <div className="flex items-center space-x-4">
        <button className="text-2xl">☰</button>
        <button className="bg-gray-200 text-black font-bold py-2 px-4 rounded" onClick={toggleWalletModal}>
          {activeAddress ? ellipseAddress(activeAddress) : 'Connect Wallet'}
        </button>
        <ConnectWallet openModal={openWalletModal} closeModal={toggleWalletModal} />
      </div>
    </header>
  )
}

export default WebsiteHeader
