import { ReadinessReview } from "@/features/readiness/components/readiness-review";

export default async function ReadinessPage({ params }: { params: Promise<{ initiativeId: string }> }) {
  const { initiativeId } = await params;
  return <ReadinessReview initiativeId={initiativeId} />;
}
