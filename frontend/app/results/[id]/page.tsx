import { redirect } from "next/navigation";

export default async function ResultPage({
  params
}: {
  params: Promise<{ id: string }>;
}) {
  redirect("/login");
}
