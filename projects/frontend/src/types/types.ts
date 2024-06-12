// types.ts

import { NoticeboardClient } from '../contracts/Noticeboard'
import { NoticeboardInfo, ValidatorAd } from '../interfaces/contract-specs'

export type NoticeboardApp = {
  appId: number
  noticeboardInfo: NoticeboardInfo
  client: NoticeboardClient
  validatorList: bigint[]
  validators: ValidatorAd[]
}

export type UserProfile = {
  validator: boolean | undefined
  new_user: boolean | undefined
  valAppId: bigint | undefined
  delAppId: bigint | undefined
}
