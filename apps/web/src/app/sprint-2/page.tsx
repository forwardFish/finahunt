import { redirect } from "next/navigation";

type PageProps = { searchParams?: Promise<Record<string, string | string[] | undefined>> };

export default async function Sprint2CompatibilityPage({ searchParams }: PageProps) {
  const params = searchParams ? await searchParams : {};
  const date = Array.isArray(params.date) ? params.date[0] : params.date;
  redirect(date ? `/workbench?date=${encodeURIComponent(date)}` : "/workbench");
}
