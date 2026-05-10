import { NavLink } from 'react-router-dom';

const sections = [
  { label: 'Overview', to: '/' },
  { label: 'Documents', to: '/upload' },
  { label: 'Assistant', to: '/chat' },
];

export default function Sidebar() {
  return (
    <aside className="hidden rounded-lg border border-slate-200 bg-white p-3 md:block">
      <div className="px-2 pb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
        Workspace
      </div>
      <div className="space-y-1">
        {sections.map((section) => (
          <NavLink
            key={section.to}
            to={section.to}
            className={({ isActive }) =>
              [
                'block rounded-md px-3 py-2 text-sm font-medium',
                isActive ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100',
              ].join(' ')
            }
          >
            {section.label}
          </NavLink>
        ))}
      </div>
    </aside>
  );
}
