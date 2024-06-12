import { useEffect, useState } from 'react'
import { useGlobalState } from '../providers/GlobalStateProvider'

interface CurrentRoundInterface {}

const CurrentRound: React.FC<CurrentRoundInterface> = () => {
  const [currentRound, setCurrentRound] = useState<number>(0)

  const { algorandClient } = useGlobalState()

  const algodClient = algorandClient.client.algod

  // Periodically update current round if user is new, i.e. ready to be come a validator
  const updateRounds = async () => {
    try {
      const algodStatus = await algodClient.status().do()
      const currentRoundNew = algodStatus['last-round']

      setCurrentRound(currentRoundNew)

      console.log('Fetched up-to-date round number in header.')
    } catch (e) {
      console.error('Failed to get current round number in header: %s', e)
    }
  }
  useEffect(() => {
    // Set up the interval to call updateRounds
    const intervalId = setInterval(updateRounds, Number(5_000))

    // Clean up the interval when the component is unmounted
    return () => clearInterval(intervalId)
  }, [])

  return <div className="text-l text-red-600">Current round number: {currentRound}</div>
}

export default CurrentRound
