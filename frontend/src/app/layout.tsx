import type { Metadata } from "next";
import "./globals.css";
import { Header } from "@/components/layout/header";
import { Sidebar } from "@/components/layout/sidebar";
import { AuthProvider } from "@/context/AuthContext";
import { AuthGuard } from "@/components/auth/AuthGuard";

export const metadata: Metadata = {
  title: "CareerPilot — AI-Powered Career Intelligence Platform",
  description:
    "Navigate your career. Engineer your future. Zero-cost local intelligence with factual integrity resume optimization and hybrid candidate-job matching.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-soft-bg text-soft-text antialiased flex flex-col">
        <AuthProvider>
          <Header />
          <div className="flex-1 flex max-w-[1600px] w-full mx-auto">
            <Sidebar />
            <main className="flex-1 p-4 lg:p-6 overflow-y-auto">
              <AuthGuard>{children}</AuthGuard>
            </main>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
