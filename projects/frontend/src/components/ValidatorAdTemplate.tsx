import { ValidatorAd } from '../interfaces/contract-specs'
import { ellipseAddress } from '../utils/ellipseAddress'

interface ValidatorAdTemplateProps {
  validatorAd: ValidatorAd
}

const ValidatorAdTemplate: React.FC<ValidatorAdTemplateProps> = ({ validatorAd }) => {
  const {
    manager,
    maxDelCnt,
    valConfigMan: { feeSetup, feeRound, maxBreach, breachRounds, setupRounds, confirmationRounds, minAmt, maxAmt, deposit },
    earnFactor,
  } = validatorAd

  return (
    <section className="border border-solid border-grayhero-content text-left rounded-lg p-6 max-w-md bg-white mx-auto">
      <h2 className="text-lg font-semibold">The validator hereby:</h2>
      <ol className="list-decimal ml-5">
        <li>Agrees to voluntarily participate on the IgoProtect platform.</li>
        <li>
          Pledges to protect the Algorand network to the best of one's abilities by maintaining one's node and the keys delegated to it by
          delegators.
        </li>
        <li>
          Understands that for servicing of requests, one is using a hot wallet on one's own node. The wallet's address is:{' '}
          {ellipseAddress(manager)}.
        </li>
        <li>Understands that anyone will be able to delegate their stake to one's node at any time.</li>
        <li>
          Agrees to receive from the delegators fees for validator setup (i.e., participation key generation) and operation in ALGO. The
          setup fee charged is {feeSetup.toString()} uALGO. The operational fee is {feeRound.toString()} uALGO/round.
        </li>
        <li>Understands that the fees will be available for claiming after the end of the contract with a delegator.</li>
        <li>Commits to donate {earnFactor!.toString()}% of the fees I generate to the IgoProtect platform for its maintenance.</li>
        <li>
          Requires a new delegator to deposit {deposit.toString()} uALGO that can be seized in case of delegator breaching the agreed
          contract.
        </li>
        <li>
          Defines that breaching of the contract by a delegator means that delegator's wallet balances drops below {minAmt.toString()} uALGO
          or goes above {maxAmt.toString()} at any point during contract validity.
        </li>
        <li>
          Commits to notifying the delegator {maxBreach.toString()} time(s) in case of delegator breaching the contract commitments before
          seizing its deposit, whereby two breaches are considered as separate when being more than {breachRounds.toString()} rounds apart.
        </li>
        <li>
          Understands that after seizing a delegator's deposit due to contract breaches, its participation keys can be deleted at one's sole
          discretion without having to wait for delegator to register offline or keys to expire, even though this endangers the Algorand
          network.
        </li>
        <li>
          Understands that in case one's node was not performing according to the guaranteed uptime, the platform can seize one's deposit in
          part or in full.
        </li>
        <li>
          Commits to having capacity for {maxDelCnt.toString()} delegators at one's node and will be held responsible if adding more
          delegators causes degraded validator performance.
        </li>
        <li>
          Commits to respond to a new delegators' requests by generating and depositing new participation keys within a period of{' '}
          {setupRounds.toString()} rounds.
        </li>
        <li>Agrees that in case one's does not generate the keys in time, one will refund the setup fee.</li>
        <li>
          Reservers the right to single-sidedly cancel a new delegator's request when the latter does not confirm the generated
          participation keys within a period of {confirmationRounds.toString()} rounds.
        </li>
        <li>
          Agrees by signing the contract to IgoProtect's{' '}
          <a href="https://github.com/uhudo/igoprotect/" target="_blank" rel="noopener noreferrer">
            Terms & Conditions
          </a>
        </li>
      </ol>
    </section>
  )
}

export default ValidatorAdTemplate
