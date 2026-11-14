import { Header } from "@/components/storefront/Header";
import { Footer } from "@/components/storefront/Footer";
import { CookieBanner } from "@/components/storefront/CookieBanner";

export default function SiteLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-full flex-col bg-rf-bg text-rf-ink">
      <Header />
      <main className="flex-1">{children}</main>
      <Footer />
      <CookieBanner />
    </div>
  );
}
