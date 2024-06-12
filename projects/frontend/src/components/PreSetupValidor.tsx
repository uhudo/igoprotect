import { useNavigate } from 'react-router-dom'
import { useGlobalState } from '../providers/GlobalStateProvider'
import WebsiteHeader from './WebsiteHeader'

interface PreSetupValidorProps {}

const PreSetupValidor: React.FC<PreSetupValidorProps> = () => {
  const navigate = useNavigate()

  const { userProfile, setUserProfile } = useGlobalState()

  const goToCreateValidator = () => {
    if (userProfile.new_user || userProfile.valAppId === undefined) {
      setUserProfile({ ...userProfile, validator: true, new_user: true })
      navigate(`/validators/0`)
    } else {
      navigate(`/validators/${userProfile.valAppId}`)
    }
  }

  return (
    <div className="main-website">
      <WebsiteHeader />
      <div className="main-body">
        <div className="p-4 w-full max-w-2xl items-center justify-start min-h-screen">
          <div className="border m-4 p-4 rounded-md">
            <div>
              <p className="mb-4">
                Great that you want to be a part of IgoProtect with your node and let others delegate their stake to you!{' '}
              </p>
              <p className="mb-4">
                To start, please download and run the automatic request servicing script that you can find at our{' '}
                <a
                  href="https://github.com/uhudo/igoprotect/blob/main/projects/i-go-protect/validator-script/README.md#usage-instructions"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-500 underline"
                >
                  Github
                </a>
                . For running the script, you will need Python version 3.12 or newer. You will need to run the script continuously to
                service the requests you get from users via the platform.{' '}
              </p>
              <p className="mb-4">
                The script will operate a hot wallet for you to service the requests. The wallet is not secured, thus fund it just with
                little funds to cover transaction fees (e.g. 1 ALGO should suffice). Based on your popularity, you will need to top it up
                occasionally to service new requests. The hot wallet does not have any access to your potential validator earnings.
              </p>
              <p className="mb-4">Once you have your script setup and the hot wallet ready, click next.</p>
              <button className="btn hover text-black font-bold py-2 px-4 rounded" onClick={goToCreateValidator}>
                Next
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PreSetupValidor
