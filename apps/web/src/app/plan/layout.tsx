import { AuthHeader } from "@/components/auth-header";

export default function PlanLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <AuthHeader />
      {children}
    </>
  );
}
