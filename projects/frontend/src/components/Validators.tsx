import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ValidatorAd } from '../interfaces/contract-specs'
import { useGlobalState } from '../providers/GlobalStateProvider'
import { getValidatorAd, getValidatorIDs } from '../utils/getFromBlockchain'
import WebsiteHeader from './WebsiteHeader'

const tableClasses = 'min-w-full divide-y divide-gray-200 border-collapse border border-gray-300'
const tableHeaderClasses = 'px-6 py-3 text-center text-xs font-medium text-gray-500 tracking-wider border border-gray-300'
const tableDataClasses = 'px-6 py-4 whitespace-nowrap text-center border border-gray-300'

const TableHeader: React.FC = () => (
  <thead className="bg-gray-50 sticky top-0 z-2">
    <tr>
      <th className={tableHeaderClasses} rowSpan={2}>
        ID
      </th>
      <th className={tableHeaderClasses} rowSpan={2}>
        Name
      </th>
      <th className={tableHeaderClasses} colSpan={2}>
        Stake [uALGO]
      </th>
      <th className={tableHeaderClasses} colSpan={2}>
        Fee [uALGO]
      </th>
      <th className={tableHeaderClasses} rowSpan={2}>
        Deposit [uALGO]
      </th>
    </tr>
    <tr>
      <th className={tableHeaderClasses}>Min</th>
      <th className={tableHeaderClasses}>Max</th>
      <th className={tableHeaderClasses}>Setup</th>
      <th className={tableHeaderClasses}>Operational [per round]</th>
    </tr>
  </thead>
)

const TableRow: React.FC<{ validator: ValidatorAd; goToValidator: (appId: number) => void }> = ({ validator, goToValidator }) => (
  <tr key={Number(validator.appId)} onClick={() => goToValidator(Number(validator.appId))} className="hover:bg-gray-100 cursor-pointer">
    <td className={tableDataClasses}>{Number(validator.appId)}</td>
    <td className={tableDataClasses}>{validator.valConfigExtra.name}</td>
    <td className={tableDataClasses}>{Number(validator.valConfigMan.minAmt)}</td>
    <td className={tableDataClasses}>{Number(validator.valConfigMan.maxAmt)}</td>
    <td className={tableDataClasses}>{Number(validator.valConfigMan.feeSetup)}</td>
    <td className={tableDataClasses}>{Number(validator.valConfigMan.feeRound)}</td>
    <td className={tableDataClasses}>{Number(validator.valConfigMan.deposit)}</td>
  </tr>
)

interface ValidatorsProps {}

const Validators: React.FC<ValidatorsProps> = () => {
  const navigate = useNavigate()
  const { noticeboardApp, setNoticeboardApp, algorandClient } = useGlobalState()
  const [loading, setLoading] = useState<boolean>(true)

  useEffect(() => {
    const fetchValidators = async () => {
      setLoading(true)

      try {
        const fetchedValidatorList = await getValidatorIDs(algorandClient.client.algod, BigInt(noticeboardApp.appId))

        const fetchedValidators = await Promise.all(
          fetchedValidatorList.map(async (validatorId) => {
            try {
              const valInfo = await getValidatorAd(algorandClient.client.algod, validatorId)
              return valInfo
            } catch (error) {
              console.error(`Failed to fetch info for validator ID ${validatorId}:`, error)
              return null
            }
          }),
        )

        setNoticeboardApp({
          ...noticeboardApp,
          validators: fetchedValidators.filter((val) => val !== null) as ValidatorAd[],
          validatorList: fetchedValidatorList,
        })
      } catch (error) {
        console.error('Failed to fetch validators:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchValidators()
  }, [noticeboardApp.appId, algorandClient.client.algod])

  const goToValidator = (appId: number) => {
    navigate(`/validators/${appId}`)
  }

  const goToLearn = () => {
    navigate(`/learn`)
  }

  if (loading) {
    return (
      <div className="main-website">
        <WebsiteHeader />
        <div className="main-body">
          <h1 className="text-xl font-bold">Loading validators</h1>
          <button className="loading loading-spinner" />
        </div>
      </div>
    )
  } else {
    return (
      <div className="main-website">
        <WebsiteHeader />
        <div className="flex justify-center bg-gray-50 pt-8 ">
          <div className="">
            <h1 className="text-4xl font-bold mb-6 text-center pb-4">List of Validators</h1>
            <div className="overflow-x-auto max-w-full">
              <div className="max-h-96 overflow-y-auto">
                <table className={tableClasses}>
                  <colgroup>
                    <col />
                    <col />
                    <col span={2} />
                    <col />
                  </colgroup>
                  <TableHeader />
                  <tbody className="bg-white divide-y divide-gray-200">
                    {noticeboardApp.validators.map((validator) => {
                      if (validator.live) {
                        return <TableRow key={Number(validator.appId)} validator={validator} goToValidator={goToValidator} />
                      } else {
                        return
                      }
                    })}
                  </tbody>
                </table>
              </div>
              <div className="flex justify-center mt-4">
                <button className="btn btn-primary" onClick={goToLearn}>
                  Become a validator
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }
}

export default Validators
