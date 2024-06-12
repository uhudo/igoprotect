import { useNavigate } from 'react-router-dom'
import { DelegatorContractInfo } from '../interfaces/contract-specs'
import { ellipseAddress } from '../utils/ellipseAddress'

const tableClasses = 'min-w-full divide-y divide-gray-200 border-collapse border border-gray-300'
const tableHeaderClasses = 'px-6 py-3 text-center text-xs font-medium text-gray-500 tracking-wider border border-gray-300'
const tableDataClasses = 'px-6 py-4 whitespace-nowrap text-center border border-gray-300'

const TableHeader: React.FC = () => (
  <thead className="bg-gray-50">
    <tr>
      <th className={tableHeaderClasses} rowSpan={2}>
        ID
      </th>
      <th className={tableHeaderClasses} rowSpan={2}>
        Account
      </th>
      <th className={tableHeaderClasses} colSpan={2}>
        Date
      </th>
      <th className={tableHeaderClasses} rowSpan={2}>
        Breaches
      </th>
    </tr>
    <tr>
      <th className={tableHeaderClasses}>Start round</th>
      <th className={tableHeaderClasses}>End round</th>
    </tr>
  </thead>
)

const TableRow: React.FC<{ delegator: DelegatorContractInfo; goToDelegator: (appId: number) => void }> = ({ delegator, goToDelegator }) => (
  <tr key={Number(delegator.appId)} onClick={() => goToDelegator(Number(delegator.appId))} className="hover:bg-gray-100 cursor-pointer">
    <td className={tableDataClasses}>{Number(delegator.appId)}</td>
    <td className={tableDataClasses}>{ellipseAddress(delegator.delAcc)}</td>
    <td className={tableDataClasses}>{Number(delegator.roundStart)}</td>
    <td className={tableDataClasses}>{Number(delegator.roundEnd)}</td>
    <td className={tableDataClasses}>
      {Number(delegator.numBreach)}/{Number(delegator.valConfigMan!.maxBreach)}
    </td>
  </tr>
)

interface ValidatorDelegatorsProps {
  delegators: (DelegatorContractInfo | undefined)[]
  maxDelCnt: bigint
}

const ValidatorDelegators: React.FC<ValidatorDelegatorsProps> = ({ delegators, maxDelCnt }) => {
  const navigate = useNavigate()

  const goToDelegator = (id: number) => {
    navigate(`/contract/${id}`)
  }

  return (
    <div className="container mx-auto p-4 border mb-4 rounded-md">
      <h3 className="text-2xl font-semibold mb-2 text-center">Delegators</h3>
      <h3 className="text-xl font-semibold mb-2 text-left">
        Occupied: {delegators.length} of max {maxDelCnt.toString()}
      </h3>
      <div className="overflow-x-auto">
        <table className={tableClasses}>
          <colgroup>
            <col />
            <col />
            <col span={2} />
            <col />
          </colgroup>
          <TableHeader />
          <tbody className="bg-white divide-y divide-gray-200">
            {delegators.map((delegator) => {
              if (delegator) return <TableRow key={Number(delegator.appId)} delegator={delegator} goToDelegator={goToDelegator} />
              else {
                return
              }
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default ValidatorDelegators
