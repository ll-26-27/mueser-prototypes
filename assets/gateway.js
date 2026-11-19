/* Diagrams are rendered from local Mermaid; the pages and text work without JS. */
(async () => {
  const diagrams = [...document.querySelectorAll('.mermaid')];
  if (diagrams.length && window.mermaid) {
    mermaid.initialize({startOnLoad:false,securityLevel:'strict',theme:'base',fontFamily:'system-ui, sans-serif',themeVariables:{primaryColor:'#edf1ec',primaryTextColor:'#292e2b',primaryBorderColor:'#9aa99c',lineColor:'#728077',secondaryColor:'#f2ece2',tertiaryColor:'#fffefa',clusterBkg:'#f8f7f3',clusterBorder:'#dcded5',fontSize:'15px'},flowchart:{htmlLabels:false,curve:'basis',padding:18}});
    for (const node of diagrams) {
      try { await mermaid.run({nodes:[node]}); }
      catch (_) { node.textContent = 'Diagram unavailable. The same workflow is described below.'; node.className='diagram-error'; }
    }
  }
  let active=null, opener=null;
  function close(){if(!active)return;active.classList.remove('expanded');active.removeAttribute('role');active.removeAttribute('aria-modal');document.body.style.overflow='';active=null;opener?.focus();}
  document.querySelectorAll('[data-expand]').forEach(button=>{button.addEventListener('click',()=>{if(active)close();active=document.getElementById(button.dataset.expand);opener=button;active.classList.add('expanded');active.setAttribute('role','dialog');active.setAttribute('aria-modal','true');document.body.style.overflow='hidden';active.querySelector('.close-diagram').focus();});});
  document.querySelectorAll('.close-diagram').forEach(button=>button.addEventListener('click',close));
  document.addEventListener('keydown',event=>{if(!active)return;if(event.key==='Escape')close();if(event.key==='Tab'){event.preventDefault();active.querySelector('.close-diagram').focus();}});
})();
