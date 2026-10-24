import React from 'react';
import './style.css';
export const metadata = {title:'AgentOps Command Center', description:'CrewAI incident investigation'};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}</body></html>}
