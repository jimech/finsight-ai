import { AuthHeader } from "@/components/auth-header";

export default function DashboardLayout({
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
