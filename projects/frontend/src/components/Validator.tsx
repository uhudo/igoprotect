import { useWallet } from '@txnlab/use-wallet'
import _ from 'lodash'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { DelegatorContractInfo, ValConfigExtra, ValConfigMan, ValidatorAd } from '../interfaces/contract-specs'
import { useGlobalState } from '../providers/GlobalStateProvider'
import {
  DEFAULT_DELEGATOR_CONTRACT_DURATION,
  DEFAULT_VALIDATOR_AD,
  MAX_LINK_LENGTH,
  MAX_NAME_LENGTH,
  MIN_STAKE_RANGE,
  START_ROUND_IN_FUTURE,
  UNDEFINED_DELEGATOR_CONTRACT_INFO,
} from '../utils/constants'
import { configUserProfileFromAddress, getValidatorAd, getValidatorIDs } from '../utils/getFromBlockchain'
import DeleteValidatorAd from './DeleteValidatorAd'
import SignDelegatorContract from './SignDelegatorContract'
import SignValidatorAd from './SignValidatorAd'
import ValidatorDelegators from './ValidatorDelegators'
import WebsiteHeader from './WebsiteHeader'
import WithdrawBalance from './WithdrawBalance'

const renderInput = (
  label: string,
  id: string,
  type: string,
  value: string | number,
  edit: boolean | undefined,
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void,
  maxLength?: number,
) => (
  <div className="mb-4 flex items-center space-x-2">
    <label htmlFor={id} className="block text-sm font-medium text-gray-700">
      {label}:
    </label>
    <input
      readOnly={!edit}
      type={type}
      id={id}
      value={value}
      onChange={onChange}
      maxLength={maxLength}
      className={`mt-1 flex-1 block w-full rounded-md border-2 shadow-sm focus:ring focus:ring-indigo-200 focus:ring-opacity-50 ${
        edit ? 'border-indigo-500 bg-white' : 'border-gray-300 bg-gray-100'
      } text-sm`}
    />
  </div>
)

interface ValidatorInfoProps {
  edit: boolean | undefined
  validatorAd: ValidatorAd
  setValidatorAd: React.Dispatch<React.SetStateAction<ValidatorAd | undefined>>
}

const ValidatorInfo: React.FC<ValidatorInfoProps> = ({ edit, validatorAd, setValidatorAd }) => {
  const handleStakeChange = (type: 'minAmt' | 'maxAmt') => (e: React.ChangeEvent<HTMLInputElement>) => {
    let inputValue = BigInt(e.target.value)
    if (type === 'maxAmt' && inputValue < validatorAd.valConfigMan.minAmt) {
      inputValue = validatorAd.valConfigMan.minAmt + MIN_STAKE_RANGE
    } else if (type === 'minAmt' && inputValue > validatorAd.valConfigMan.maxAmt) {
      inputValue = validatorAd.valConfigMan.maxAmt - MIN_STAKE_RANGE
    } else if (inputValue < 0) {
      inputValue = MIN_STAKE_RANGE
    }
    setValidatorAd({ ...validatorAd, valConfigMan: { ...validatorAd.valConfigMan, [type]: inputValue } })
  }

  const handleChange =
    (key: keyof ValConfigMan | keyof ValConfigExtra, nested: 'valConfigMan' | 'valConfigExtra') =>
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = nested === 'valConfigMan' ? BigInt(e.target.value) : e.target.value
      setValidatorAd({ ...validatorAd, [nested]: { ...validatorAd[nested], [key]: value } })
    }

  return (
    <div className="p-6 bg-white shadow-md rounded-md">
      <div className="border p-4 mb-4 rounded-md">
        <h1 className="text-lg font-semibold mb-4">Mandatory info:</h1>
        <div className="flex space-x-4">
          <div className="flex-1">
            {renderInput(
              'Min stake [uALGO]',
              'min-stake',
              'number',
              Number(validatorAd.valConfigMan.minAmt),
              edit,
              handleStakeChange('minAmt'),
            )}
          </div>
          <div className="flex-1">
            {renderInput(
              'Max stake [uALGO]',
              'max-stake',
              'number',
              Number(validatorAd.valConfigMan.maxAmt),
              edit,
              handleStakeChange('maxAmt'),
            )}
          </div>
        </div>
        <div className="flex-1">
          <div className="flex space-x-4">
            <div className="flex-1">
              {renderInput(
                'Setup fee [uALGO]',
                'fee-setup',
                'number',
                Number(validatorAd.valConfigMan.feeSetup),
                edit,
                handleChange('feeSetup', 'valConfigMan'),
              )}
            </div>
            <div className="flex-1">
              {renderInput(
                'Operational fee [uALGO/round]',
                'fee-round',
                'number',
                Number(validatorAd.valConfigMan.feeRound),
                edit,
                handleChange('feeRound', 'valConfigMan'),
              )}
            </div>
          </div>
          <div className="flex space-x-4">
            <div className="flex-1">
              {renderInput(
                'Setup rounds [round]',
                'setup-round',
                'number',
                Number(validatorAd.valConfigMan.setupRounds),
                edit,
                handleChange('setupRounds', 'valConfigMan'),
              )}
            </div>
            <div className="flex-1">
              {renderInput(
                'Confirmation rounds [round]',
                'confirmation-round',
                'number',
                Number(validatorAd.valConfigMan.confirmationRounds),
                edit,
                handleChange('confirmationRounds', 'valConfigMan'),
              )}
            </div>
          </div>

          <div className="flex space-x-4">
            <div className="flex-1">
              {renderInput(
                'Required deposit [uALGO]',
                'deposit',
                'number',
                Number(validatorAd.valConfigMan.deposit),
                edit,
                handleChange('deposit', 'valConfigMan'),
              )}
            </div>
            <div className="flex-1">
              {renderInput(
                'Maximum number of allowable breaches',
                'max-breach',
                'number',
                Number(validatorAd.valConfigMan.maxBreach),
                edit,
                handleChange('maxBreach', 'valConfigMan'),
              )}
            </div>
          </div>
        </div>
      </div>
      <div className="border p-4 rounded-md">
        <h1 className="text-lg font-semibold mb-4">Optional info:</h1>
        {renderInput(
          'Name',
          'name',
          'text',
          validatorAd.valConfigExtra.name,
          edit,
          handleChange('name', 'valConfigExtra'),
          MAX_NAME_LENGTH,
        )}
        {renderInput(
          'Link',
          'about',
          'text',
          validatorAd.valConfigExtra.link,
          edit,
          handleChange('link', 'valConfigExtra'),
          MAX_LINK_LENGTH,
        )}
      </div>
    </div>
  )
}

interface OperatingInfoBasicProps {
  edit: boolean
  validatorAd: ValidatorAd
  setValidatorAd: React.Dispatch<React.SetStateAction<ValidatorAd | undefined>>
}
const OperatingInfoBasic: React.FC<OperatingInfoBasicProps> = ({ edit, validatorAd, setValidatorAd }) => {
  const handleChange = (key: keyof ValidatorAd) => (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.type === 'number' ? Number(e.target.value) : e.target.value
    setValidatorAd({ ...validatorAd, [key]: value })
  }

  return (
    <div className="">
      <div>
        {renderInput('Manager account', 'manager-acc', 'text', validatorAd.manager, edit, handleChange('manager'))}
        <div className="flex">
          {renderInput(
            'Max number of accounts',
            'max-del-cnt',
            'number',
            validatorAd.maxDelCnt.toString(),
            edit,
            handleChange('maxDelCnt'),
          )}
        </div>
      </div>
      <div className="flex">
        {renderInput('Current earnings [uALGO]', 'current-earnings', '', validatorAd.earnings.toString(), false, () => {
          return null
        })}
      </div>
      <div className="">
        <label htmlFor="accepting-new-delegators" className="text-sm font-medium text-gray-700 mr-2">
          Accepting new delegators:
        </label>
        <input
          type="checkbox"
          id="accepting-new-delegators"
          checked={validatorAd.live}
          onChange={(e) => {
            setValidatorAd({ ...validatorAd, live: e.target.checked })
          }}
          className="rounded border-gray-300 shadow-sm focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
        />
      </div>
    </div>
  )
}

interface RightPanelProps {
  validator: boolean | undefined
  new_contract: boolean | undefined
  validatorAd: ValidatorAd
  setValidatorAd: React.Dispatch<React.SetStateAction<ValidatorAd | undefined>>
}
const RightPanel: React.FC<RightPanelProps> = ({ validatorAd, setValidatorAd }) => {
  const navigate = useNavigate()
  const { selectedValAppID } = useParams()
  const { noticeboardApp, setNoticeboardApp, algorandClient, userProfile, setUserProfile } = useGlobalState()

  const [openSignValidatorAdModal, setOpenSignValidatorAdModal] = useState<boolean>(false)
  const [openDeleteValidatorAdModal, setOpenDeleteValidatorAdModal] = useState<boolean>(false)
  const [openWithdrawEarningsModal, setOpenWithdrawEarningsModal] = useState<boolean>(false)
  const [openSignDelegatorContract, setOpenSignDelegatorContract] = useState<boolean>(false)
  const [valAdFromNoticeboard, setValAdFromNoticeboard] = useState<ValidatorAd | undefined>(undefined)
  const [delegatorContractInfo, setDelegatorContractInfo] = useState<DelegatorContractInfo>(UNDEFINED_DELEGATOR_CONTRACT_INFO)
  const [rightPanelOption, setRightPanelOption] = useState<string>('none')
  const [valFull, setValFull] = useState<boolean>(false)

  const { signer, activeAddress } = useWallet()

  const toggleModal = (setModalState: React.Dispatch<React.SetStateAction<boolean>>) => () => {
    setModalState((prev) => !prev)
  }

  const renderButton = (text: string, onClick: () => void, disabled: boolean = false, additionalClasses: string = '') => (
    <button className={`btn ${disabled ? 'btn-disabled' : ''} ${additionalClasses}`} onClick={onClick} disabled={disabled}>
      {text}
    </button>
  )

  const renderSectionHeader = (text: React.ReactNode) => <div className="text-lg font-semibold mb-4">{text}</div>

  useEffect(() => {
    setValAdFromNoticeboard(noticeboardApp.validators.find((validator) => validator.appId === BigInt(selectedValAppID!)))
  }, [noticeboardApp, selectedValAppID])

  useEffect(() => {
    setValFull(validatorAd.delCnt >= validatorAd.maxDelCnt)
  }, [validatorAd])

  const resetValidatorAdFields = () => {
    // Get the selected validator ad for displaying
    setValidatorAd(noticeboardApp.validators.find((validator) => validator.appId === BigInt(selectedValAppID!)))
  }

  const gotToValidators = () => {
    navigate(`/validators/`)
  }

  useEffect(() => {
    const getDelegatorInfo = async () => {
      if (rightPanelOption === 'new-delegator') {
        let currentRound: bigint = 0n
        try {
          const algodStatus = await algorandClient.client.algod.status().do()
          currentRound = BigInt(algodStatus['last-round'] + START_ROUND_IN_FUTURE)
        } catch (e) {
          console.error('Failed to get current round number: %s', e)
        }
        const delegatorContractInfoSelected: DelegatorContractInfo = {
          ...UNDEFINED_DELEGATOR_CONTRACT_INFO,
          roundStart: currentRound,
          roundEnd: currentRound + BigInt(DEFAULT_DELEGATOR_CONTRACT_DURATION),
          valConfigMan: validatorAd.valConfigMan,
          valConfigExtra: validatorAd.valConfigExtra,
          noticeboardAppId: validatorAd.noticeboardAppId,
          valAppId: validatorAd.appId,
          delAcc: activeAddress,
        }
        setDelegatorContractInfo(delegatorContractInfoSelected)
      }
    }
    getDelegatorInfo()
  }, [validatorAd, algorandClient.client.algod, noticeboardApp.appId, activeAddress, rightPanelOption])

  useEffect(() => {
    if (activeAddress && userProfile.new_user === undefined) {
      configUserProfileFromAddress({
        address: activeAddress,
        noticeboardApp: noticeboardApp,
        algodClient: algorandClient.client.algod,
        userProfile: userProfile,
        setUserProfile: setUserProfile,
      })
    }

    if (
      (userProfile.validator && userProfile.new_user) ||
      (userProfile.new_user && userProfile.validator === undefined && BigInt(selectedValAppID!) === 0n)
    ) {
      // Create new validator
      setRightPanelOption('new-validator')
    } else if (userProfile.validator && !userProfile.new_user) {
      // Modify existing validator
      setRightPanelOption('modify-existing-validator')
    } else if (!userProfile.validator && userProfile.new_user) {
      // Create new delegator
      setRightPanelOption('new-delegator')
    } else if (!userProfile.validator && !userProfile.new_user) {
      // Delegator
      setRightPanelOption('none')
    }

    // For testing
    // setRightPanelOption(2)
  }, [userProfile, activeAddress])

  switch (rightPanelOption) {
    case 'new-validator': {
      return (
        <div className="p-6 bg-white shadow-md rounded-md">
          <div className="border p-4 mb-4 rounded-md">
            {renderSectionHeader('Fill in your operating information')}
            <OperatingInfoBasic edit={true} validatorAd={validatorAd} setValidatorAd={setValidatorAd} />
          </div>
          {renderButton('Create ad', toggleModal(setOpenSignValidatorAdModal), false, 'mt-4 btn')}
          <SignValidatorAd
            openModal={openSignValidatorAdModal}
            setModalState={setOpenSignValidatorAdModal}
            createNew={true}
            validatorAd={validatorAd}
          />
        </div>
      )
    }
    case 'modify-existing-validator': {
      return (
        <div className="p-6 bg-white shadow-md rounded-md">
          <div className="border p-4 mb-4 rounded-md">
            {renderSectionHeader('Operating info:')}
            <OperatingInfoBasic edit={true} validatorAd={validatorAd} setValidatorAd={setValidatorAd} />
          </div>
          <div className="mt-4 space-x-4">
            {renderButton('Reset fields', resetValidatorAdFields, _.isEqual(valAdFromNoticeboard, validatorAd))}
            {renderButton('Update ad', toggleModal(setOpenSignValidatorAdModal), _.isEqual(valAdFromNoticeboard, validatorAd), 'btn')}
            <SignValidatorAd
              openModal={openSignValidatorAdModal}
              setModalState={setOpenSignValidatorAdModal}
              createNew={false}
              validatorAd={validatorAd}
            />
            {renderButton('Delete ad', toggleModal(setOpenDeleteValidatorAdModal), validatorAd.delCnt > 0, 'btn')}
            <DeleteValidatorAd
              openModal={openDeleteValidatorAdModal}
              setModalState={setOpenDeleteValidatorAdModal}
              validatorAd={validatorAd}
            />
            {renderButton('Withdraw earnings', toggleModal(setOpenWithdrawEarningsModal), validatorAd.earnings <= 0n, 'btn')}
            <WithdrawBalance
              openModal={openWithdrawEarningsModal}
              setModalState={setOpenWithdrawEarningsModal}
              validatorAd={validatorAd}
              setValidatorAd={setValidatorAd}
            />
          </div>

          <div className="mt-6">
            <ValidatorDelegators delegators={validatorAd.delegators} maxDelCnt={validatorAd.maxDelCnt} />
          </div>
        </div>
      )
    }
    case 'new-delegator': {
      return (
        <div className="p-6 bg-white shadow-md rounded-md">
          <ValidatorDelegators delegators={validatorAd.delegators} maxDelCnt={validatorAd.maxDelCnt} />
          <div className="mt-4">
            {renderSectionHeader(
              <span>
                Do you trust <em>{validatorAd.valConfigExtra.name}</em> to protect the network for you?
              </span>,
            )}
            <div className="space-x-4">
              {renderButton(
                valFull ? 'Validator is full' : 'Yes',
                toggleModal(setOpenSignDelegatorContract),
                valFull,
                valFull ? 'btn-disabled' : 'btn',
              )}
              {renderButton(valFull ? 'Back' : 'No', gotToValidators, false, 'btn')}
              <SignDelegatorContract
                openModal={openSignDelegatorContract}
                setModalState={setOpenSignDelegatorContract}
                delegatorContractInfo={delegatorContractInfo}
                setDelegatorContractInfo={setDelegatorContractInfo}
              />
            </div>
          </div>
        </div>
      )
    }
    default: {
      return (
        <div className="p-6 bg-white shadow-md rounded-md">
          <ValidatorDelegators delegators={validatorAd.delegators} maxDelCnt={validatorAd.maxDelCnt} />
        </div>
      )
    }
  }
}
//           <ValidatorDelegators delegators={noticeboardApp.validators.filter((validator)=>{validator.appId })} />

interface ValidatorProps {}

const Validator: React.FC<ValidatorProps> = () => {
  const { selectedValAppID } = useParams()
  const { noticeboardApp, setNoticeboardApp, algorandClient, userProfile } = useGlobalState()
  const [validatorAd, setValidatorAd] = useState<ValidatorAd | undefined>(undefined)
  const [loading, setLoading] = useState<boolean>(true)

  useEffect(() => {
    const fetchValidator = async () => {
      setLoading(true)

      try {
        // Check that selectedValAppID is unsigned int
        if (
          !selectedValAppID ||
          isNaN(Number(selectedValAppID)) ||
          Number(selectedValAppID) < 0 ||
          !Number.isInteger(Number(selectedValAppID))
        ) {
          setValidatorAd(undefined)
          return
        }

        if (BigInt(selectedValAppID) == 0n) {
          setValidatorAd({
            ...DEFAULT_VALIDATOR_AD,
            earnFactor: noticeboardApp.noticeboardInfo.valEarnFactor,
            deposit: noticeboardApp.noticeboardInfo.depositValMin + 1n, //+1 because it has to be larger and not equal
            live: true,
          })
          return
        }

        // Get list of validators ad from the noticeboard
        const fetchedValidatorList = await getValidatorIDs(algorandClient.client.algod, BigInt(noticeboardApp.appId))

        // Check if selected validator ad exists in the noticeboard
        if (!fetchedValidatorList.includes(BigInt(selectedValAppID))) {
          setValidatorAd(undefined)
          return
        }

        // Fetch the selected valdiator
        try {
          const fetchedValidator = await getValidatorAd(algorandClient.client.algod, BigInt(selectedValAppID))

          // Check if selected validator ad has been fetched already from the noticeboard
          if (noticeboardApp.validatorList.includes(BigInt(selectedValAppID))) {
            // Check if the fetched validator ad is different than stored
            const currentValidator = noticeboardApp.validators.find((validator) => validator.appId === BigInt(selectedValAppID!))
            if (!_.isEqual(fetchedValidator, currentValidator)) {
              // Update the fetched validator ad in the noticeboard
              setNoticeboardApp({
                ...noticeboardApp,
                validatorList: [
                  ...noticeboardApp.validatorList.filter((valAppId) => valAppId !== BigInt(selectedValAppID)),
                  BigInt(selectedValAppID),
                ],
                validators: [
                  ...noticeboardApp.validators.filter((validator) => {
                    validator.appId !== BigInt(selectedValAppID)
                  }),
                  fetchedValidator!,
                ],
              })
            }
          } else {
            // Add the newly fetched validator ad to noticeboard
            setNoticeboardApp({
              ...noticeboardApp,
              validatorList: [...noticeboardApp.validatorList, BigInt(selectedValAppID)],
              validators: [...noticeboardApp.validators, fetchedValidator!],
            })
          }
        } catch (error) {
          console.error(`Failed to fetch info for validator ID ${BigInt(selectedValAppID)}:`, error)
          setValidatorAd(undefined)
          return
        }

        // Get the selected validator ad for displaying
        setValidatorAd(noticeboardApp.validators.find((validator) => validator.appId === BigInt(selectedValAppID)))

        // Store selected validator ad info
      } catch (error) {
        console.error('Failed to fetch validator: %s', selectedValAppID, error)
        setValidatorAd(undefined)
      } finally {
        setLoading(false)
      }
    }

    fetchValidator()
  }, [selectedValAppID, algorandClient, noticeboardApp])

  if (loading) {
    return (
      <div className="main-website">
        <WebsiteHeader />
        <div className="main-body">
          <h1 className="text-xl font-bold">Loading validator with ID '{selectedValAppID}'</h1>
          <button className="loading loading-spinner" />
        </div>
      </div>
    )
  } else {
    if (!validatorAd) {
      return (
        <div className="main-website">
          <WebsiteHeader />
          <div className="main-body">
            <h1 className="text-xl font-bold text-red-600">Validator with ID '{selectedValAppID}' does not exist on the platform.</h1>
          </div>
        </div>
      )
    } else {
      return (
        <div className="main-website">
          <WebsiteHeader />
          <div className="">
            <div className="p-4">
              <h1 className="text-3xl font-bold text-center">Validator ID: {selectedValAppID}</h1>
            </div>
            <div className="flex flex-1">
              <div className="w-1/2 p-4">
                <ValidatorInfo
                  edit={
                    userProfile.validator === true ||
                    (userProfile.new_user === true && userProfile.validator === undefined && BigInt(selectedValAppID!) === 0n)
                  }
                  validatorAd={validatorAd}
                  setValidatorAd={setValidatorAd}
                />
              </div>
              <div className="w-1/2 p-4">
                <RightPanel
                  validator={userProfile.validator}
                  new_contract={userProfile.new_user}
                  validatorAd={validatorAd}
                  setValidatorAd={setValidatorAd}
                />
              </div>
            </div>
          </div>
        </div>
      )
    }
  }
}

export default Validator
