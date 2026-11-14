import { ChevronRight } from "lucide-react";
import { Link } from "@/i18n/navigation";

export interface Crumb {
  href: string;
  label: string;
}

export function Breadcrumbs({ items }: { items: Crumb[] }) {
  return (
    <nav aria-label="Breadcrumb" className="mb-6 text-sm text-rf-ink-muted">
      <ol className="flex flex-wrap items-center gap-1">
        {items.map((item, i) => {
          const last = i === items.length - 1;
          return (
            <li key={item.href} className="flex items-center gap-1">
              {last ? (
                <span aria-current="page" className="text-rf-ink">
                  {item.label}
                </span>
              ) : (
                <Link href={item.href} className="hover:text-rf-primary">
                  {item.label}
                </Link>
              )}
              {!last && (
                <ChevronRight className="h-4 w-4 shrink-0" aria-hidden />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
