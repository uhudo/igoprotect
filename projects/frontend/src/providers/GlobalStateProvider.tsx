// GlobalState.tsx
import AlgorandClient from '@algorandfoundation/algokit-utils/types/algorand-client'
import React, { ReactNode, createContext, useContext, useState } from 'react'
import { NoticeboardClient } from '../contracts/Noticeboard'
import { NoticeboardApp, UserProfile } from '../types/types'
import { getAlgodConfigFromViteEnvironment } from '../utils/network/getAlgoClientConfigs'

// Get the app ID of the deployed Noticeboard
import { noticeboardAppID } from '../noticeboardAppID'
import { DEFULAT_USER_PROFILE } from '../utils/constants'
import { getNoticeboardInfo } from '../utils/getFromBlockchain'

type GlobalStateType = {
  userProfile: UserProfile
  setUserProfile: React.Dispatch<React.SetStateAction<UserProfile>>
  algorandClient: AlgorandClient
  setAlgorandClient: React.Dispatch<React.SetStateAction<AlgorandClient>>
  noticeboardApp: NoticeboardApp
  setNoticeboardApp: React.Dispatch<React.SetStateAction<NoticeboardApp>>
}

const algodConfig = getAlgodConfigFromViteEnvironment()
const defaultAlgorandClient: AlgorandClient = AlgorandClient.fromConfig({ algodConfig })

const defaultNoticeboardClient: NoticeboardClient = new NoticeboardClient(
  {
    resolveBy: 'id',
    id: noticeboardAppID,
  },
  defaultAlgorandClient.client.algod,
)

const defaultNoticeboardInfo = await getNoticeboardInfo(defaultNoticeboardClient)

const defaultNoticeboardApp: NoticeboardApp = {
  appId: noticeboardAppID,
  noticeboardInfo: defaultNoticeboardInfo!,
  client: defaultNoticeboardClient,
  validatorList: [],
  validators: [],
}

const GlobalStateContext = createContext<GlobalStateType | undefined>(undefined)

const GlobalStateProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [userProfile, setUserProfile] = useState<UserProfile>(DEFULAT_USER_PROFILE)
  const [noticeboardApp, setNoticeboardApp] = useState<NoticeboardApp>(defaultNoticeboardApp)
  const [algorandClient, setAlgorandClient] = useState<AlgorandClient>(defaultAlgorandClient)

  return (
    <GlobalStateContext.Provider
      value={{
        userProfile,
        setUserProfile,
        algorandClient,
        setAlgorandClient,
        noticeboardApp,
        setNoticeboardApp,
      }}
    >
      {children}
    </GlobalStateContext.Provider>
  )
}

const useGlobalState = (): GlobalStateType => {
  const context = useContext(GlobalStateContext)
  if (context === undefined) {
    throw new Error('useGlobalState must be used within a GlobalStateProvider')
  }
  return context
}

export { GlobalStateProvider, useGlobalState }
