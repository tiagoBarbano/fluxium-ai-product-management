import { InitiativeProposalHistory } from "@/features/proposals/components/initiative-proposal-history";

export default async function InitiativeProposalsPage({ params }: { params: Promise<{ initiativeId: string }> }) {
  const { initiativeId } = await params;
  return <InitiativeProposalHistory initiativeId={initiativeId} />;
}
