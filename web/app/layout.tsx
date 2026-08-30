import type { Metadata } from "next";
import "./globals.css";
import { FilterProvider } from "@/lib/FilterContext";
import Sidebar from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "QA Command",
  description: "Test Execution & Defect Metrics — ZAIMAH TECHNOLOGIES",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <FilterProvider>
          <div className="flex min-h-screen">
            <Sidebar />
            <div className="flex-1 min-w-0">{children}</div>
          </div>
        </FilterProvider>
      </body>
    </html>
  );
}
