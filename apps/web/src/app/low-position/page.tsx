import { redirect } from "next/navigation";

type PageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

function takeFirst(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

export default async function LowPositionCompatibilityPage({ searchParams }: PageProps) {
  const params = searchParams ? await searchParams : {};
  const date = takeFirst(params.date);
  const query = new URLSearchParams();
  if (date) {
    query.set("date", date);
  }
  redirect(query.toString() ? `/research?${query.toString()}` : "/research");
}
