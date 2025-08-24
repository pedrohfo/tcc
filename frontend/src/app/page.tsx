import { redirect } from "next/navigation";
import { cookies } from "next/headers";

export default async function Home() {
  const cookieStore = await cookies();
  const token = cookieStore.get("access"); // use o mesmo nome que você está salvando no login

  if (!token) {
    redirect("/login");
  } else {
    redirect("/fases");
  }
}
