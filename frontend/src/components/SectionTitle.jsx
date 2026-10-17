import React from 'react';
function SectionTitle({eyebrow,title,desc,action}){return <div className="section-title"><div>{eyebrow&&<span className="eyebrow">{eyebrow}</span>}<h2>{title}</h2>{desc&&<p className="muted">{desc}</p>}</div>{action}</div>}
export default SectionTitle;
