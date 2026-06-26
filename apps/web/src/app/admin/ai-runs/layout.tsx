import { AuthHeader } from "@/components/auth-header";

export default function AdminAiRunsLayout({
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
