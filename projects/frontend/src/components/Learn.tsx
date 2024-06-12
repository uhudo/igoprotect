import { useNavigate } from 'react-router-dom'
import WebsiteHeader from './WebsiteHeader'

interface LearnProps {}

const Learn: React.FC<LearnProps> = () => {
  const navigate = useNavigate()

  const goToCreateValidator = () => {
    navigate(`/validators/presetup`)
  }

  return (
    <div className="main-website">
      <WebsiteHeader />
      <div className="main-body ">
        <div className="p-4 w-full max-w-2xl items-center justify-start min-h-screen">
          <div className="border m-4 p-4 rounded-md">
            <p className="mb-4">Setting up your own node can take up to around one hour.</p>
            <p className="font-bold mb-2">Step 1:</p>
            <p className="mb-4">
              To run a node yourself, you will need a computer that is running 24/7. Check computer requirements at {''}
              <a
                href="https://developer.algorand.org/docs/run-a-node/setup/install/#hardware-requirements"
                target="_blank"
                className="text-blue-500 underline"
              >
                Algorand developer docs.
              </a>
            </p>
            <p className="mb-4">
              If you do not have access to a suitable computer, you can buy one, e.g. similar to {''}
              <a
                href="https://www.amazon.com/Beelink-4-75GHz-Computer-Desktop-Displays/dp/B0C61WPCVT"
                target="_blank"
                className="text-blue-500 underline"
              >
                this one,
              </a>{' '}
              or rent a cloud server, e.g. by {''}
              <a href="https://www.netcup.eu/vserver/vps.php" target="_blank" className="text-blue-500 underline">
                netcup
              </a>
              .
            </p>
            <p className="font-bold mb-2">Step 2:</p>
            <p className="mb-4">
              Install the node software by following, e.g. {''}
              <a
                href="https://developer.algorand.org/docs/run-a-node/setup/install/#installation-with-a-package-manager"
                target="_blank"
                className="text-blue-500 underline"
              >
                official docs
              </a>
              , or various excellent community guides and simplified solutions like:{' '}
              <a href="https://github.com/AustP/austs-one-click-node/releases" target="_blank" className="text-blue-500 underline">
                Aust One Click Node
              </a>{' '}
              - simple installation for any operating system,{' '}
              <a
                href="https://developer.algorand.org/docs/run-a-node/setup/install/#installation-with-a-package-manager"
                target="_blank"
                className="text-blue-500 underline"
              >
                Pixelnode
              </a>{' '}
              - simple node management, or {''}
              <a
                href="https://www.reddit.com/r/AlgorandOfficial/comments/vlbrha/setting_up_a_raspberry_pi_4_participation_node"
                target="_blank"
                className="text-blue-500 underline"
              >
                guide tailored for Raspberry Pi 4
              </a>
              .
            </p>

            <p className="font-bold mb-2">Step 3:</p>
            <p className="mb-4">Register at IgoProtect to let others use your free capabilities and earn some fees.</p>

            <button className="btn hover text-black font-bold py-2 px-4 rounded" onClick={goToCreateValidator}>
              Create an ad for your validator
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Learn
