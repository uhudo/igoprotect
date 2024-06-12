import { DelegatorContractInfo } from '../interfaces/contract-specs'
import { ellipseAddress } from '../utils/ellipseAddress'

interface DelegatorContractTemplateProps {
  delegatorContractInfo: DelegatorContractInfo
}

const DelegatorContractTemplate: React.FC<DelegatorContractTemplateProps> = ({ delegatorContractInfo }) => {
  if (!delegatorContractInfo || !delegatorContractInfo.valConfigMan || !delegatorContractInfo.delAcc) {
    return
  }

  const { valAppId, delAcc, roundStart, roundEnd } = delegatorContractInfo
  const { minAmt, maxAmt, deposit, maxBreach, breachRounds, feeRound, feeSetup, setupRounds, confirmationRounds } =
    delegatorContractInfo.valConfigMan!

  const operationalFee = feeRound * (roundEnd - roundStart)

  const renderListItem = (content: React.ReactNode, key: number) => <li key={key}>{content}</li>

  const listItems = [
    `Authorizes validator denoted with ID ${valAppId.toString()} to protect the Algorand network on one's behalf.`,
    <>
      Agrees to have at least {minAmt.toString()} uALGO at address {ellipseAddress(delAcc.toString())} but not more than {maxAmt.toString()}{' '}
      uALGO at any point in time between start round {roundStart.toString()} and end round {roundEnd.toString()}.
    </>,
    `Agrees to deposit ${deposit.toString()} uALGO as a commitment to respecting these terms.`,
    <>
      Agrees that in case of breaching these contract obligations more than {maxBreach.toString()} times, whereby two breaches are
      considered as separate when being more than {breachRounds.toString()} rounds apart, one agrees to forfeit one's deposit.
    </>,
    <>
      Agrees to pay for this service a setup fee of {feeSetup.toString()} uALGO and an operational fee of {operationalFee.toString()} uALGO
      (=
      {feeRound.toString()}uALGO/round*({roundEnd.toString()}-{roundStart.toString()}) rounds).
    </>,
    'Agrees to pay the service fees in advance.',
    'Understands that one can withdraw from the contract at any point due to any reason by connecting to this platform and issuing a withdrawal.',
    'Agrees to issue an account deregistration transaction only through this platform and only in combination with the contract withdrawal.',
    'Understands that in case of a withdrawal, the unused portion of the operational fee will be proportionally refunded and the deposit returned in full.',
    `Understands that the validator commits to finish the setup for starting a new contract in at most ${setupRounds.toString()} rounds after one concludes the delegation contract.`,
    `Understands that one needs to confirm the setup within ${confirmationRounds.toString()} rounds after the validator finished the setup.`,
    'Agrees that if the setup is not confirmed in time, the operational fee will be seized. The deposit will be returned in full.',
    <>
      Agrees by signing the contract to IgoProtect's{' '}
      <a href="https://github.com/uhudo/igoprotect/" target="_blank" rel="noopener noreferrer">
        Terms & Conditions
      </a>
    </>,
  ]

  return (
    <section className="border border-solid border-grayhero-content text-left rounded-lg p-6 max-w-md bg-white mx-auto">
      <h2 className="text-lg font-semibold">The delegator hereby </h2>
      <ol className="list-decimal ml-5">{listItems.map((item, index) => renderListItem(item, index))}</ol>
    </section>
  )
}

export default DelegatorContractTemplate
